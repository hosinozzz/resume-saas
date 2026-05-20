variable "project_name" {
  description = "プロジェクト識別子"
  type        = string
}

variable "environment" {
  description = "デプロイ環境"
  type        = string
}

variable "dynamodb_table_name" {
  description = "IPレート制限・ジョブステータス共用テーブル名"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDBテーブルARN（IAMポリシーに使用）"
  type        = string
}

variable "generated_bucket_name" {
  description = "生成ファイル一時保存バケット名"
  type        = string
}

variable "generated_bucket_arn" {
  description = "生成ファイル一時保存バケットARN（IAMポリシーに使用）"
  type        = string
}

variable "max_requests_per_hour" {
  description = "IPアドレスあたりの1時間あたり最大リクエスト数"
  type        = number
}

variable "sqs_queue_url" {
  description = "ワーカーキューURL（main LambdaのSQS_QUEUE_URL環境変数に設定）"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ワーカーキューARN（IAMポリシーとevent source mappingに使用）"
  type        = string
}
