variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of AZs to spread public/private subnets across (2 recommended for ALB + RDS subnet group)"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the public subnets (one per AZ), used by the ALB"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the private subnets (one per AZ), used by ECS tasks and RDS"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Whether to create a NAT Gateway for private subnet egress (required for ECS tasks in private subnets to reach ECR/SQS/CloudWatch)"
  type        = bool
  default     = true
}
