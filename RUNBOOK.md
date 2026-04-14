# RUNBOOK — ML Serving Infrastructure

> Manual operacional: procedimientos para operar, mantener y responder a incidentes en el sistema.

## 1. Operaciones del Día a Día

### 1.1 Iniciar el entorno local

```bash
make run
# Verifica estado:
make health
```

### 1.2 Ver logs en tiempo real

```bash
# Todos los servicios
make logs

# Un servicio específico
docker compose logs -f inference-api
docker compose logs -f model-manager
```

### 1.3 Verificar métricas actuales

```bash
# Ver métricas crudas de la API
curl http://localhost:8000/metrics

# Ver en Grafana (requiere servicios corriendo)
open http://localhost:3000
```

---

## 2. Deploy a Producción (Blue-Green)

### Prerequisitos
- Imagen construida y subida al registry (`make push IMAGE_TAG=v1.2.0`)
- Acceso al cluster de producción (`kubectl config use-context production`)
- Aprobación de al menos un reviewer en GitHub

### Procedimiento paso a paso

**Paso 1:** Ir a GitHub Actions → "Deploy to Production (Blue-Green)"

**Paso 2:** Clic en "Run workflow"

**Paso 3:** Ingresar:
- `image_tag`: el SHA o versión a desplegar (ej: `sha-abc1234` o `v1.2.0`)
- `confirm`: escribir exactamente `DEPLOY`

**Paso 4:** El pipeline hace automáticamente:
1. Detecta el slot activo (blue o green)
2. Despliega la nueva versión en el slot inactivo
3. Corre smoke tests contra el nuevo slot (sin tráfico real)
4. Si smoke tests pasan → cambia el selector del Service
5. Observa 30 segundos
6. Si hay problemas → rollback automático al slot anterior

**Paso 5:** Verificar post-deploy:
```bash
# Verificar que el nuevo slot está recibiendo tráfico
kubectl get pods -l app=inference-api -n ml-serving

# Smoke test manual
curl -X POST https://api.production.com/predict \
  -H "X-API-Key: $PROD_API_KEY" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

---

## 3. Rollback Manual

Si necesitas revertir a la versión anterior manualmente:

```bash
# Ver el slot activo actualmente
kubectl get service inference-api -n ml-serving \
  -o jsonpath='{.spec.selector.slot}'

# Cambiar al slot opuesto manualmente
# Si el activo es "green", cambia a "blue":
kubectl patch service inference-api -n ml-serving \
  -p '{"spec":{"selector":{"app":"inference-api","slot":"blue"}}}'

# O usar el script de rollback:
./scripts/rollback.sh
```

El rollback toma menos de 10 segundos.

---

## 4. Respuesta a Incidentes

### 4.1 Alerta: `HighErrorRate` (>5% errores)

```bash
# 1. Ver logs recientes
kubectl logs -l app=inference-api -n ml-serving --tail=100

# 2. Ver métricas de error por endpoint
# En Grafana: dashboard "ML Serving Overview" → panel "Error Rate"

# 3. Si el problema es el modelo, verificar readiness:
kubectl get pods -l app=inference-api -n ml-serving
curl http://inference-api:8000/ready

# 4. Si necesitas rollback urgente:
./scripts/rollback.sh
```

### 4.2 Alerta: `ModelNotLoaded`

```bash
# El modelo no está en memoria. Verificar model-manager:
kubectl get pods -l app=model-manager -n ml-serving

# Ver logs del model-manager:
kubectl logs -l app=model-manager -n ml-serving

# Si el pod está en CrashLoopBackOff:
kubectl describe pod <nombre-del-pod> -n ml-serving

# Reiniciar el model-manager:
kubectl rollout restart deployment/model-manager -n ml-serving

# Esperar a que esté ready:
kubectl rollout status deployment/model-manager -n ml-serving
```

### 4.3 Alerta: `LowPredictionConfidence` (posible model drift)

```bash
# 1. Revisar distribución de predicciones en Grafana
# Dashboard "ML Serving Overview" → "Distribución de Confianza"

# 2. Verificar si el input data ha cambiado
# Revisar logs de preprocessing-service por errores de validación

# 3. Si hay drift confirmado:
# - Reentrenar el modelo con datos nuevos
# - Versionar el nuevo modelo (v1.1.0)
# - Hacer deploy via blue-green
```

---

## 5. Escalado Manual

### Escalar Inference API manualmente
```bash
# Aumentar réplicas temporalmente (ante pico de tráfico)
kubectl scale deployment inference-api -n ml-serving --replicas=4

# Volver al valor normal
kubectl scale deployment inference-api -n ml-serving --replicas=2
```

### Ver estado del HPA
```bash
kubectl get hpa -n ml-serving
kubectl describe hpa inference-api-hpa -n ml-serving
```

---

## 6. Backup y Recovery del Modelo

### Backup del modelo actual
```bash
# Copiar el modelo desde el PVC a local
kubectl cp ml-serving/$(kubectl get pod -l app=model-manager -n ml-serving \
  -o jsonpath='{.items[0].metadata.name}'):/app/models/iris_model.pkl \
  ./backup/iris_model_$(date +%Y%m%d_%H%M%S).pkl
```

### Restaurar un modelo desde backup
```bash
# Copiar modelo de backup al pod
kubectl cp ./backup/iris_model_20260409_120000.pkl \
  ml-serving/$(kubectl get pod -l app=model-manager -n ml-serving \
  -o jsonpath='{.items[0].metadata.name}'):/app/models/iris_model.pkl

# Reiniciar para que lo cargue
kubectl rollout restart deployment/model-manager -n ml-serving
```

---

## 7. Contactos y Escalación

| Nivel | Contacto | Cuando |
|---|---|---|
| L1 | Equipo de operaciones | Alertas de severidad `warning` |
| L2 | Nestor (autor) | Alertas `critical`, model drift |
| L3 | Arquitectura | Problemas de infraestructura mayor |

---

*Versión: 1.0.0 | Última actualización: 2026-04-09*
