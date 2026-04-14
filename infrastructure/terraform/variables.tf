# ============================================================
# variables.tf — Variables de configuración de Terraform
#
# 🧒 PARA NIÑOS:
# Las variables son como los parámetros de una receta.
# En vez de tener el número exacto de ingredientes
# escrito en la receta, usamos variables para poder
# cambiar las cantidades fácilmente.
#
# 📘 TÉCNICO:
# Las variables sin default deben pasarse via:
#   - terraform.tfvars (NO commitear al repo)
#   - Variables de entorno TF_VAR_nombre
#   - Flags -var al ejecutar terraform
# ============================================================

variable "namespace" {
  description = "Namespace de Kubernetes donde se despliegan los servicios"
  type        = string
  default     = "ml-serving"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.namespace))
    error_message = "El namespace solo puede contener letras minúsculas, números y guiones."
  }
}

variable "environment" {
  description = "Entorno de despliegue (development | staging | production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "El entorno debe ser: development, staging o production."
  }
}

variable "registry" {
  description = "Registry de imágenes Docker (ej: ghcr.io/tu-usuario)"
  type        = string
  default     = "ghcr.io/ndf14685"
}

variable "image_tag" {
  description = "Tag de las imágenes Docker a desplegar"
  type        = string
  default     = "latest"
}

variable "api_key" {
  description = "API Key para autenticar requests a la Inference API"
  type        = string
  sensitive   = true  # Terraform no la muestra en outputs ni logs
}

variable "kubeconfig_path" {
  description = "Ruta al archivo kubeconfig para conectar con el cluster"
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Contexto de Kubernetes a usar (ej: minikube)"
  type        = string
  default     = "minikube"
}

# ── Configuración de recursos por servicio ───────────────────

variable "inference_api_replicas" {
  description = "Número de réplicas del Inference API"
  type        = number
  default     = 2

  validation {
    condition     = var.inference_api_replicas >= 1 && var.inference_api_replicas <= 10
    error_message = "Las réplicas deben estar entre 1 y 10."
  }
}

variable "preprocessing_replicas" {
  description = "Número de réplicas del Preprocessing Service"
  type        = number
  default     = 2
}

variable "model_manager_replicas" {
  description = "Número de réplicas del Model Manager"
  type        = number
  default     = 1  # Singleton: gestiona el estado del modelo
}
