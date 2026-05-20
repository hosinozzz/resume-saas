terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # ステートはローカル保存（運用開始後はS3バックエンドへ移行を推奨）
  # backend "s3" {
  #   bucket = "resume-saas-tfstate"
  #   key    = "prod/terraform.tfstate"
  #   region = "ap-northeast-1"
  # }
}

# メインリージョン（東京）
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# CloudWatch Billing Alarmはus-east-1でしか取得できない
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ──────────────────────────────────────────
# S3: 静的フロントエンド（CloudFront経由で配信）
# ──────────────────────────────────────────
module "s3_frontend" {
  source = "./modules/s3"

  bucket_name = "${var.project_name}-frontend-${var.environment}"
  purpose     = "frontend"
}

# ──────────────────────────────────────────
# S3: 生成ファイル一時保存（TTL管理 / 署名付きURL発行元）
# ──────────────────────────────────────────
module "s3_generated" {
  source = "./modules/s3"

  bucket_name            = "${var.project_name}-generated-${var.environment}"
  purpose                = "generated"
  expiration_days        = 7  # 生成HTML（{job_id}/preview.html, clean.html）は7日後に削除
  upload_expiration_days = 1  # アップロード原本（uploaded/{job_id}/resume.txt）は1日後に削除
  cors_allowed_origins   = ["https://d20pg6j10067w4.cloudfront.net"]
}

# ──────────────────────────────────────────
# CloudFront: HTTPS配信 + S3フロントエンドのOAC
# ──────────────────────────────────────────
module "cloudfront" {
  source = "./modules/cloudfront"

  frontend_bucket_id                  = module.s3_frontend.bucket_id
  frontend_bucket_regional_domain_name = module.s3_frontend.bucket_regional_domain_name
  project_name                        = var.project_name
  environment                         = var.environment
}

# ──────────────────────────────────────────
# DynamoDB: IPレート制限管理テーブル
# ──────────────────────────────────────────
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

# ──────────────────────────────────────────
# SQS: 非同期ワーカーキュー
# ──────────────────────────────────────────
module "sqs" {
  source = "./modules/sqs"

  project_name = var.project_name
  environment  = var.environment
}

# ──────────────────────────────────────────
# Lambda: ファイル受付(main) + Claude API処理(worker)
# ──────────────────────────────────────────
module "lambda" {
  source = "./modules/lambda"

  project_name          = var.project_name
  environment           = var.environment
  dynamodb_table_name   = module.dynamodb.table_name
  dynamodb_table_arn    = module.dynamodb.table_arn
  generated_bucket_name = module.s3_generated.bucket_id
  generated_bucket_arn  = module.s3_generated.bucket_arn
  max_requests_per_hour = var.max_requests_per_hour
  sqs_queue_url         = module.sqs.queue_url
  sqs_queue_arn         = module.sqs.queue_arn
}

# ──────────────────────────────────────────
# API Gateway: HTTP API → Lambda統合
# ──────────────────────────────────────────
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name      = var.project_name
  environment       = var.environment
  lambda_invoke_arn = module.lambda.invoke_arn
  lambda_arn        = module.lambda.arn
}

# ──────────────────────────────────────────
# CloudWatch Billing Alarm: 月額$50超過でSNS通知
# （通知受信後、手動でLambda Concurrency=0に設定して停止）
# ──────────────────────────────────────────
# ──────────────────────────────────────────
# SES: お問い合わせメール送信元アドレス検証
# ──────────────────────────────────────────
# ──────────────────────────────────────────
# Route53: resumeai.jp パブリックホスティングゾーン
# ──────────────────────────────────────────
resource "aws_route53_zone" "main" {
  name    = "resumeai.jp"
  comment = "resumeai.jp public hosted zone"
}

resource "aws_ses_email_identity" "contact" {
  email = "hosinozzz@gmail.com"
}

resource "aws_sns_topic" "cost_alert" {
  provider = aws.us_east_1
  name     = "${var.project_name}-cost-alert"
}

resource "aws_cloudwatch_metric_alarm" "cost_limit" {
  provider = aws.us_east_1

  alarm_name          = "${var.project_name}-monthly-cost-limit"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400
  statistic           = "Maximum"
  threshold           = var.monthly_cost_limit_usd
  alarm_description   = "月額コスト上限（$${var.monthly_cost_limit_usd}）超過。Lambda停止を検討してください。"
  alarm_actions       = [aws_sns_topic.cost_alert.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }
}
