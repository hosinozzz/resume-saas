# ──────────────────────────────────────────
# IAMロール（main / worker 共通）
# ──────────────────────────────────────────
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB: IPレート制限 + ジョブステータス管理
resource "aws_iam_role_policy" "dynamodb" {
  name = "dynamodb-rate-limit"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
      ]
      Resource = var.dynamodb_table_arn
    }]
  })
}

# S3: 生成ファイルバケットの読み書き
resource "aws_iam_role_policy" "s3_generated" {
  name = "s3-generated-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
      ]
      Resource = "${var.generated_bucket_arn}/*"
    }]
  })
}

# SQS: main LambdaはSendMessage、worker LambdaはReceive/Delete
# 共通ロールなので両方許可（最小権限からは外れるがMVPとして許容）
resource "aws_iam_role_policy" "sqs" {
  name = "sqs-worker-queue"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
      ]
      Resource = var.sqs_queue_arn
    }]
  })
}

# SES: お問い合わせメール送信
resource "aws_iam_role_policy" "ses_send" {
  name = "ses-send-email"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ses:SendEmail", "ses:SendRawEmail"]
      Resource = "*"
    }]
  })
}

# Secrets Manager: Claude APIキーとStripeシークレット取得
resource "aws_iam_role_policy" "secrets_manager" {
  name = "secrets-manager-read"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = ["secretsmanager:GetSecretValue"]
      Resource  = "arn:aws:secretsmanager:*:*:secret:${var.project_name}/*"
    }]
  })
}

# ──────────────────────────────────────────
# CloudWatch Logs
# ──────────────────────────────────────────
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${var.project_name}-worker-${var.environment}"
  retention_in_days = 14
}

# ──────────────────────────────────────────
# デプロイパッケージ（main / worker 共通zip）
# ──────────────────────────────────────────
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../backend/lambda"
  output_path = "${path.module}/lambda_deploy.zip"
}

# ──────────────────────────────────────────
# main Lambda: ファイル受付 + SQS送信 + ステータス確認
# ──────────────────────────────────────────
resource "aws_lambda_function" "main" {
  function_name    = "${var.project_name}-${var.environment}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  # SQS送信 + DynamoDB書き込みのみなので30秒で十分
  timeout     = 30
  memory_size = 512

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      GENERATED_BUCKET_NAME = var.generated_bucket_name
      MAX_REQUESTS_PER_HOUR = tostring(var.max_requests_per_hour)
      SQS_QUEUE_URL         = var.sqs_queue_url
      CLAUDE_API_TIMEOUT    = "25"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.basic_execution,
    aws_cloudwatch_log_group.lambda,
  ]
}

# /upload 専用 Function URL（API GatewayのCORS問題を回避するため維持）
resource "aws_lambda_function_url" "upload" {
  function_name      = aws_lambda_function.main.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET"]
    allow_headers = ["content-type"]
    max_age       = 300
  }
}

resource "aws_lambda_permission" "function_url_public" {
  statement_id           = "AllowPublicFunctionURL"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.main.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# ──────────────────────────────────────────
# worker Lambda: SQSトリガーでClaude API呼び出し（最大15分）
# ──────────────────────────────────────────
resource "aws_lambda_function" "worker" {
  function_name    = "${var.project_name}-worker-${var.environment}"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "worker.lambda_handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  # Claude APIの応答待ち含め最大15分
  timeout     = 900
  memory_size = 1024

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      GENERATED_BUCKET_NAME = var.generated_bucket_name
      # CLAUDE_API_TIMEOUTは未設定 → claude_client.pyのデフォルト600秒が適用される
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.basic_execution,
    aws_cloudwatch_log_group.worker,
  ]
}

# SQS → worker Lambda のイベントソースマッピング
# batch_size=1: 1ジョブ = 1Lambda呼び出し（15分かかる処理を直列に）
resource "aws_lambda_event_source_mapping" "sqs_to_worker" {
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.worker.arn
  batch_size       = 1
  enabled          = true

  # ビジビリティタイムアウト（900秒）内に処理が完了しない場合はSQSが再試行
  function_response_types = ["ReportBatchItemFailures"]
}
