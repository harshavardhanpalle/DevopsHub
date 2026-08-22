#############################################
# ALB Security Group -- public entry point
#############################################
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Allow public HTTP (and HTTPS, once a cert is added) into the ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "To ECS tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

#############################################
# ECS Tasks Security Group -- frontend, gateway, and the 4 microservices all
# share this SG. Only the frontend's port is reachable from the ALB; all
# other inter-service traffic (frontend->gateway, gateway->services) is
# self-referencing, since ECS Service Connect keeps every task on this SG.
#############################################
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks-sg"
  description = "ECS Fargate tasks (frontend, gateway, user/blog/category/notification-service)"
  vpc_id      = var.vpc_id

  ingress {
    description     = "ALB to frontend (port 80)"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  dynamic "ingress" {
    for_each = var.container_ports
    content {
      description = "Intra-cluster: Service Connect traffic between frontend/gateway/services"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      self        = true
    }
  }

  egress {
    description = "All outbound (ECR pulls, SQS API, CloudWatch Logs, RDS)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-tasks-sg"
  }
}

#############################################
# RDS Security Group -- only reachable from ECS tasks, never public
#############################################
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "PostgreSQL, reachable only from ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "ECS tasks to PostgreSQL"
    from_port       = var.rds_port
    to_port         = var.rds_port
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}
