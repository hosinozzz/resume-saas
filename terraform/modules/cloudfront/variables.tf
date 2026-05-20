variable "frontend_bucket_id" {
  description = "フロントエンドS3バケット名（バケットポリシー適用先）"
  type        = string
}

variable "frontend_bucket_regional_domain_name" {
  description = "CloudFrontオリジン設定用リージョナルドメイン名"
  type        = string
}

variable "project_name" {
  description = "プロジェクト識別子"
  type        = string
}

variable "environment" {
  description = "デプロイ環境"
  type        = string
}
