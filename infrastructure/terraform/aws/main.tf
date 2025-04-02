provider "aws" {
  region = var.aws_region
}

resource "aws_lambda_function" "security_scanner" {
  function_name = "cloudsecops-scanner"
  runtime       = "python3.11"
  handler       = "handler.lambda_handler"
  filename      = "../../../backend/scanners/aws_scanner.zip"
}