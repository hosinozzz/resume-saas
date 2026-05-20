resource "aws_apigatewayv2_api" "this" {
  name          = "${var.project_name}-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    # 初期はワイルドカード。CloudFrontデプロイ後にドメインを限定すること
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type", "stripe-signature"]
    max_age       = 300
  }
}

# Lambda プロキシ統合（payload format 2.0 = HTTP API推奨形式）
resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_invoke_arn
  payload_format_version = "2.0"
}

# ルート定義: handler.py側でevent.rawPathを見てディスパッチする
locals {
  routes = toset([
    "POST /upload",
    "GET /status/{job_id}",
    "POST /payment/checkout",
    "POST /payment/webhook",
    "GET /payment/clean-url",
    "GET /health",
  ])
}

resource "aws_apigatewayv2_route" "routes" {
  for_each = local.routes

  api_id    = aws_apigatewayv2_api.this.id
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# $defaultステージ: 自動デプロイ有効
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  depends_on = [aws_apigatewayv2_route.routes]
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

# API GatewayからLambdaを呼び出す権限
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
