variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "create_bucket" {
  description = "Whether to create the S3 bucket"
  type        = bool
  default     = false
}

variable "bucket_name" {
  description = "Name of the S3 bucket (must be globally unique)"
  type        = string
}
