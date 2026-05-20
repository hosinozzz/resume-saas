variable "project_name" {
  description = "プロジェクト識別子"
  type        = string
}

variable "environment" {
  description = "デプロイ環境"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Lambda統合に使用するinvoke ARN"
  type        = string
}

variable "lambda_arn" {
  description = "Lambda関数ARN（aws_lambda_permission用）"
  type        = string
}
