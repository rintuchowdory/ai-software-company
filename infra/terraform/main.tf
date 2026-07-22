terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ECS Cluster
resource "aws_ecs_cluster" "ai_company" {
  name = "ai-software-company"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Service
resource "aws_ecs_service" "orchestrator" {
  name            = "orchestrator"
  cluster         = aws_ecs_cluster.ai_company.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  desired_count   = 2

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.orchestrator.id]
    assign_public_ip = false
  }
}

# RDS
resource "aws_db_instance" "project_state" {
  identifier        = "ai-company-state"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "project_state"
  username          = "aicompany"
  password          = var.db_password
  backup_retention_period = 7
  deletion_protection     = true
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "ai-company-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# Security Group
resource "aws_security_group" "orchestrator" {
  name_prefix = "ai-company-"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
