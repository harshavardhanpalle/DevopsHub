resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${var.project_name}-${var.service_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-${var.service_name}-logs"
  }
}

resource "aws_ecs_task_definition" "this" {
  family                   = "${var.project_name}-${var.service_name}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = var.container_image
      essential = true
      portMappings = [
        {
          name          = var.service_name
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        for k, v in var.environment : { name = k, value = v }
      ]
      secrets = [
        for k, arn in var.secrets : { name = k, valueFrom = arn }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = var.service_name
        }
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.service_name}-task"
  }
}

resource "aws_ecs_service" "this" {
  name            = "${var.project_name}-${var.service_name}"
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = var.namespace_arn

    service {
      port_name      = var.service_name
      discovery_name = var.service_name

      client_alias {
        port = var.container_port
      }
    }

    log_configuration {
      log_driver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.this.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "${var.service_name}-service-connect"
      }
    }
  }

  dynamic "load_balancer" {
    for_each = var.target_group_arn != null ? [1] : []
    content {
      target_group_arn = var.target_group_arn
      container_name   = var.service_name
      container_port   = var.container_port
    }
  }

  # Only the frontend service has an ALB health check gating deployments;
  # others are internal-only and reachable solely via Service Connect.
  health_check_grace_period_seconds = var.target_group_arn != null ? 60 : null

  tags = {
    Name = "${var.project_name}-${var.service_name}-service"
  }
}
