variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "secrets_manager_secret_arns" {
  description = "Secrets Manager secret ARNs the ECS task execution role is allowed to read (JWT secret + per-service DATABASE_URL secrets), so they can be injected into containers via the task definition's \"secrets\" block"
  type        = list(string)
}

variable "sqs_queue_arn" {
  description = "ARN of the notifications SQS queue (user-service/blog-service send, notification-service receives/deletes)"
  type        = string
}
