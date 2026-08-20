variable "project_name" {
  description = "Name prefix used to tag/name resources"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the RDS subnet group (RDS is never publicly exposed)"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID allowing only ECS tasks to reach PostgreSQL"
  type        = string
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.4"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "multi_az" {
  description = "Whether to enable Multi-AZ failover (costs more; off by default to control cost, matching the reference architecture's documented tradeoff)"
  type        = bool
  default     = false
}

variable "master_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "devopshub"
}

variable "backup_retention_period" {
  description = "Days to retain automated backups"
  type        = number
  default     = 7
}

variable "skip_final_snapshot" {
  description = "Whether to skip the final snapshot on destroy (true is convenient for dev/test, false is safer for production)"
  type        = bool
  default     = true
}

variable "service_database_names" {
  description = "Logical database names to provision connection-string secrets for, one per microservice that owns its own tables (matches db-init/01-create-databases.sh: userdb, blogdb, categorydb, notificationdb)"
  type        = list(string)
  default     = ["userdb", "blogdb", "categorydb", "notificationdb"]
}
