#############################################
# General
#############################################
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Name prefix used to tag/name every resource"
  type        = string
  default     = "devopshub"
}

variable "environment" {
  description = "Deployment environment tag (e.g. production, staging)"
  type        = string
  default     = "production"
}

#############################################
# Networking
#############################################
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the public subnets (ALB), one per AZ"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the private subnets (ECS tasks + RDS), one per AZ"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "az_count" {
  description = "Number of Availability Zones to spread subnets across (2 is the minimum for an ALB + an RDS subnet group)"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Whether to create a NAT Gateway for private-subnet egress. Required for ECS tasks in private subnets to pull images from ECR and reach the Amazon SQS API."
  type        = bool
  default     = true
}

#############################################
# ECR / images
#############################################
variable "image_tag" {
  description = "Image tag to deploy for every service (pushed manually or by a future CI/CD stage; no Jenkins/CI wiring happens in this stage)"
  type        = string
  default     = "latest"
}

#############################################
# ECS
#############################################
variable "task_cpu" {
  description = "CPU units per task, applied uniformly to all 6 services (frontend, gateway, user/blog/category/notification-service)"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory (MB) per task, applied uniformly to all 6 services"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired running task count per service"
  type        = number
  default     = 1
}

#############################################
# RDS
#############################################
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_multi_az" {
  description = "Enable RDS Multi-AZ failover (off by default to control cost)"
  type        = bool
  default     = false
}

variable "db_master_username" {
  description = "RDS master username"
  type        = string
  default     = "devopshub"
}

variable "db_skip_final_snapshot" {
  description = "Skip the final RDS snapshot on destroy (true for dev/test convenience; set false for a real production environment)"
  type        = bool
  default     = true
}

#############################################
# SQS
#############################################
variable "sqs_queue_name" {
  description = "Base SQS queue name (matches the local ElasticMQ queue name \"notifications\")"
  type        = string
  default     = "notifications"
}

variable "sqs_max_receive_count" {
  description = "Failed processing attempts before a message moves to the DLQ"
  type        = number
  default     = 5
}

#############################################
# App-level (non-secret) config
#############################################
variable "jwt_expire_minutes" {
  description = "JWT token expiry, minutes (matches user-service's JWT_EXPIRE_MINUTES)"
  type        = number
  default     = 60
}
