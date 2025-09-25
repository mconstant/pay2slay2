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

# Services list exposed by the Akash provider.  Structure example:
# [
#   {
#     available = 1
#     available_replicas = 1
#     name = "api"
#     ready_replicas = 1
#     replicas = 1
#     total = 1
#     updated_replicas = 1
#     uris = ["example-url"]
#     ips = [
#       {
#         ip = "x.x.x.x"
#         port = 80
#         proto = "TCP"
#         external_port = 12345
#       }
#     ]
#     forwarded_ports = [
#       {
#         host = "host-url"
#         port = 80
#         proto = "TCP"
#         external_port = 12345
#       }
#     ]
#   }
# ]
output "services" {
  description = "List of services created by the Akash deployment (replicas, uris, ips, forwarded_ports)."
  value       = akash_deployment.p2s.services
}
