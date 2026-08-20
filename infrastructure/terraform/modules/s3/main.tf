#############################################
# S3 Bucket (optional, e.g. for static assets/backups)
#############################################
resource "aws_s3_bucket" "assets" {
  count  = var.create_bucket ? 1 : 0
  bucket = var.bucket_name

  tags = {
    Name = "${var.project_name}-assets"
  }
}
