variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "queue_name" {
  description = "Base queue name (matches the local ElasticMQ queue name \"notifications\" used in docker-compose)"
  type        = string
  default     = "notifications"
}

variable "visibility_timeout_seconds" {
  description = "Time a message is hidden after being received, before it's eligible for redelivery"
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "How long SQS retains messages (default 4 days)"
  type        = number
  default     = 345600
}

variable "max_receive_count" {
  description = "Number of failed processing attempts before a message moves to the DLQ"
  type        = number
  default     = 5
}
