# ML Serving Infrastructure

> Infraestructura de producción para servir modelos de Machine Learning — DevOps Take-Home Challenge

[![CI](https://github.com/ndf14685/ml-serving-infrastructure/actions/workflows/ci.yml/badge.svg)](https://github.com/ndf14685/ml-serving-infrastructure/actions)
[![Coverage](https://codecov.io/gh/ndf14685/ml-serving-infrastructure/branch/main/graph/badge.svg)](https://codecov.io/gh/ndf14685/ml-serving-infrastructure)

## Descripción

Este proyecto implementa una infraestructura completa y lista para producción para servir modelos de ML. Incluye 3 microservicios, CI/CD automatizado, infraestructura como código con Terraform, despliegue en Kubernetes y observabilidad con Prometheus + Grafana.

El modelo predice la especie de una flor Iris (setosa, versicolor, virginica) a partir de 4 medidas: largo/ancho del sépalo y largo/ancho del pétalo.

## Arquitectura

```
Cliente HTTP
    │
    ▼
Ingress (nginx)
    │
    ▼
┌─────────────────────────────────────────┐
│           inference-api :8000           │
│  ┌────────────────────────────────────┐ │
│  │  Auth (API Key) → Rate Limit       │ │
│  │  → preprocessing-service :8001    │ │
│  │  → model-manager :8002            │ │
│  │  → sklearn Pipeline → Response    │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
    │
    ▼
Prometheus :9090 → Grafana :3000
```

Para la arquitectura completa ver [ARCHITECTURE.md](./ARCHITECTURE.md).

## Prerequisitos

| Herramienta | Versión | Instalación |
|---|---|---|
| Docker | ≥ 25.x | [docs.docker.com](https://docs.docker.com) |
| Docker Compose | ≥ 2.x | Incluido con Docker Desktop |
| Minikube | ≥ 1.33 | `brew install minikube` |
| kubectl | ≥ 1.30 | `brew install kubectl` |
| Terraform | ≥ 1.8 | `brew install terraform` |
| Make | cualquiera | `brew install make` |

## Quickstart (5 comandos)

```bash
# 1. Clonar el repositorio
git clone https://github.com/ndf14685/ml-serving-infrastructure
cd ml-serving-infrastructure

# 2. Configurar variables de entorno
make setup
# → Crea .env desde .env.example. Edita API_KEY y GRAFANA_ADMIN_PASSWORD

# 3. Editar .env con tus valores
nano .env

# 4. Levantar todos los servicios
make run

# 5. Verificar que todo está bien
make health
```

En 2-3 minutos tendrás todo corriendo en:
- **API**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin / tu-password)

## Uso de la API

### Verificar salud del servicio
```bash
curl http://localhost:8000/health
```

### Ver un ejemplo de request
```bash
curl http://localhost:8000/predict/example
```

### Hacer una predicción
```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: tu-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'
```

**Respuesta esperada:**
```json
{
  "predicted_class": "setosa",
  "confidence": 0.97,
  "model_version": "1.0.0",
  "input_received": { "sepal_length": 5.1, ... }
}
```

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `API_KEY` | Clave para autenticar requests | ✅ Sí |
| `GRAFANA_ADMIN_PASSWORD` | Password del admin de Grafana | ✅ Sí |
| `LOG_LEVEL` | Nivel de logs (DEBUG/INFO/WARNING/ERROR) | No (default: INFO) |
| `ENVIRONMENT` | Entorno (development/staging/production) | No (default: development) |
| `MODEL_VERSION` | Versión del modelo activo | No (default: 1.0.0) |

Ver `.env.example` para la lista completa.

## Tests

```bash
# Correr unit tests de todos los servicios
make test

# Correr tests de un servicio específico
cd services/inference-api
python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing

# Correr integration tests (requiere servicios corriendo)
make integration-test
```

### Cobertura objetivo

| Servicio | Cobertura mínima |
|---|---|
| inference-api | ≥ 80% |
| preprocessing-service | ≥ 80% |
| model-manager | ≥ 80% |

## Deploy a Kubernetes (local con Minikube)

```bash
# 1. Iniciar Minikube
minikube start --cpus=4 --memory=8192

# 2. Habilitar addons necesarios
minikube addons enable ingress
minikube addons enable metrics-server

# 3. Deploy con Terraform
cd infrastructure/terraform
terraform init
terraform plan -var="api_key=tu-api-key"
terraform apply -var="api_key=tu-api-key"

# 4. Verificar estado
make k8s-status

# 5. Obtener URL del servicio
minikube service inference-api -n ml-serving --url
```

## Monitoreo

### Acceder a Grafana
1. Navegar a http://localhost:3000
2. Login: admin / (tu GRAFANA_ADMIN_PASSWORD)
3. El dashboard "ML Serving Infrastructure — Overview" está pre-configurado

### Métricas disponibles

| Métrica | Descripción |
|---|---|
| `inference_api_requests_total` | Total de requests por endpoint/status |
| `inference_api_request_duration_seconds` | Latencia (histograma) |
| `inference_api_predictions_total` | Predicciones por clase |
| `inference_api_prediction_confidence` | Distribución de confianza |
| `inference_api_model_loaded` | 1 si el modelo está en memoria |

## CI/CD Pipeline

```
PR a main → lint → security → unit-tests → docker-build → scan
merge a main → build-push (imágenes a ghcr.io)
manual → deploy-production (blue-green con aprobación)
```

Ver [ARCHITECTURE.md](./ARCHITECTURE.md) para el diagrama completo.

## Troubleshooting

**El servicio no levanta:**
```bash
docker compose logs inference-api
# Verificar que .env tiene API_KEY configurada
```

**Error 401 en /predict:**
```bash
# Verificar que estás enviando el header correcto
curl -H "X-API-Key: tu-api-key" ...
```

**Modelo no cargado (503 en /predict):**
```bash
# Verificar que model-manager está healthy
docker compose ps
curl http://localhost:8002/ready
```

**Grafana no muestra datos:**
```bash
# Verificar que Prometheus está scrapeando
curl http://localhost:9090/targets
```

Para más detalles ver [RUNBOOK.md](./RUNBOOK.md).

## Known Limitations

- El modelo se entrena en memoria al iniciar el `model-manager`. En producción real, el modelo debería versionarse en un Model Registry (MLflow, W&B).
- La estrategia blue-green está implementada para `inference-api`. Los otros servicios usan rolling update estándar.
- Los Kubernetes Secrets están en base64 (no encriptados at-rest). En producción usar HashiCorp Vault o AWS Secrets Manager.

## Mejoras Futuras

- Integrar MLflow para model registry y experiment tracking
- Implementar A/B testing a nivel de modelo (no solo infraestructura)
- Agregar distributed tracing con Jaeger/OpenTelemetry
- Implementar GitOps con ArgoCD
- Agregar autenticación OAuth2 / JWT en lugar de API Key estática

## AI Usage

Ver [AI_USAGE.md](./AI_USAGE.md) para declaración completa de uso de IA según la política del challenge.

---

*Versión: 1.0.0 | Autor: Nestor | Fecha: 2026-04-09*
