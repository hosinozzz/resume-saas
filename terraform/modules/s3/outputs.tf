output "bucket_id" {
  description = "S3バケット名（ID）"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "S3バケットARN（IAMポリシー等で使用）"
  value       = aws_s3_bucket.this.arn
}

output "bucket_regional_domain_name" {
  description = "CloudFront OACオリジン設定用のリージョナルドメイン名"
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}
