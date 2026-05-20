# DLQ: 3回失敗したメッセージをここへ移動（デバッグ用に1日保持）
resource "aws_sqs_queue" "worker_dlq" {
  name                      = "${var.project_name}-worker-dlq-${var.environment}"
  message_retention_seconds = 86400 # 1日
}

# ワーカーキュー: visibility_timeoutはworker Lambdaのタイムアウト（900秒）と揃える
resource "aws_sqs_queue" "worker" {
  name                       = "${var.project_name}-worker-${var.environment}"
  visibility_timeout_seconds = 900   # worker Lambdaのタイムアウトと同値
  message_retention_seconds  = 86400 # 1日

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.worker_dlq.arn
    maxReceiveCount     = 3
  })
}
