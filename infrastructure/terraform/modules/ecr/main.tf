resource "aws_ecr_repository" "this" {
  for_each             = toset(var.repository_names)
  name                 = "${var.project_name}-${each.value}"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  tags = {
    Name = "${var.project_name}-${each.value}"
  }
}

# Keep each repo to the last 10 images so it doesn't grow unbounded --
# this stage has no CI/CD yet, but the policy is safe to have in place
# ahead of Jenkins/ECR pushes being wired up later.
resource "aws_ecr_lifecycle_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}
