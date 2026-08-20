output "endpoint" {
  description = "RDS connection endpoint (host:port)"
  value       = aws_db_instance.this.endpoint
}

output "address" {
  description = "RDS hostname only"
  value       = aws_db_instance.this.address
}

output "port" {
  description = "RDS port"
  value       = aws_db_instance.this.port
}

output "master_secret_arn" {
  description = "Secrets Manager ARN holding the master username/password/host/port (for admin/db-init use, e.g. running db-init/01-create-databases.sh once against this instance)"
  value       = aws_secretsmanager_secret.rds_master.arn
}

output "database_url_secret_arns" {
  description = "Map of service database name -> Secrets Manager ARN holding its full DATABASE_URL, for use in ECS task definitions"
  value       = { for k, v in aws_secretsmanager_secret.database_url : k => v.arn }
}
