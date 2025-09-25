###############################################
# Outputs for Akash Deployment
###############################################

output "deployment_id" {
  description = "Akash deployment ID"
  value       = akash_deployment.p2s.id
}

output "image" {
  description = "Deployed container image reference"
  value       = local.image
}
