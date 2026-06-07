terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "caged" {
  name     = var.resource_group_name
  location = var.location
}

# Storage Account com ADLS Gen2
resource "azurerm_storage_account" "datalake" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.caged.name
  location                 = azurerm_resource_group.caged.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true
}

# Containers — camadas do Data Lake
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

# Key Vault
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "caged" {
  name                = var.key_vault_name
  location            = azurerm_resource_group.caged.location
  resource_group_name = azurerm_resource_group.caged.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    secret_permissions = ["Get", "Set", "List", "Delete", "Purge"]
  }
}

# Guarda connection string no Key Vault
resource "azurerm_key_vault_secret" "storage_key" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.datalake.primary_connection_string
  key_vault_id = azurerm_key_vault.caged.id
}

# Azure Data Factory
resource "azurerm_data_factory" "caged" {
  name                = var.data_factory_name
  location            = azurerm_resource_group.caged.location
  resource_group_name = azurerm_resource_group.caged.name
  identity {
    type = "SystemAssigned"
  }
}

# Azure Synapse Analytics Workspace
resource "azurerm_synapse_workspace" "caged" {
  name                                 = var.synapse_workspace_name
  resource_group_name                  = azurerm_resource_group.caged.name
  location                             = azurerm_resource_group.caged.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.synapse.id
  sql_administrator_login              = var.synapse_admin_login
  sql_administrator_login_password     = var.synapse_admin_password

  identity {
    type = "SystemAssigned"
  }
}

# Filesystem pro Synapse
resource "azurerm_storage_data_lake_gen2_filesystem" "synapse" {
  name               = "synapse"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Synapse SQL Pool — serverless nao precisa de pool dedicado
resource "azurerm_synapse_firewall_rule" "allow_all" {
  name                 = "AllowAll"
  synapse_workspace_id = azurerm_synapse_workspace.caged.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "255.255.255.255"
}
