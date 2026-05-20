output "cloudfront_url" {
  description = "サービスのメインURL（CloudFront）"
  value       = "https://${module.cloudfront.domain_name}"
}

output "api_gateway_url" {
  description = "API GatewayエンドポイントURL（フロントからのAPIコール先）"
  value       = module.api_gateway.invoke_url
}

output "frontend_bucket_name" {
  description = "フロントエンド静的ファイルのデプロイ先S3バケット名"
  value       = module.s3_frontend.bucket_id
}

output "generated_bucket_name" {
  description = "生成HTMLの一時保存先S3バケット名"
  value       = module.s3_generated.bucket_id
}

output "dynamodb_table_name" {
  description = "IPレート制限テーブル名"
  value       = module.dynamodb.table_name
}

output "lambda_function_name" {
  description = "main Lambda関数名（コスト超過時は Concurrency=0 で停止）"
  value       = module.lambda.function_name
}

output "worker_function_name" {
  description = "worker Lambda関数名（SQSトリガー / Claude API処理）"
  value       = module.lambda.worker_function_name
}

output "upload_function_url" {
  description = "/upload・/status専用 Lambda Function URL"
  value       = module.lambda.function_url
}

output "sqs_queue_url" {
  description = "ワーカーキューURL（モニタリング・デバッグ用）"
  value       = module.sqs.queue_url
}

output "cost_alert_sns_arn" {
  description = "コストアラートSNSトピックARN（メール購読はAWSコンソールから設定）"
  value       = aws_sns_topic.cost_alert.arn
}

output "route53_zone_id" {
  description = "resumeai.jp Route53ホスティングゾーンID"
  value       = aws_route53_zone.main.zone_id
}

output "route53_name_servers" {
  description = "resumeai.jp のNSレコード（ドメインレジストラに設定する4つのネームサーバー）"
  value       = aws_route53_zone.main.name_servers
}

output "acm_certificate_arn" {
  description = "resumeai.jp ACM証明書ARN（us-east-1）"
  value       = aws_acm_certificate_validation.resumeai_jp.certificate_arn
}
