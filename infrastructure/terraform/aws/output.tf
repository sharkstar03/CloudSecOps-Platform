output "api_gateway_url" {
  description = "The URL of the API Gateway"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.backend.function_name
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket for static frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "security_group_id" {
  description = "Security Group ID for the application"
  value       = aws_security_group.app_sg.id
}

output "iam_role_arn" {
  description = "IAM Role ARN for the application"
  value       = aws_iam_role.lambda_exec.arn
}