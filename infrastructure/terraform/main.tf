# ============================================================
# main.tf — Configuración principal de Terraform
#
# 🧒 PARA NIÑOS:
# Terraform es como el arquitecto de nuestra ciudad digital.
# En vez de construir edificios a mano, le decimos en este
# archivo QUÉ queremos construir, y él lo construye solo.
# Si queremos cambiar algo, cambiamos el archivo y Terraform
# actualiza todo automáticamente.
#
# 📘 TÉCNICO:
# Provisiona el namespace de Kubernetes con sus configuraciones
# de recursos usando el provider de Kubernetes.
# Compatible con Minikube (local) y clusters cloud.
# ============================================================

terraform {
  required_version = ">= 1.8.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.14"
    }
  }

  # Estado local para desarrollo. En producción: backend S3 o GCS
  # backend "s3" {
  #   bucket = "ml-serving-terraform-state"
  #   key    = "terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# ── Provider de Kubernetes ────────────────────────────────────
# Lee la configuración del kubeconfig local (Minikube)
provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path    = var.kubeconfig_path
    config_context = var.kube_context
  }
}

# ── Módulos ────────────────────────────────────────────────────

# Módulo: Networking (namespace + políticas de red)
module "networking" {
  source = "./modules/networking"

  namespace   = var.namespace
  environment = var.environment
}

# Módulo: Kubernetes (deployments + services + HPA)
module "kubernetes" {
  source = "./modules/kubernetes"

  namespace     = var.namespace
  environment   = var.environment
  registry      = var.registry
  image_tag     = var.image_tag
  api_key       = var.api_key

  # Dependencia explícita: el namespace debe existir primero
  depends_on = [module.networking]
}
