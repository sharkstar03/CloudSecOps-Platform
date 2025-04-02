#!/bin/bash
cd infrastructure/terraform/aws
terraform init
terraform apply -auto-approve
aws lambda update-function-code --function-name cloudsecops-scanner --zip-file fileb://../../../backend/scanners/aws_scanner.zip