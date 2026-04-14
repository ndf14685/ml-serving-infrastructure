# Architecture — ML Serving Infrastructure

## 1. Visión General

Este sistema sirve un modelo de clasificación Iris (scikit-learn RandomForest) via una arquitectura de microservicios, con observabilidad completa y deployment blue-green sin downtime.

```
[Cliente HTTP]
      │
      │ POST /predict  {"sepal_length": 5.1, ...}
      ▼
[Ingress Controller — nginx]
      │
      ▼
[inference-api :8000]
      ├── Autentica API Key (X-API-Key header)
      ├── Valida payload (Pydantic v2)
      ├── Llama preprocessing-service → features validadas
      ├── Carga modelo desde volumen compartido
      ├── Ejecuta predicción sklearn
      ├── Emite métricas Prometheus
      └── Retorna: {"class": "setosa", "confidence": 0.97}

[preprocessing-service :8001]   [model-manager :8002]
      │                                │
      │ Valida rangos Iris             │ Entrena y persiste
      │ Retorna features array         │ el modelo .pkl
      ▼                                ▼
[Volumen compartido: /app/models/iris_model.pkl]

[Prometheus :9090] ← scrape cada 15s ← todos los servicios
[Grafana :3000]    ← datasource Prometheus → dashboards
```

---

## 2. Microservicios

| Servicio | Puerto | Responsabilidad | Réplicas (prod) |
|---|---|---|---|
| `inference-api` | 8000 | Servir predicciones, autenticación, rate limiting | 2–6 (HPA) |
| `preprocessing-service` | 8001 | Validar y normalizar features Iris | 2–4 (HPA) |
| `model-manager` | 8002 | Entrenar, persistir y servir metadata del modelo | 1 (singleton) |

---

## 3. Flujo de Datos

```
1. Cliente envía POST /predict con X-API-Key header
2. Ingress → inference-api
3. auth.py verifica API Key (hmac.compare_digest, timing-safe)
4. Pydantic valida schema (tipos, campos requeridos)
5. inference-api → preprocessing-service POST /preprocess
6. validators.py verifica rangos biológicos válidos Iris
7. inference-api carga modelo desde /app/models/ (joblib)
8. RandomForest.predict_proba() → clase + confianza
9. Prometheus counters/histograms actualizados
10. Respuesta: {predicted_class, confidence, model_version}
```

---

## 4. Decisiones de Diseño (ADRs)

### ADR-001: FastAPI sobre Flask
**Decisión:** FastAPI con Pydantic v2 para todos los servicios.
**Razón:** Validación automática de schemas, async nativo, documentación OpenAPI auto-generada, mejor performance.

### ADR-002: RandomForest sobre otros modelos
**Decisión:** RandomForest de scikit-learn para clasificación Iris.
**Razón:** Robusto, interpretable, no requiere GPU, serialización estable con joblib.

### ADR-003: Volumen compartido para el modelo
**Decisión:** PVC compartido entre model-manager (escritura) e inference-api (lectura).
**Razón:** Permite actualizar el modelo sin rebuild de imágenes. Tradeoff: acoplamiento via filesystem.

### ADR-004: Preprocessing como servicio separado
**Decisión:** Servicio independiente en lugar de lógica en inference-api.
**Razón:** Separation of concerns, escalabilidad independiente, testeable en aislamiento.

### ADR-005: Blue-Green para producción
**Decisión:** Blue-green deployment via selector switch en el Service de K8s.
**Razón:** Rollback < 5 segundos. Alternativa (rolling update) tiene período de versiones mixtas.

### ADR-006: Terraform para IaC
**Decisión:** Terraform gestiona la infraestructura K8s, YAML manifests son la fuente de verdad declarativa.
**Razón:** Terraform permite gestión de estado, módulos reutilizables y plan antes de apply.

---

## 5. Modelo de Seguridad

