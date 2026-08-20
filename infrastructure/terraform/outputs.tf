output "website_url" {
  description = "Public URL of the application (ALB DNS name)"
  value       = "http://${module.alb.alb_dns_name}"
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "ecr_repository_urls" {
  description = "Map of short name -> ECR repository URL, for docker push"
  value       = module.ecr.repository_urls
}

output "ecs_cluster_name" {
  value = module.ecs_cluster.cluster_name
}

output "rds_endpoint" {
  description = "RDS host:port (not publicly reachable -- accessible only from inside the VPC)"
  value       = module.rds.endpoint
}

output "rds_master_secret_arn" {
  description = "Secrets Manager ARN with the RDS master username/password -- needed once to run db-init/01-create-databases.sh's CREATE DATABASE statements against this instance (see IMPLEMENTATION_STATUS.md)"
  value       = module.rds.master_secret_arn
}

output "sqs_queue_url" {
  value = module.sqs.queue_url
}

output "sqs_dlq_url" {
  value = module.sqs.dlq_url
}
