#############################################
# ECS Task Execution Role -- used by every service (frontend, gateway, and
# the 4 microservices) to pull images from ECR, ship logs to CloudWatch, and
# resolve the "secrets" block (JWT_SECRET / DATABASE_URL) at container start.
#############################################
data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.project_name}-ecs-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = {
    Name = "${var.project_name}-ecs-task-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "secrets_read" {
  statement {
    sid       = "ReadTaskSecrets"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = var.secrets_manager_secret_arns
  }
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name   = "${var.project_name}-ecs-task-execution-secrets"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.secrets_read.json
}

#############################################
# App Task Role -- attached only to user-service, blog-service, and
# notification-service (the SQS producers/consumer); scoped to exactly the
# one notifications queue + its DLQ, nothing else. Frontend, gateway, and
# category-service call no AWS APIs, so they get no task role.
#############################################
data "aws_iam_policy_document" "sqs_access" {
  statement {
    sid = "SendAndReceiveNotifications"
    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
    ]
    resources = [var.sqs_queue_arn]
  }
}

resource "aws_iam_role" "app_task" {
  name               = "${var.project_name}-app-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = {
    Name = "${var.project_name}-app-task-role"
  }
}

resource "aws_iam_role_policy" "app_task_sqs" {
  name   = "${var.project_name}-app-task-sqs"
  role   = aws_iam_role.app_task.id
  policy = data.aws_iam_policy_document.sqs_access.json
}