```
┌─────────────────────────────────────────────┐
│  Capa 1: Autenticación                       │
│  - API Key via X-API-Key header              │
│  - hmac.compare_digest (timing-safe)         │
│  - Rate limiting: 100 req/min por IP         │
├─────────────────────────────────────────────┤
│  Capa 2: Contenedores                        │
│  - Usuario non-root (uid 1001)               │
│  - readOnlyRootFilesystem: true              │
│  - allowPrivilegeEscalation: false           │
│  - capabilities drop ALL                     │
├─────────────────────────────────────────────┤
│  Capa 3: Red                                 │
│  - NetworkPolicies: default deny all         │
│  - Solo inference-api expuesto externamente  │
│  - Preprocessing y model-manager: ClusterIP  │
├─────────────────────────────────────────────┤
│  Capa 4: Secrets                             │
│  - API Key en K8s Secret (no en ConfigMap)   │
│  - Nunca en variables de entorno hardcoded   │
│  - Scanning Trivy en CI (0 CRITICAL)         │
└─────────────────────────────────────────────┘
```

---

## 6. Observabilidad

### Métricas Prometheus

| Métrica | Tipo | Labels |
|---|---|---|
| `http_requests_total` | Counter | method, endpoint, http_status |
| `http_request_duration_seconds` | Histogram | method, endpoint |
| `model_predictions_total` | Counter | predicted_class |
| `model_prediction_confidence` | Histogram | — |
| `model_loaded` | Gauge | — |
| `preprocessing_requests_total` | Counter | status |
| `preprocessing_duration_seconds` | Histogram | — |

### Alertas activas

| Alerta | Condición | Severidad |
|---|---|---|
| `HighErrorRate` | error rate > 5% por 5min | critical |
| `HighLatencyP95` | p95 > 2s por 10min | warning |
| `ModelNotLoaded` | model_loaded == 0 | critical |
| `LowPredictionConfidence` | avg confidence < 70% por 30min | warning |
| `PodCrashLooping` | restarts > 3 en 10min | critical |

---

## 7. Estrategia de Deploy

### Blue-Green (Producción)

```
Estado inicial:
  Service selector: app=inference-api, color=blue
  inference-api-blue ← todo el tráfico

Durante deploy:
  1. kubectl apply inference-api-green (nueva versión)
  2. kubectl rollout status → esperar Ready
  3. Smoke tests contra inference-api-green (sin tráfico)
  4. kubectl patch service → selector color=green
  5. Todo el tráfico migra instantáneamente
  6. Si falla: patch → color=blue (rollback < 5s)
  7. Si ok: delete inference-api-blue

Tiempo de rollback: < 5 segundos
Downtime: 0
```

### Rolling Update (Staging)

```
kubectl rollout status deployment/inference-api
maxUnavailable: 1
maxSurge: 1
```

---

## 8. Estructura del Repositorio

```
ml-serving-infrastructure/
├── services/          → Código de aplicación (Python/FastAPI)
│   ├── inference-api/
│   ├── preprocessing-service/
│   └── model-manager/
├── infrastructure/
│   ├── terraform/     → IaC para K8s (módulos: networking, kubernetes)
│   ├── kubernetes/    → Manifests YAML (base + overlays staging/prod)
│   └── monitoring/    → Prometheus config + Grafana dashboards
├── .github/workflows/ → CI/CD pipelines (ci, build-push, staging, production)
├── scripts/           → Scripts operacionales (setup, deploy, rollback)
└── docker-compose.yml → Entorno local de desarrollo
```

---

## 9. Limitaciones Conocidas

1. **PVC ReadWriteOnce**: El modelo solo puede ser escrito por un pod a la vez. En multi-node, model-manager es singleton para evitar conflictos.
2. **Autenticación simple**: API Key single-tenant. Para multi-tenant se necesitaría OAuth2/JWT.
3. **Modelo en disco**: No hay model registry. Para producción real se recomienda MLflow o BentoML.
4. **Sin TLS interno**: La comunicación entre microservicios va sin TLS. En producción se usaría Istio o cert-manager.
5. **Iris dataset**: Modelo demo. Para modelos reales considerar latencia de inferencia y batch prediction.
