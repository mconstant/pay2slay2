###############################################
# Akash Deployment Terraform Configuration
# Core logic (variables in vars.tf)
###############################################

provider "akash" {
  chain_id = var.akash_chain_id
  node     = var.akash_node

  keyring {
    backend  = "test" # For CI automation; consider 'os' or 'file' for prod/hardware
    mnemonic = var.akash_mnemonic
  }

  gas_adjustment = var.gas_adjustment
  gas_prices {
    denom  = "uakt"
    amount = var.gas_price_uakt
  }
}

locals {
  # Fully qualified image reference (e.g. ghcr.io/OWNER/REPO:TAG)
  image = "${var.image_repo}:${var.image_tag}"
}

# Placeholder: Define a basic SDL rendered as part of a deployment
resource "akash_deployment" "p2s" {
  sdl = <<-EOT
    version: "2.0"
    services:
      api:
        image: ${local.image}
        expose:
          - port: 8000
            as: 80
            to:
              - global: true
    profiles:
      compute:
        api:
          resources:
            cpu:
              units: ${var.cpu_units}
            memory:
              size: ${var.memory_size}
            storage:
              size: ${var.storage_size}
      placement:
        westcoast:
          pricing:
            api:
              denom: uakt
              amount: ${var.deployment_price_uakt}
    deployment:
      api:
        westcoast:
          profile: api
          count: 1
  EOT
}

