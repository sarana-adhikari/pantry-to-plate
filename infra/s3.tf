# S3 Bucket for Static Website
resource "aws_s3_bucket" "frontend_bucket" {
  bucket = "pantry-to-plate-frontend-${random_id.id.hex}" # Needs to be unique
}

resource "random_id" "id" {
  byte_length = 4
}

# S3 Bucket Policy to allow CloudFront to read the files
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

output "s3_bucket_name" {
  value = aws_s3_bucket.frontend_bucket.bucket
}