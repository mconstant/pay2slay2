plugin "aws" { enabled = false }
plugin "azurerm" { enabled = false }
plugin "google" { enabled = false }

# Core rule configuration (adjust severities as needed)
rule "terraform_standard_module_structure" { enabled = true }
rule "terraform_deprecated_interpolation" { enabled = true }
rule "terraform_naming_convention" { enabled = true }

# Ignore missing provider-specific rules since using Akash custom provider (not covered by built-ins)
