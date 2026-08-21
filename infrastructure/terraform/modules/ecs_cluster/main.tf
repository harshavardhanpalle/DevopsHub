resource "aws_ecs_cluster" "this" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

resource "aws_service_discovery_http_namespace" "this" {
  name = "${var.project_name}.local"

  description = "Service Connect namespace for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-namespace"
  }
}
