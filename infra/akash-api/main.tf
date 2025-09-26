provider "akash" {
  chain_id         = var.akash_chain_id
  node             = var.akash_node
  account_address  = var.akash_account_address
}

locals {
  image = "${var.image_repo}:${var.image_tag}"
}

resource "akash_deployment" "api" {
  sdl = <<-EOT
    version: "2.0"
    services:
      api:
        image: ${local.image}
        env:
          - BANANO_RPC_ENDPOINT=${var.banano_rpc_endpoint}
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
              units: 1.0
            memory:
              size: 1Gi
            storage:
              size: 4Gi
      placement:
        westcoast:
          pricing:
            api:
              denom: uakt
              amount: var.deployment_price_uakt
    deployment:
      api:
        westcoast:
          profile: api
          count: 1
  EOT
}

output "deployment_id" { value = akash_deployment.api.id }
