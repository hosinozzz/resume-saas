variable "bucket_name" {
  description = "S3バケット名（グローバルで一意）"
  type        = string
}

variable "purpose" {
  description = "バケット用途（frontend / generated）"
  type        = string

  validation {
    condition     = contains(["frontend", "generated"], var.purpose)
    error_message = "purpose は frontend または generated のみ指定可能。"
  }
}

variable "expiration_days" {
  description = "全オブジェクトの自動削除日数（0=無効）。生成HTMLに適用"
  type        = number
  default     = 0
}

variable "upload_expiration_days" {
  description = "uploaded/ プレフィックスのオブジェクト削除日数（0=無効）。アップロード原本に適用"
  type        = number
  default     = 0
}

variable "cors_allowed_origins" {
  description = "CORSで許可するオリジン一覧（空リスト=CORS設定なし）"
  type        = list(string)
  default     = []
}
