terraform {
  backend "s3" {
    bucket = "pantry-to-plate-tfstate-89313" # Use the exact name you just created
    key    = "prod/terraform.tfstate"        # The file path inside the bucket
    region = "us-east-1"
  }
}

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

# 6. S3 Bucket for Static Website
resource "aws_s3_bucket" "frontend_bucket" {
  bucket = "pantry-to-plate-frontend-${random_id.id.hex}" # Needs to be unique
}

resource "random_id" "id" {
  byte_length = 4
}

# 7. CloudFront Origin Access Control (OAC) 
# This ensures people can't bypass CloudFront to access your S3 bucket directly
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "s3_oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# 8. CloudFront Distribution
resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name              = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    origin_id                = "S3Origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Origin"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# 9. S3 Bucket Policy to allow CloudFront to read the files
data "aws_iam_policy_document" "s3_policy" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend_bucket.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.s3_distribution.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend_bucket_policy" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = data.aws_iam_policy_document.s3_policy.json
}

# Output the Website URL
output "website_url" {
  value = aws_cloudfront_distribution.s3_distribution.domain_name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.frontend_bucket.bucket
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.s3_distribution.id
}