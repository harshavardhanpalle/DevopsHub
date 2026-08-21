terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0, < 6.0.0" # >= 5.40 for aws_ecs_service.service_connect_configuration
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "s3" {
    bucket         = "devopshub-tfstate-bucket"
    key            = "devopshub/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "devopshub-tf-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
