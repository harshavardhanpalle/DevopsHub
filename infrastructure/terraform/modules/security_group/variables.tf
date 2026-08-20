variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC the security groups belong to"
  type        = string
}

variable "container_ports" {
  description = "Container ports used across the ECS services (frontend, gateway, user/blog/category/notification-service), opened for intra-cluster (self-referencing) traffic only"
  type        = list(number)
}

variable "rds_port" {
  description = "PostgreSQL port"
  type        = number
  default     = 5432
}
