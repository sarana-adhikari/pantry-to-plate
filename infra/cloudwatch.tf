# CloudWatch Logs for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  # Lambda requires log groups to follow a very specific naming convention
  name = "/aws/lambda/${aws_lambda_function.pantry_backend.function_name}"

  # Automatically delete logs after 14 days to prevent unnecessary storage costs
  retention_in_days = 0
}