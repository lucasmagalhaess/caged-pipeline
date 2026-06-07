output "resource_group" {
  value = azurerm_resource_group.caged.name
}

output "storage_account" {
  value = azurerm_storage_account.datalake.name
}

output "key_vault" {
  value = azurerm_key_vault.caged.name
}

output "synapse_workspace" {
  value = azurerm_synapse_workspace.caged.name
}

output "data_factory" {
  value = azurerm_data_factory.caged.name
}
