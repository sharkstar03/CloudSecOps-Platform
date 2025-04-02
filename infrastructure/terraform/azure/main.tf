provider "azurerm" {
  features {}
}

# Get current client config for Key Vault
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "cloudsecops" {
  name     = "${var.project_name}-${var.environment}"
  location = var.location

  tags = merge(var.tags, {
    Name        = "${var.project_name}-resource-group"
    Environment = var.environment
  })
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_name}-vnet"
  address_space       = [var.vnet_cidr]
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name

  tags = merge(var.tags, {
    Name        = "${var.project_name}-vnet"
    Environment = var.environment
  })
}

# Subnets
resource "azurerm_subnet" "public" {
  name                 = "${var.project_name}-public-subnet"
  resource_group_name  = azurerm_resource_group.cloudsecops.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.public_subnet_cidr]
}

resource "azurerm_subnet" "private" {
  name                 = "${var.project_name}-private-subnet"
  resource_group_name  = azurerm_resource_group.cloudsecops.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.private_subnet_cidr]
  service_endpoints    = ["Microsoft.Sql", "Microsoft.Storage", "Microsoft.KeyVault"]
}

# Network Security Group for App Service
resource "azurerm_network_security_group" "app" {
  name                = "${var.project_name}-app-nsg"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name

  security_rule {
    name                       = "allow-http"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-https"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-app-nsg"
    Environment = var.environment
  })
}

# Network Security Group for Database
resource "azurerm_network_security_group" "db" {
  name                = "${var.project_name}-db-nsg"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name

  security_rule {
    name                       = "allow-postgresql"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = var.public_subnet_cidr
    destination_address_prefix = "*"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-db-nsg"
    Environment = var.environment
  })
}

# Associate NSGs with Subnets
resource "azurerm_subnet_network_security_group_association" "public" {
  subnet_id                 = azurerm_subnet.public.id
  network_security_group_id = azurerm_network_security_group.app.id
}

resource "azurerm_subnet_network_security_group_association" "private" {
  subnet_id                 = azurerm_subnet.private.id
  network_security_group_id = azurerm_network_security_group.db.id
}

# Storage Account for logs and assets
resource "azurerm_storage_account" "main" {
  name                     = "${var.project_name}${var.environment}sa"
  resource_group_name      = azurerm_resource_group.cloudsecops.name
  location                 = azurerm_resource_group.cloudsecops.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  min_tls_version          = "TLS1_2"
  
  blob_properties {
    delete_retention_policy {
      days = 7
    }
  }

  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.private.id]
    ip_rules                   = var.allowed_ips
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-storage"
    Environment = var.environment
  })
}

# Container registry for Docker images
resource "azurerm_container_registry" "acr" {
  name                = "${var.project_name}${var.environment}acr"
  resource_group_name = azurerm_resource_group.cloudsecops.name
  location            = azurerm_resource_group.cloudsecops.location
  sku                 = "Standard"
  admin_enabled       = true

  tags = merge(var.tags, {
    Name        = "${var.project_name}-acr"
    Environment = var.environment
  })
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.project_name}-db-${var.environment}"
  resource_group_name    = azurerm_resource_group.cloudsecops.name
  location               = azurerm_resource_group.cloudsecops.location
  version                = "14"
  delegated_subnet_id    = azurerm_subnet.private.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  administrator_login    = var.db_username
  administrator_password = var.db_password
  zone                   = "1"
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
  backup_retention_days  = 7

  high_availability {
    mode = var.environment == "production" ? "ZoneRedundant" : "Disabled"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
  })
}

# Private DNS Zone for PostgreSQL
resource "azurerm_private_dns_zone" "postgres" {
  name                = "cloudsecops.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.cloudsecops.name

  tags = merge(var.tags, {
    Name        = "${var.project_name}-postgres-dns"
    Environment = var.environment
  })
}

