# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "pantry_to_plate_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Package the Python code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda.zip"
}

# AWS Lambda Function
resource "aws_lambda_function" "pantry_backend" {
  function_name    = "pantry-to-plate-api"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.10"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      GEMINI_API_KEY = var.gemini_key
    }
  }

}

# API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "pantry_api" {
  name          = "pantry-to-plate-gateway"
  protocol_type = "HTTP"
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

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pantry_backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.pantry_api.execution_arn}/*/*"
}

# Output the API URL to the terminal after deployment
output "api_endpoint" {
  value = "${aws_apigatewayv2_api.pantry_api.api_endpoint}/generate"
}

# 5. CloudWatch Logs for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  # Lambda requires log groups to follow a very specific naming convention
  name = "/aws/lambda/${aws_lambda_function.pantry_backend.function_name}"

  # Automatically delete logs after 14 days to prevent unnecessary storage costs
  retention_in_days = 0
}