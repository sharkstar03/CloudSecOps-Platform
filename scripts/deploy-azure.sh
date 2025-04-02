#!/bin/bash
# CloudSecOps Platform - Azure Deployment Script
# This script deploys the platform components to Azure

set -e

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found. Make sure all required environment variables are set."
fi

# Check for required environment variables
required_vars=(
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET"
    "AZURE_TENANT_ID"
    "AZURE_SUBSCRIPTION_ID"
    "RESOURCE_GROUP_NAME"
    "LOCATION"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set."
        exit 1
    fi
done

echo "==== CloudSecOps Platform - Azure Deployment ===="
echo "Subscription: $AZURE_SUBSCRIPTION_ID"
echo "Resource Group: $RESOURCE_GROUP_NAME"
echo "Location: $LOCATION"

# Login to Azure
echo "Authenticating with Azure..."
az login --service-principal \
    --username "$AZURE_CLIENT_ID" \
    --password "$AZURE_CLIENT_SECRET" \
    --tenant "$AZURE_TENANT_ID"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"

# Create resource group if it doesn't exist
echo "Ensuring resource group exists..."
az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION" --tags "Project=CloudSecOps" "Environment=${ENVIRONMENT:-production}"

# Deploy infrastructure using Terraform
echo "Deploying infrastructure with Terraform..."
cd infrastructure/terraform/azure

echo "Initializing Terraform..."
terraform init

echo "Validating Terraform configuration..."
terraform validate

echo "Applying Terraform configuration..."
terraform apply -auto-approve \
    -var="client_id=$AZURE_CLIENT_ID" \
    -var="client_secret=$AZURE_CLIENT_SECRET" \
    -var="tenant_id=$AZURE_TENANT_ID" \
    -var="subscription_id=$AZURE_SUBSCRIPTION_ID" \
    -var="location=$LOCATION" \
    -var="resource_group_name=$RESOURCE_GROUP_NAME" \
    -var="environment=${ENVIRONMENT:-production}"

# Get outputs for further deployment steps
FUNCTION_APP_NAME=$(terraform output -raw function_app_name)
STORAGE_ACCOUNT_NAME=$(terraform output -raw storage_account_name)
KEY_VAULT_NAME=$(terraform output -raw key_vault_name)

echo "Infrastructure deployment complete."
echo "Function App: $FUNCTION_APP_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"

# Build and deploy backend
echo "Building backend application..."
cd ../../../backend

# Install dependencies
pip install -r requirements.txt

# Package the backend code
echo "Packaging backend application..."
mkdir -p dist
zip -r dist/backend.zip api/ integrations/ scanners/ requirements.txt

# Deploy to Azure Function App
echo "Deploying backend to Azure Function App..."
az functionapp deployment source config-zip \
    -g "$RESOURCE_GROUP_NAME" \
    -n "$FUNCTION_APP_NAME" \
    --src dist/backend.zip

# Build and deploy frontend
echo "Building frontend application..."
cd ../frontend

# Install dependencies
npm install

# Create production build
npm run build

# Upload to Azure Blob Storage
echo "Deploying frontend to Azure Storage Account..."
az storage blob upload-batch \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --auth-mode key \
    --destination '$web' \
    --source build/ \
    --overwrite

# Enable static website hosting
az storage blob service-properties update \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --static-website \
    --index-document index.html \
    --404-document index.html

# Get the frontend URL
FRONTEND_URL=$(az storage account show \
    -n "$STORAGE_ACCOUNT_NAME" \
    -g "$RESOURCE_GROUP_NAME" \
    --query "primaryEndpoints.web" \
    --output tsv)

echo "===== Deployment Complete ====="
echo "Backend API: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo "Frontend URL: $FRONTEND_URL"
echo "============================================="

# Add app settings/environment variables to Function App
echo "Configuring application settings..."
az functionapp config appsettings set \
    -g "$RESOURCE_GROUP_NAME" \
    -n "$FUNCTION_APP_NAME" \
    --settings \
    "FRONTEND_URL=$FRONTEND_URL" \
    "KEY_VAULT_NAME=$KEY_VAULT_NAME" \
    "AZURE_TENANT_ID=$AZURE_TENANT_ID"

echo "Deployment to Azure completed successfully!"