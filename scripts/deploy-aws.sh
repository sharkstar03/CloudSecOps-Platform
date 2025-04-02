#!/bin/bash

# Deploy CloudSecOps Platform to AWS
# Usage: ./deploy-aws.sh [environment]

set -e

# Default environment is development
ENVIRONMENT=${1:-development}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Configuration based on environment
case $ENVIRONMENT in
  production)
    TERRAFORM_WORKSPACE="production"
    AWS_REGION="us-east-1"
    echo "Deploying to PRODUCTION environment"
    ;;
  staging)
    TERRAFORM_WORKSPACE="staging"
    AWS_REGION="us-east-1"
    echo "Deploying to STAGING environment"
    ;;
  *)
    TERRAFORM_WORKSPACE="development"
    AWS_REGION="us-east-1"
    echo "Deploying to DEVELOPMENT environment"
    ;;
esac

# Check if required tools are installed
for tool in aws terraform docker jq; do
  if ! command -v $tool &> /dev/null; then
    echo "Error: $tool is required but not installed. Please install it first."
    exit 1
  fi
done

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
  echo "Error: AWS credentials not configured. Please configure AWS CLI first."
  exit 1
fi

echo "===== Building Docker Images ====="
# Build backend image
cd "$PROJECT_ROOT"
docker build -t cloudsecops/api:latest .

# Build frontend image
cd "$PROJECT_ROOT/frontend"
docker build -t cloudsecops/frontend:latest .

echo "===== Deploying Infrastructure with Terraform ====="
cd "$PROJECT_ROOT/infrastructure/terraform/aws"

# Initialize Terraform
terraform init

# Select or create workspace
if terraform workspace list | grep -q "$TERRAFORM_WORKSPACE"; then
  terraform workspace select "$TERRAFORM_WORKSPACE"
else
  terraform workspace new "$TERRAFORM_WORKSPACE"
fi

# Apply Terraform configuration
terraform apply -var "environment=$ENVIRONMENT" -var "region=$AWS_REGION" -auto-approve

# Get outputs
ECR_REPOSITORY=$(terraform output -raw ecr_repository_url)
ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
DB_ENDPOINT=$(terraform output -raw rds_endpoint)

echo "===== Pushing Docker Images to ECR ====="
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Tag and push backend image
docker tag cloudsecops/api:latest $ECR_REPOSITORY:api-latest
docker push $ECR_REPOSITORY:api-latest

# Tag and push frontend image
docker tag cloudsecops/frontend:latest $ECR_REPOSITORY:frontend-latest
docker push $ECR_REPOSITORY:frontend-latest

echo "===== Deploying ECS Tasks ====="
# Update ECS services to use new images
aws ecs update-service --cluster $ECS_CLUSTER --service cloudsecops-api-service --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster $ECS_CLUSTER --service cloudsecops-frontend-service --force-new-deployment --region $AWS_REGION

echo "===== Running Database Migrations ====="
# Run database migrations
cd "$PROJECT_ROOT"
python -m alembic upgrade head

echo "===== Deployment Completed Successfully ====="
echo "API Service URL: https://api.cloudsecops.example.com"
echo "Frontend URL: https://cloudsecops.example.com"
echo ""
echo "To monitor the deployment status, check the AWS Management Console or run:"
echo "aws ecs describe-services --cluster $ECS_CLUSTER --services cloudsecops-api-service cloudsecops-frontend-service --region $AWS_REGION"