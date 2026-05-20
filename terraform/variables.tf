variable "aws_region" {
  description = "AWSリージョン（デフォルト: 東京）"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "プロジェクト識別子。全リソース名のプレフィックスに使用"
  type        = string
  default     = "resume-saas"
}

variable "environment" {
  description = "デプロイ環境"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment は dev または prod のみ指定可能。"
  }
}

variable "monthly_cost_limit_usd" {
  description = "月額コスト上限（USD）。超過時にCloudWatchアラームが発火"
  type        = number
  default     = 50
}

variable "max_requests_per_hour" {
  description = "同一IPアドレスからの1時間あたり最大リクエスト数"
  type        = number
  default     = 3
}
