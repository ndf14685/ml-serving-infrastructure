# ============================================================
# modules/kubernetes/main.tf — Deployments, Services y HPA
#
# 🧒 PARA NIÑOS:
# Este módulo es como el gerente de la ciudad digital.
# Se encarga de arrancar todos los servicios, asegurarse
# de que siempre haya suficientes copias corriendo, y que
# cada servicio tenga los recursos que necesita.
#
# 📘 TÉCNICO:
# Crea Deployments, Services y HPA para los 3 microservicios.
# El Secret de la API Key se crea de forma segura con sensitive.
# ============================================================

variable "namespace" { type = string }
variable "environment" { type = string }
variable "registry" { type = string }
variable "image_tag" { type = string }
variable "api_key" {
  type      = string
  sensitive = true
}

locals {
  common_labels = {
    "app.kubernetes.io/managed-by" = "terraform"
    "environment"                  = var.environment
  }
}

# ── Secret: API Key (valor sensible, no en outputs) ─────────
resource "kubernetes_secret" "api_key" {
  metadata {
    name      = "ml-api-secrets"
    namespace = var.namespace
    labels    = local.common_labels
  }

  data = {
    # base64 encoding es manejado automáticamente por Terraform
    "api-key" = var.api_key
  }

  type = "Opaque"
}

# ── ConfigMap: Configuración no sensible ────────────────────
resource "kubernetes_config_map" "ml_config" {
  metadata {
    name      = "ml-serving-config"
    namespace = var.namespace
    labels    = local.common_labels
  }

  data = {
    "ENVIRONMENT"               = var.environment
    "LOG_LEVEL"                 = var.environment == "production" ? "INFO" : "DEBUG"
    "MODEL_VERSION"             = "1.0.0"
    "MODEL_PATH"                = "/app/models/iris_model.pkl"
    "PREPROCESSING_SERVICE_URL" = "http://preprocessing-service:8001"
    "MODEL_MANAGER_URL"         = "http://model-manager:8002"
  }
}

# ── Deployment: Inference API ────────────────────────────────
resource "kubernetes_deployment" "inference_api" {
  metadata {
    name      = "inference-api"
    namespace = var.namespace
    labels    = merge(local.common_labels, { "app" = "inference-api" })
  }

  spec {
    replicas = 2

    selector {
      match_labels = { "app" = "inference-api" }
    }

    # PodDisruptionBudget asegura mínimo 1 pod durante rolling updates
    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = "1"
        max_surge       = "1"
      }
    }

    template {
      metadata {
        labels = merge(local.common_labels, { "app" = "inference-api" })
        annotations = {
          # Fuerza re-deploy si el configmap cambia
          "checksum/config" = sha256(jsonencode(kubernetes_config_map.ml_config.data))
        }
      }

      spec {
        # SEGURIDAD: No montar tokens de service account si no se necesitan
        automount_service_account_token = false

        container {
          name  = "inference-api"
          image = "${var.registry}/inference-api:${var.image_tag}"

          # SEGURIDAD: Contexto de seguridad del contenedor
          security_context {
            run_as_non_root            = true
            run_as_user                = 1001
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities {
              drop = ["ALL"]
            }
          }

          # Variables de entorno desde ConfigMap
          env_from {
            config_map_ref { name = kubernetes_config_map.ml_config.metadata[0].name }
          }

          # Variable sensible desde Secret
          env {
            name = "API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api_key.metadata[0].name
                key  = "api-key"
              }
            }
          }

          # Recursos: requests (garantizados) y limits (máximo)
          resources {
            requests = { cpu = "100m", memory = "256Mi" }
            limits   = { cpu = "500m", memory = "512Mi" }
          }

          # Liveness probe: ¿está el proceso vivo?
          liveness_probe {
            http_get { path = "/health"; port = 8000 }
            initial_delay_seconds = 30
            period_seconds        = 10
            failure_threshold     = 3
          }

          # Readiness probe: ¿puede recibir tráfico?
          readiness_probe {
            http_get { path = "/ready"; port = 8000 }
            initial_delay_seconds = 20
            period_seconds        = 5
            failure_threshold     = 3
          }

          port { container_port = 8000 }
        }
      }
    }
  }
}

# ── Service: Inference API ────────────────────────────────────
resource "kubernetes_service" "inference_api" {
  metadata {
    name      = "inference-api"
    namespace = var.namespace
    labels    = merge(local.common_labels, { "app" = "inference-api" })
  }

  spec {
    selector = { "app" = "inference-api" }
    type     = "ClusterIP"
    port {
      port        = 8000
      target_port = 8000
      protocol    = "TCP"
    }
  }
}

