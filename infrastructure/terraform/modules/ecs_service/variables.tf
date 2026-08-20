variable "project_name" {
  type = string
}

variable "service_name" {
  description = "Short name, matches the docker-compose service name exactly (e.g. \"user-service\", \"gateway\", \"frontend\") -- used as the Service Connect discovery name so inter-service URLs need no code changes"
  type        = string
}

variable "container_image" {
  description = "Full ECR image URI (repo:tag)"
  type        = string
}

variable "container_port" {
  type = number
}

variable "cpu" {
  type    = number
  default = 256
}

variable "memory" {
  type    = number
  default = 512
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "environment" {
  description = "Plain (non-secret) environment variables"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Map of env var name -> Secrets Manager secret ARN, resolved into the container at start"
  type        = map(string)
  default     = {}
}

variable "cluster_id" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "namespace_arn" {
  description = "Service Connect (Cloud Map HTTP namespace) ARN"
  type        = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "execution_role_arn" {
  type = string
}

variable "task_role_arn" {
  description = "Optional -- only services that call AWS APIs (SQS) need one"
  type        = string
  default     = null
}

variable "target_group_arn" {
  description = "Optional -- only the frontend service is registered with the ALB"
  type        = string
  default     = null
}

variable "aws_region" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 14
}
