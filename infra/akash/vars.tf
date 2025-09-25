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