# ── HPA: Inference API (autoescalado) ────────────────────────
resource "kubernetes_horizontal_pod_autoscaler_v2" "inference_api" {
  metadata {
    name      = "inference-api-hpa"
    namespace = var.namespace
  }

  spec {
    min_replicas = 2
    max_replicas = 6

    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.inference_api.metadata[0].name
    }

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }
  }
}

# ── Deployment: Preprocessing Service ───────────────────────
resource "kubernetes_deployment" "preprocessing" {
  metadata {
    name      = "preprocessing-service"
    namespace = var.namespace
    labels    = merge(local.common_labels, { "app" = "preprocessing-service" })
  }

  spec {
    replicas = 2

    selector {
      match_labels = { "app" = "preprocessing-service" }
    }

    template {
      metadata {
        labels = merge(local.common_labels, { "app" = "preprocessing-service" })
      }

      spec {
        automount_service_account_token = false

        container {
          name  = "preprocessing-service"
          image = "${var.registry}/preprocessing-service:${var.image_tag}"

          security_context {
            run_as_non_root            = true
            run_as_user                = 1001
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities { drop = ["ALL"] }
          }

          env_from {
            config_map_ref { name = kubernetes_config_map.ml_config.metadata[0].name }
          }

          resources {
            requests = { cpu = "50m", memory = "128Mi" }
            limits   = { cpu = "250m", memory = "256Mi" }
          }

          liveness_probe {
            http_get { path = "/health"; port = 8001 }
            initial_delay_seconds = 20
            period_seconds        = 10
          }

          readiness_probe {
            http_get { path = "/health"; port = 8001 }
            initial_delay_seconds = 10
            period_seconds        = 5
          }

          port { container_port = 8001 }
        }
      }
    }
  }
}

resource "kubernetes_service" "preprocessing" {
  metadata {
    name      = "preprocessing-service"
    namespace = var.namespace
    labels    = merge(local.common_labels, { "app" = "preprocessing-service" })
  }

  spec {
    selector = { "app" = "preprocessing-service" }
    type     = "ClusterIP"
    port { port = 8001; target_port = 8001 }
  }
}

# ── Deployment: Model Manager ────────────────────────────────
resource "kubernetes_deployment" "model_manager" {
  metadata {
    name      = "model-manager"
    namespace = var.namespace
    labels    = merge(local.common_labels, { "app" = "model-manager" })
  }

  spec {
    replicas = 1  # Singleton para gestión consistente del modelo

    selector {
      match_labels = { "app" = "model-manager" }
    }

    template {
      metadata {
        labels = merge(local.common_labels, { "app" = "model-manager" })
      }

      spec {
        automount_service_account_token = false

        container {
          name  = "model-manager"
          image = "${var.registry}/model-manager:${var.image_tag}"

          security_context {
            run_as_non_root            = true
            run_as_user                = 1001
            allow_privilege_escalation = false
            capabilities { drop = ["ALL"] }
          }

          env_from {
            config_map_ref { name = kubernetes_config_map.ml_config.metadata[0].name }
          }

          resources {
            requests = { cpu = "100m", memory = "256Mi" }
            limits   = { cpu = "500m", memory = "1Gi" }
          }

          liveness_probe {
            http_get { path = "/health"; port = 8002 }
            initial_delay_seconds = 60
            period_seconds        = 15
          }

          readiness_probe {
            http_get { path = "/ready"; port = 8002 }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          port { container_port = 8002 }

          # Volumen para persistir el modelo
          volume_mount {
            name       = "model-storage"
            mount_path = "/app/models"
          }
        }

        volume {
          name = "model-storage"
          persistent_volume_claim {
            claim_name = "model-pvc"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "model_manager" {
  metadata {
    name      = "model-manager"
    namespace = var.namespace
    labels    = merge(local.common_labels, { "app" = "model-manager" })
  }

  spec {
    selector = { "app" = "model-manager" }
    type     = "ClusterIP"
    port { port = 8002; target_port = 8002 }
  }
}

# ── PersistentVolumeClaim para el modelo ─────────────────────
resource "kubernetes_persistent_volume_claim" "model_pvc" {
  metadata {
    name      = "model-pvc"
    namespace = var.namespace
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = { storage = "1Gi" }
    }
  }
}

output "inference_api_service_name" {
  value = kubernetes_service.inference_api.metadata[0].name
}
