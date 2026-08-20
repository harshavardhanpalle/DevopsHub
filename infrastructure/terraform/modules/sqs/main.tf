#############################################
# Dead Letter Queue -- catches messages notification-service fails to
# process after max_receive_count attempts (matches the app's existing
# "don't delete on processing failure" retry behavior from Stage 1.5;
# without a DLQ a permanently malformed message redelivers forever).
#############################################
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-${var.queue_name}-dlq"
  message_retention_seconds = 1209600 # 14 days -- give time to inspect/replay

  tags = {
    Name = "${var.project_name}-${var.queue_name}-dlq"
  }
}

#############################################
# Main notifications queue -- user-service/blog-service publish
# USER_REGISTERED / ARTICLE_PUBLISHED events here; notification-service
# consumes them. Matches the local queue name "notifications" from
# local-sqs/elasticmq.conf so no app code changes are needed.
#############################################
resource "aws_sqs_queue" "main" {
  name                       = "${var.project_name}-${var.queue_name}"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name = "${var.project_name}-${var.queue_name}"
  }
}

# Lets CloudWatch alarm on the DLQ depth later without extra wiring; not a
# new service, just an allowed source for the DLQ (SQS-to-SQS redrive is
# already covered by redrive_policy above, this is redrive_allow_policy on
# the DLQ side so the main queue is permitted to redrive into it).
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.main.arn]
  })
}
