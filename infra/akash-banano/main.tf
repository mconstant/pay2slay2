provider "akash" {
  chain_id         = var.akash_chain_id
  node             = var.akash_node
  account_address  = var.akash_account_address
}

locals {
  image = "xmconstantx/configurable-bananode:stable"
}

resource "akash_deployment" "banano" {
  sdl = <<-EOT
    version: "2.0"
    services:
      banano:
        image: ${local.image}
        env:
          - CONFIG_NODE_WEBSOCKET_ENABLE=true
          - CONFIG_NODE_RPC_ENABLE=true
          - CONFIG_SNAPSHOT_URL=https://ledgerfiles.moonano.net/files/rocksdb-2025-09-13.tar.gz
          - CONFIG_RPC_ENABLE_CONTROL=false
          - CONFIG_NODE_ROCKSDB_ENABLE=true
        expose:
          - port: 7071
            as: 7071
            to:
              - global: true
          - port: 7072
            as: 7072
            to:
              - global: true
          - port: 7074
            as: 7074
            to:
              - global: true
    profiles:
      compute:
        banano-profile:
          resources:
            cpu:
              units: 2.0
            memory:
              size: 2Gi
            storage:
              size: 32Gi
      placement:
        westcoast:
          pricing:
            banano-profile:
              denom: uakt
              amount: var.deployment_price_uakt
    deployment:
      banano:
        westcoast:
          profile: banano-profile
          count: 1
  EOT
}

output "deployment_id" { value = akash_deployment.banano.id }
