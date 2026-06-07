variable "resource_group_name" {
  default = "caged-pipeline-rg"
}

variable "location" {
  default = "brazilsouth"
}

variable "storage_account_name" {
  default = "cagedatalake2026"
}

variable "key_vault_name" {
  default = "caged-kv-2026"
}

variable "data_factory_name" {
  default = "caged-adf"
}

variable "synapse_workspace_name" {
  default = "caged-synapse"
}

variable "synapse_admin_login" {
  default = "adminsynapse"
}

variable "synapse_admin_password" {
  default = "CagedPipeline2026!"
}
