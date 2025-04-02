output "function_app_name" {
  description = "Name of the Azure Function App"
  value       = azurerm_function_app.backend.name
}

output "function_app_url" {
  description = "URL of the Azure Function App"
  value       = azurerm_function_app.backend.default_hostname
}

output "app_service_plan_id" {
  description = "ID of the App Service Plan"
  value       = azurerm_app_service_plan.main.id
}

output "resource_group_name" {
  description = "Name of the Azure Resource Group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the Storage Account"
  value       = azurerm_storage_account.main.name
}

output "key_vault_name" {
  description = "Name of the Azure Key Vault"
  value       = azurerm_key_vault.main.name
}

output "app_insights_instrumentation_key" {
  description = "Instrumentation Key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "static_website_url" {
  description = "URL of the static website hosting the frontend"
  value       = azurerm_storage_account.frontend.primary_web_host
}