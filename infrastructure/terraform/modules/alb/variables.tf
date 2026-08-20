variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB"
  type        = list(string)
}

variable "security_group_id" {
  description = "ALB security group ID"
  type        = string
}

variable "health_check_path" {
  description = "Health check path on the frontend container"
  type        = string
  default     = "/"
}
