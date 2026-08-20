output "bucket_name" {
  description = "Name of the S3 bucket, if created"
  value       = var.create_bucket ? aws_s3_bucket.assets[0].bucket : null
}

output "bucket_arn" {
  description = "ARN of the S3 bucket, if created"
  value       = var.create_bucket ? aws_s3_bucket.assets[0].arn : null
}
