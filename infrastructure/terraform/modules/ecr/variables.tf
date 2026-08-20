variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "repository_names" {
  description = "Short names (e.g. \"frontend\", \"gateway\", \"user-service\") to create ECR repos for; final repo name is <project_name>-<name>"
  type        = list(string)
}

variable "image_tag_mutability" {
  description = "IMMUTABLE or MUTABLE"
  type        = string
  default     = "MUTABLE"
}

variable "scan_on_push" {
  description = "Whether ECR should scan images for vulnerabilities on push"
  type        = bool
  default     = true
}
