output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.this.arn
}

output "alb_dns_name" {
  description = "Public DNS name of the ALB -- the application's entry point"
  value       = aws_lb.this.dns_name
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

output "http_listener_arn" {
  description = "ARN of the HTTP:80 listener"
  value       = aws_lb_listener.http.arn
}
