# API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "pantry_api" {
  name          = "pantry-to-plate-gateway"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"] # In production, I'd limit this to my CloudFront URL
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.pantry_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.pantry_backend.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "generate_recipe_route" {
  api_id    = aws_apigatewayv2_api.pantry_api.id
  route_key = "POST /generate"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.pantry_api.id
  name        = "$default"
  auto_deploy = true
}

# Output the API URL to the terminal after deployment
output "api_endpoint" {
  value = "${aws_apigatewayv2_api.pantry_api.api_endpoint}/generate"
}