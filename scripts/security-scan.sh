#!/bin/bash

# Security scan script for CloudSecOps Platform
# Usage: ./security-scan.sh [output-directory]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
OUTPUT_DIR=${1:-"$PROJECT_ROOT/security-reports"}
DATE_SUFFIX=$(date +"%Y%m%d_%H%M%S")

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "===== Running Security Scans for CloudSecOps Platform ====="
echo "Results will be saved to: $OUTPUT_DIR"

# Check if required tools are installed
missing_tools=0

check_tool() {
  if ! command -v $1 &> /dev/null; then
    echo "Warning: $1 is not installed, skipping related scans."
    missing_tools=1
    return 1
  fi
  return 0
}

# Docker image scanning with Trivy
if check_tool trivy; then
  echo "===== Scanning Docker Images with Trivy ====="
  trivy image --format json --output "$OUTPUT_DIR/trivy-api-$DATE_SUFFIX.json" cloudsecops/api:latest
  trivy image --format json --output "$OUTPUT_DIR/trivy-frontend-$DATE_SUFFIX.json" cloudsecops/frontend:latest
  echo "Docker image scanning completed."
fi

# Python dependency check with Safety
if check_tool safety && [ -f "$PROJECT_ROOT/requirements.txt" ]; then
  echo "===== Checking Python Dependencies with Safety ====="
  safety check -r "$PROJECT_ROOT/requirements.txt" --json > "$OUTPUT_DIR/safety-$DATE_SUFFIX.json"
  echo "Python dependency check completed."
fi

# JavaScript dependency check with npm audit
if check_tool npm && [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
  echo "===== Checking JavaScript Dependencies with npm audit ====="
  cd "$PROJECT_ROOT/frontend"
  npm audit --json > "$OUTPUT_DIR/npm-audit-$DATE_SUFFIX.json" || true
  echo "JavaScript dependency check completed."
  cd "$PROJECT_ROOT"
fi

# Static code analysis with Bandit for Python
if check_tool bandit; then
  echo "===== Running Static Code Analysis with Bandit ====="
  bandit -r "$PROJECT_ROOT/backend" -f json -o "$OUTPUT_DIR/bandit-$DATE_SUFFIX.json"
  echo "Python static code analysis completed."
fi

# Static code analysis with ESLint for JavaScript
if check_tool npx && [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
  echo "===== Running Static Code Analysis with ESLint ====="
  cd "$PROJECT_ROOT/frontend"
  npx eslint --format json --output-file "$OUTPUT_DIR/eslint-$DATE_SUFFIX.json" src || true
  echo "JavaScript static code analysis completed."
  cd "$PROJECT_ROOT"
fi

# Infrastructure as Code scanning with TFSec
if check_tool tfsec; then
  echo "===== Scanning Terraform Code with TFSec ====="
  tfsec "$PROJECT_ROOT/infrastructure/terraform" --format json --out "$OUTPUT_DIR/tfsec-$DATE_SUFFIX.json"
  echo "Terraform security scanning completed."
fi

# Secret scanning with GitLeaks
if check_tool gitleaks; then
  echo "===== Scanning for Secrets with GitLeaks ====="
  gitleaks detect --source "$PROJECT_ROOT" --report-format json --report-path "$OUTPUT_DIR/gitleaks-$DATE_SUFFIX.json"
  echo "Secret scanning completed."
fi

# OWASP ZAP API scanning (requires running API)
if check_tool zap-cli; then
  echo "===== Running OWASP ZAP API Scan ====="
  
  # Check if API is running
  if curl -s http://localhost:8000/health >/dev/null; then
    zap-cli quick-scan --self-contained --start-options "-config api.disablekey=true" \
      --spider -r http://localhost:8000/api \
      -o "$OUTPUT_DIR/zap-$DATE_SUFFIX.json"
    echo "API security scanning completed."
  else
    echo "Warning: API is not running, skipping OWASP ZAP scan."
  fi
fi

# IAM policy analysis with cloudsplaining (AWS)
if check_tool cloudsplaining && check_tool aws; then
  echo "===== Analyzing AWS IAM Policies with Cloudsplaining ====="
  
  # Check if AWS credentials are configured
  if aws sts get-caller-identity &> /dev/null; then
    mkdir -p "$OUTPUT_DIR/cloudsplaining"
    aws iam get-account-authorization-details > "$OUTPUT_DIR/cloudsplaining/iam-data.json"
    cloudsplaining scan --input-file "$OUTPUT_DIR/cloudsplaining/iam-data.json" --output "$OUTPUT_DIR/cloudsplaining"
    echo "AWS IAM policy analysis completed."
  else
    echo "Warning: AWS credentials not configured, skipping IAM policy analysis."
  fi
fi

echo "===== Security Scan Summary ====="
echo "Total scan reports generated: $(find "$OUTPUT_DIR" -name "*-$DATE_SUFFIX.json" | wc -l)"

if [ $missing_tools -eq 1 ]; then
  echo "Warning: Some security tools were not installed. Install missing tools for more comprehensive scanning."
fi

echo "Security scan completed. Results saved to: $OUTPUT_DIR"
echo "Review the reports for security issues that need to be addressed."