output "domain_name" {
  description = "CloudFrontドメイン名（root outputs.tfのcloudfront_urlで使用）"
  value       = aws_cloudfront_distribution.this.domain_name
}

output "distribution_id" {
  description = "CloudFrontディストリビューションID（デプロイ時のキャッシュ無効化に使用）"
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "CloudFrontディストリビューションARN"
  value       = aws_cloudfront_distribution.this.arn
}
