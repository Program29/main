provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "example" {
  name     = "example-resource-group"
  location = "East US"
}

resource "azurerm_storage_account" "example" {
  name                     = "examplestoracc"  # Must be globally unique
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier            = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_key_vault" "example" {
  name                = "example-keyvault"  # Must be globally unique
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name

  sku {
    family = "A"
    name   = "standard"
  }

  tenant_id = data.azurerm_client_config.example.tenant_id
}

resource "azurerm_databricks_workspace" "example" {
  name                = "example-databricks"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  sku                 = "standard"
}

resource "azurerm_data_factory" "example" {
  name                = "exampleadf"  # Must be globally unique
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
}

data "azurerm_client_config" "example" {}

output "storage_account_name" {
  value = azurerm_storage_account.example.name
}

output "key_vault_id" {
  value = azurerm_key_vault.example.id
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.example.workspace_url
}

output "data_factory_id" {
  value = azurerm_data_factory.example.id
}
