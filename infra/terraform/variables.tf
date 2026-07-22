variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "db_password" {
  description = "PostgreSQL password"
  sensitive   = true
}

variable "private_subnets" {
  description = "Private subnet IDs"
  type        = list(string)
}
