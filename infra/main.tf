terraform {
  backend "s3" {
    bucket = "pantry-to-plate-tfstate-89313"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}