output "table_name" {
  description = "DynamoDBテーブル名（Lambda環境変数に渡す）"
  value       = aws_dynamodb_table.rate_limit.name
}

output "table_arn" {
  description = "DynamoDBテーブルARN（IAMポリシーに渡す）"
  value       = aws_dynamodb_table.rate_limit.arn
}
