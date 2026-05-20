resource "aws_dynamodb_table" "rate_limit" {
  name         = "${var.project_name}-rate-limit-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"

  attribute {
    name = "pk"
    type = "S"
  }

  # TTL: Pythonで ttl = int(time.time()) + 7200 をセット → DynamoDBが自動削除
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}
