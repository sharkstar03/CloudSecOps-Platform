variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cloudsecops"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
}

variable "location" {
  description = "Azure region to deploy resources"
  type        = string
  default     = "eastus"
}

variable "vnet_cidr" {
  description = "CIDR block for VNet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "db_username" {
  description = "Username for the PostgreSQL server"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "db_password" {
  description = "Password for the PostgreSQL server"
  type        = string
  sensitive   = true
}

variable "allowed_ips" {
  description = "List of allowed IP addresses for secure resources"
  type        = list(string)
  default     = []
}

variable "alert_email" {
  description = "Email address for security alerts"
  type        = string
  default     = "security@example.com"
}

variable "alert_phone" {
  description = "Phone number for security alerts"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for security alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "CloudSecOps"
    ManagedBy = "Terraform"
    Owner     = "Security Team"
  }
}

variable "enable_security_center" {
  description = "Enable Azure Security Center"
  type        = bool
  default     = true
}

variable "enable_diagnostics" {
  description = "Enable Azure Diagnostics"
  type        = bool
  default     = true
}

variable "scanner_schedule" {
  description = "CRON expression for the security scanner schedule"
  type        = string
  default     = "0 0 * * *" # Daily at midnight
}

variable "retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

variable "api_image" {
  description = "Docker image for the API service"
  type        = string
  default     = "cloudsecops/api:latest"
}

variable "frontend_image" {
  description = "Docker image for the frontend service"
  type        = string
  default     = "cloudsecops/frontend:latest"
}