# Link Private DNS Zone to VNet
resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.project_name}-postgres-dns-link"
  resource_group_name   = azurerm_resource_group.cloudsecops.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "${var.project_name}-appservice-plan"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name
  os_type             = "Linux"
  sku_name            = "B1"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-app-service-plan"
    Environment = var.environment
  })
}

# App Service for API
resource "azurerm_linux_web_app" "api" {
  name                = "${var.project_name}-api-${var.environment}"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  site_config {
    container_registry_use_managed_identity = true
    application_stack {
      docker_image     = "${azurerm_container_registry.acr.login_server}/cloudsecops/api:latest"
      docker_image_tag = "latest"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_REGISTRY_SERVER_URL"          = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME"     = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"     = azurerm_container_registry.acr.admin_password
    "DATABASE_URL"                        = "postgresql://${var.db_username}:${var.db_password}@${azurerm_postgresql_flexible_server.main.fqdn}/cloudsecops"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-api"
    Environment = var.environment
  })
}

# App Service for Frontend
resource "azurerm_linux_web_app" "frontend" {
  name                = "${var.project_name}-frontend-${var.environment}"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  site_config {
    container_registry_use_managed_identity = true
    application_stack {
      docker_image     = "${azurerm_container_registry.acr.login_server}/cloudsecops/frontend:latest"
      docker_image_tag = "latest"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_REGISTRY_SERVER_URL"          = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME"     = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"     = azurerm_container_registry.acr.admin_password
    "REACT_APP_API_URL"                   = "https://${azurerm_linux_web_app.api.default_hostname}/api"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-frontend"
    Environment = var.environment
  })
}

# Key Vault for Secrets
resource "azurerm_key_vault" "main" {
  name                        = "${var.project_name}-${var.environment}-kv"
  location                    = azurerm_resource_group.cloudsecops.location
  resource_group_name         = azurerm_resource_group.cloudsecops.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update",
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete",
    ]
  }

  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    virtual_network_subnet_ids = [azurerm_subnet.private.id]
    ip_rules                   = var.allowed_ips
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-key-vault"
    Environment = var.environment
  })
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-logs"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = merge(var.tags, {
    Name        = "${var.project_name}-logs"
    Environment = var.environment
  })
}

# Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-${var.environment}-appinsights"
  location            = azurerm_resource_group.cloudsecops.location
  resource_group_name = azurerm_resource_group.cloudsecops.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-appinsights"
    Environment = var.environment
  })
}

# Azure Monitor Action Group for alerts
resource "azurerm_monitor_action_group" "critical" {
  name                = "${var.project_name}-${var.environment}-critical-alerts"
  resource_group_name = azurerm_resource_group.cloudsecops.name
  short_name          = "critical"

  email_receiver {
    name                    = "security-team"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  webhook_receiver {
    name        = "slack"
    service_uri = var.slack_webhook_url
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-alerts"
    Environment = var.environment
  })
}

# Security Center
resource "azurerm_security_center_subscription_pricing" "main" {
  tier          = "Standard"
  resource_type = "VirtualMachines"
}

resource "azurerm_security_center_contact" "main" {
  email = var.alert_email
  phone = var.alert_phone

  alert_notifications = true
  alerts_to_admins    = true
}

# Enable auto provisioning of Log Analytics agent
resource "azurerm_security_center_auto_provisioning" "main" {
  auto_provision = "On"
}

# Enable Security Center Standard for Container Registries
resource "azurerm_security_center_subscription_pricing" "container_registries" {
  tier          = "Standard"
  resource_type = "ContainerRegistry"
}

# Enable Security Center Standard for Key Vaults
resource "azurerm_security_center_subscription_pricing" "key_vaults" {
  tier          = "Standard"
  resource_type = "KeyVaults"
}

# Enable Security Center Standard for Storage
resource "azurerm_security_center_subscription_pricing" "storage" {
  tier          = "Standard"
  resource_type = "StorageAccounts"
}

# Enable Security Center Standard for App Services
resource "azurerm_security_center_subscription_pricing" "app_services" {
  tier          = "Standard"
  resource_type = "AppServices"
}

