output "queue_url" {
  description = "ワーカーキューURL（main LambdaのSQS_QUEUE_URL環境変数に設定）"
  value       = aws_sqs_queue.worker.url
}

output "queue_arn" {
  description = "ワーカーキューARN（IAMポリシーとevent source mappingに使用）"
  value       = aws_sqs_queue.worker.arn
}

output "dlq_arn" {
  description = "DLQ ARN（監視用）"
  value       = aws_sqs_queue.worker_dlq.arn
}
