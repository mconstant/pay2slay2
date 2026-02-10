###############################################
# Variables for Akash Deployment
###############################################

variable "akash_mnemonic" {
  type        = string
  description = "24-word mnemonic for the Akash account (injected via TF_VAR_akash_mnemonic)."
}

variable "akash_node" {
  type        = string
  description = "RPC endpoint (node) for Akash network (e.g. https://rpc.akash.network:443)."
}

variable "akash_chain_id" {
  type        = string
  description = "Akash chain ID (mainnet: akashnet-2)."
  default     = "akashnet-2"
}

variable "image_tag" {
  type        = string
  description = "Container image tag to deploy."
}

variable "image_repo" {
  type        = string
  description = "Container image repository (e.g. ghcr.io/OWNER/REPO)."
}


variable "deployment_price_uakt" {
  type        = number
  description = "Bid pricing amount (uakt) for the service profile."
  default     = 1000
}

variable "cpu_units" {
  type        = string
  description = "CPU units for the compute profile."
  default     = "0.1"
}

variable "memory_size" {
  type        = string
  description = "Memory allocation (e.g. 256Mi)."
  default     = "256Mi"
}

variable "storage_size" {
  type        = string
  description = "Storage allocation (e.g. 1Gi)."
  default     = "1Gi"
}

variable "akash_account_address" {
  type        = string
  description = "Akash account address (injected via TF_VAR_akash_account_address)."
}

# --- Application secrets & config ---

variable "domain_name" {
  type        = string
  description = "Domain name for the API service (routed via Akash ingress)."
}

variable "session_secret" {
  type        = string
  description = "HMAC secret for sessions & OAuth state."
  sensitive   = true
}

variable "p2s_dry_run" {
  type        = string
  description = "Whether to run in dry-run mode (true/false)."
  default     = "false"
}

variable "demo_mode" {
  type        = string
  description = "Enable demo endpoints (1/0)."
  default     = "0"
}

variable "discord_client_id" {
  type        = string
  description = "Discord OAuth application client ID."
}

variable "discord_client_secret" {
  type        = string
  description = "Discord OAuth application client secret."
  sensitive   = true
}

variable "discord_redirect_uri" {
  type        = string
  description = "Discord OAuth redirect URI (must match Discord app settings)."
  sensitive   = true
}

variable "yunite_api_key" {
  type        = string
  description = "Yunite API key for Epic account resolution."
  sensitive   = true
}

variable "yunite_guild_id" {
  type        = string
  description = "Discord guild ID for Yunite lookups."
}

variable "yunite_base_url" {
  type        = string
  description = "Yunite API base URL."
  default     = "https://yunite.xyz/api"
}

variable "fortnite_api_key" {
  type        = string
  description = "Fortnite stats API key."
  sensitive   = true
}

variable "fortnite_base_url" {
  type        = string
  description = "Fortnite stats API base URL."
  default     = "https://fortnite-api.com/v2"
}

variable "banano_node_rpc" {
  type        = string
  description = "Banano node RPC endpoint."
}
