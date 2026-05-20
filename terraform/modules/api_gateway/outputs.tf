output "invoke_url" {
  description = "API GatewayエンドポイントURL（フロントエンドのAPI_BASE_URLに設定）"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.this.id
}

output "execution_arn" {
  description = "API Gateway実行ARN"
  value       = aws_apigatewayv2_api.this.execution_arn
}