# Assign API App Service identity to ACR pull role
resource "azurerm_role_assignment" "api_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.api.identity[0].principal_id
}

# Assign Frontend App Service identity to ACR pull role
resource "azurerm_role_assignment" "frontend_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.frontend.identity[0].principal_id
}

# User Assigned Managed Identity for security scanning
resource "azurerm_user_assigned_identity" "scanner" {
  name                = "${var.project_name}-${var.environment}-scanner-identity"
  resource_group_name = azurerm_resource_group.cloudsecops.name
  location            = azurerm_resource_group.cloudsecops.location

  tags = merge(var.tags, {
    Name        = "${var.project_name}-scanner-identity"
    Environment = var.environment
  })
}

# Assign Reader role to the scanner identity for subscription
resource "azurerm_role_assignment" "scanner_reader" {
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.scanner.principal_id
}

# Assign Security Reader role to the scanner identity
resource "azurerm_role_assignment" "scanner_security_reader" {
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"
  role_definition_name = "Security Reader"
  principal_id         = azurerm_user_assigned_identity.scanner.principal_id
}

# Azure Function App for scheduled scans
resource "azurerm_storage_account" "functions" {
  name                     = "${var.project_name}${var.environment}func"
  resource_group_name      = azurerm_resource_group.cloudsecops.name
  location                 = azurerm_resource_group.cloudsecops.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-functions-storage"
    Environment = var.environment
  })
}

resource "azurerm_service_plan" "functions" {
  name                = "${var.project_name}-${var.environment}-func-plan"
  resource_group_name = azurerm_resource_group.cloudsecops.name
  location            = azurerm_resource_group.cloudsecops.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption plan

  tags = merge(var.tags, {
    Name        = "${var.project_name}-functions-plan"
    Environment = var.environment
  })
}

resource "azurerm_linux_function_app" "scanner" {
  name                       = "${var.project_name}-${var.environment}-scanner-func"
  resource_group_name        = azurerm_resource_group.cloudsecops.name
  location                   = azurerm_resource_group.cloudsecops.location
  service_plan_id            = azurerm_service_plan.functions.id
  storage_account_name       = azurerm_storage_account.functions.name
  storage_account_access_key = azurerm_storage_account.functions.primary_access_key

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.scanner.id]
  }

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"         = "python"
    "APPINSIGHTS_INSTRUMENTATIONKEY"   = azurerm_application_insights.main.instrumentation_key
    "API_URL"                          = "https://${azurerm_linux_web_app.api.default_hostname}/api"
    "SUBSCRIPTION_ID"                  = data.azurerm_client_config.current.subscription_id
    "MANAGED_IDENTITY_CLIENT_ID"       = azurerm_user_assigned_identity.scanner.client_id
    "AZURE_STORAGE_ACCOUNT"            = azurerm_storage_account.main.name
    "DATABASE_URL"                     = "postgresql://${var.db_username}:${var.db_password}@${azurerm_postgresql_flexible_server.main.fqdn}/cloudsecops"
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}-scanner-function"
    Environment = var.environment
  })
}

# Outputs
output "api_hostname" {
  value       = azurerm_linux_web_app.api.default_hostname
  description = "The hostname of the API app service"
}

output "frontend_hostname" {
  value       = azurerm_linux_web_app.frontend.default_hostname
  description = "The hostname of the frontend app service"
}

output "postgres_server_fqdn" {
  value       = azurerm_postgresql_flexible_server.main.fqdn
  description = "The FQDN of the PostgreSQL server"
}

output "acr_login_server" {
  value       = azurerm_container_registry.acr.login_server
  description = "The login server URL for the container registry"
}

output "scanner_identity_client_id" {
  value       = azurerm_user_assigned_identity.scanner.client_id
  description = "The client ID of the scanner identity"
}

output "storage_account_name" {
  value       = azurerm_storage_account.main.name
  description = "The name of the storage account"
}