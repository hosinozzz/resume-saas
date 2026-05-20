resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
}

# パブリックアクセスを全面禁止（署名付きURL or OAC経由のみ）
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CORS（フロントエンドからの fetch ダウンロード用。generated バケットのみ設定）
resource "aws_s3_bucket_cors_configuration" "this" {
  count  = length(var.cors_allowed_origins) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  cors_rule {
    allowed_origins = var.cors_allowed_origins
    allowed_methods = ["GET"]
    allowed_headers = ["*"]
    max_age_seconds = 3600
  }
}

# ライフサイクルルール（いずれかの期限が設定されているときのみ有効）
resource "aws_s3_bucket_lifecycle_configuration" "expiration" {
  count  = (var.expiration_days > 0 || var.upload_expiration_days > 0) ? 1 : 0
  bucket = aws_s3_bucket.this.id

  # 全オブジェクト対象（生成HTML: {job_id}/preview.html, {job_id}/clean.html 等）
  dynamic "rule" {
    for_each = var.expiration_days > 0 ? [1] : []
    content {
      id     = "expire-objects"
      status = "Enabled"

      filter {}

      expiration {
        days = var.expiration_days
      }

      abort_incomplete_multipart_upload {
        days_after_initiation = 1
      }
    }
  }

  # uploaded/ プレフィックス専用（アップロード原本: uploaded/{job_id}/resume.txt）
  dynamic "rule" {
    for_each = var.upload_expiration_days > 0 ? [1] : []
    content {
      id     = "expire-uploaded-originals"
      status = "Enabled"

      filter {
        prefix = "uploaded/"
      }

      expiration {
        days = var.upload_expiration_days
      }

      abort_incomplete_multipart_upload {
        days_after_initiation = 1
      }
    }
  }
}
