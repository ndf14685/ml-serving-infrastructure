# ============================================================
# modules/networking/main.tf — Namespace y políticas de red
#
# 🧒 PARA NIÑOS:
# En una ciudad, cada barrio tiene su nombre y sus reglas.
# Este módulo crea el "barrio" (namespace) donde vivirán
# nuestros servicios y pone las reglas de quién puede
# hablar con quién.
#
# 📘 TÉCNICO:
# Crea el namespace de Kubernetes con ResourceQuota y
# LimitRange para controlar el consumo de recursos.
# ============================================================

variable "namespace" { type = string }
variable "environment" { type = string }

# ── Namespace ───────────────────────────────────────────────
resource "kubernetes_namespace" "ml_serving" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "environment"                  = var.environment
      "project"                      = "ml-serving-infrastructure"
    }
    annotations = {
      "description" = "Namespace para el ML Serving Infrastructure"
    }
  }
}

# ── ResourceQuota: límite total del namespace ───────────────
resource "kubernetes_resource_quota" "ml_serving" {
  metadata {
    name      = "ml-serving-quota"
    namespace = kubernetes_namespace.ml_serving.metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"    = "4"
      "requests.memory" = "4Gi"
      "limits.cpu"      = "8"
      "limits.memory"   = "8Gi"
      "pods"            = "20"
    }
  }
}

# ── LimitRange: límites por contenedor ──────────────────────
resource "kubernetes_limit_range" "ml_serving" {
  metadata {
    name      = "ml-serving-limits"
    namespace = kubernetes_namespace.ml_serving.metadata[0].name
  }

  spec {
    limit {
      type = "Container"
      default = {
        cpu    = "500m"
        memory = "512Mi"
      }
      default_request = {
        cpu    = "100m"
        memory = "128Mi"
      }
      max = {
        cpu    = "2"
        memory = "2Gi"
      }
    }
  }
}

output "namespace_name" {
  value = kubernetes_namespace.ml_serving.metadata[0].name
}
