# ============================================================
# outputs.tf — Valores de salida de Terraform
#
# 🧒 PARA NIÑOS:
# Cuando Terraform termina de construir todo, nos da un
# resumen de lo que creó, como cuando un constructor
# te entrega las llaves y te dice la dirección de tu casa.
#
# 📘 TÉCNICO:
# Los outputs pueden usarse en otros módulos o consumirse
# con `terraform output -json` en scripts de CI/CD.
# ============================================================

output "namespace" {
  description = "Namespace de Kubernetes donde se desplegaron los recursos"
  value       = module.networking.namespace_name
}

output "inference_api_service" {
  description = "Nombre del Service de Kubernetes para la Inference API"
  value       = module.kubernetes.inference_api_service_name
}

output "environment" {
  description = "Entorno de despliegue actual"
  value       = var.environment
}
