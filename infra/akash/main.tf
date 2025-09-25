variable "akash_mnemonic" { type = string }
variable "akash_network" { type = string }
variable "image_tag" { type = string }
variable "image_repo" { type = string }

provider "akash" {
  keyring {
    backend  = "test"
    mnemonic = var.akash_mnemonic
  }
  chain_id   = "akashnet-2"
  node       = var.akash_network
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
              units: 0.1
            memory:
              size: 256Mi
            storage:
              size: 1Gi
      placement:
        westcoast:
          pricing:
            api:
              denom: uakt
              amount: 1000
    deployment:
      api:
        westcoast:
          profile: api
          count: 1
  EOT
}
