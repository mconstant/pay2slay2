variable "akash_chain_id" { type = string }
variable "akash_node" { type = string }
variable "akash_account_address" { type = string }
variable "image_repo" { type = string }
variable "image_tag" { type = string }
variable "deployment_price_uact" {
  type    = number
  default = 1000
}
variable "deployment_price_uakt" {
  type    = number
  default = null
}
