###############################################
# Akash Deployment Terraform Configuration
# Core logic (variables in vars.tf)
###############################################

provider "akash" {
  chain_id = var.akash_chain_id
  node     = var.akash_node
  account_address = var.akash_account_address
  # NOTE: Provider v0.1.0 error shows keyring/gas blocks unsupported; mnemonic attribute also unsupported.
  # Authentication must be handled via environment or future provider updates. Leaving mnemonic commented.
  # mnemonic = var.akash_mnemonic
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
        env:
          - SESSION_SECRET=${var.session_secret}
          - P2S_DRY_RUN=${var.p2s_dry_run}
          - DEMO_MODE=${var.demo_mode}
          - DISCORD_CLIENT_ID=${var.discord_client_id}
          - DISCORD_CLIENT_SECRET=${var.discord_client_secret}
          - DISCORD_REDIRECT_URI=${var.discord_redirect_uri}
          - YUNITE_API_KEY=${var.yunite_api_key}
          - YUNITE_GUILD_ID=${var.yunite_guild_id}
          - YUNITE_BASE_URL=${var.yunite_base_url}
          - FORTNITE_API_KEY=${var.fortnite_api_key}
          - FORTNITE_BASE_URL=${var.fortnite_base_url}
          - BANANO_NODE_RPC=${var.banano_node_rpc}
          - DATABASE_URL=sqlite:///pay2slay.db
          - PAY2SLAY_AUTO_MIGRATE=1
        expose:
          - port: 8000
            as: 80
            accept:
              - ${var.domain_name}
            to:
              - global: true
      banano:
        image: xmconstantx/configurable-bananode:stable
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
        api:
          resources:
            cpu:
              units: ${var.cpu_units}
            memory:
              size: ${var.memory_size}
            storage:
              size: ${var.storage_size}
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
          attributes:
            audited: true
          signedBy:
            anyOf:
              - "akash1365yvmc4s7awdyj3n2sav7xfx76adc6dnmlx63"
              - "akash18qa2a2ltfyvkyj0ggj3hkvuj6twzyumuaru9s4"
          pricing:
            api:
              denom: uakt
              amount: ${var.deployment_price_uakt}
            banano-profile:
              denom: uakt
              amount: 1000
    deployment:
      api:
        westcoast:
          profile: api
          count: 1
      banano:
        westcoast:
          profile: banano-profile
          count: 1
  EOT
}

