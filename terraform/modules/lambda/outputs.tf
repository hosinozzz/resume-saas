output "function_name" {
  description = "main Lambda関数名"
  value       = aws_lambda_function.main.function_name
}

output "arn" {
  description = "main Lambda関数ARN"
  value       = aws_lambda_function.main.arn
}

output "invoke_arn" {
  description = "API Gateway統合に使用するinvoke ARN"
  value       = aws_lambda_function.main.invoke_arn
}

output "function_url" {
  description = "Lambda Function URL（/upload直接呼び出し用）"
  value       = aws_lambda_function_url.upload.function_url
}

output "worker_function_name" {
  description = "worker Lambda関数名"
  value       = aws_lambda_function.worker.function_name
}
