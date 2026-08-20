output "ecs_task_execution_role_arn" {
  description = "ARN of the shared ECS task execution role (all 6 services)"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "app_task_role_arn" {
  description = "ARN of the SQS-scoped app task role (user-service, blog-service, notification-service only)"
  value       = aws_iam_role.app_task.arn
}
