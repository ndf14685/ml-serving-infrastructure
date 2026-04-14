# Guia de ejecucion local — Windows 11

> Doc personal para levantar el stack completo en Windows 11 con Docker Desktop.
> No subir al repo (ya esta en .gitignore como *.local.md).

---

## Prerequisitos

### 1. Docker Desktop
- Descargar desde https://www.docker.com/products/docker-desktop/
- Instalar con configuracion por defecto (WSL2 backend recomendado)
- Verificar: abrir PowerShell o Git Bash y correr:
  ```
  docker --version
  docker compose version
  ```
  Debe mostrar Docker >= 25.x y Compose >= 2.x

### 2. Git Bash (para correr los scripts .sh y make)
- Viene incluido con Git for Windows: https://git-scm.com/download/win
- Alternativamente instalar `make` via Chocolatey:
  ```
  choco install make
  ```
  O via Scoop:
  ```
  scoop install make
  ```

### 3. Verificar que `make` esta disponible
Abrir Git Bash y correr:
```bash
make --version
```
Si no aparece, usar los comandos docker compose directamente (ver seccion alternativa mas abajo).

---

## Paso a Paso — Levantar el stack

Todos los comandos se corren desde **Git Bash** (no PowerShell ni CMD).

### 1. Navegar al proyecto

```bash
cd /d/ndf14/workspace/kinetic/ml-serving-infrastructure
```

### 2. Crear el archivo .env

```bash
cp .env.example .env
```

Editar `.env` con Notepad o VS Code. Cambiar al menos estos dos valores:

```
API_KEY=mi-clave-secreta-123          # cualquier string, lo usas en los curl
GRAFANA_ADMIN_PASSWORD=mi-password    # para entrar a Grafana
```

Los demas valores pueden quedar como estan para desarrollo local.

### 3. Construir y levantar todos los servicios

```bash
make run
```

O si `make` no esta disponible:

```bash
docker compose up --build -d
```

Primera vez tarda 3-5 minutos porque construye las 3 imagenes Docker.

### 4. Verificar que todo levanto bien

```bash
make health
```

O manualmente:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

Cada uno debe responder `{"status":"healthy",...}`.

Ver logs si algo falla:

```bash
docker compose logs -f
# O un servicio especifico:
docker compose logs -f model-manager
```

El model-manager tarda ~30 segundos en entrenarse la primera vez. Esperar a que aparezca:
```
Modelo entrenado con accuracy: 1.0000
Model Manager listo
```

---

## Probar la API

### Ver documentacion interactiva

Abrir en el browser:
```
http://localhost:8000/docs
```

### Hacer una prediccion (Git Bash)

```bash
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: mi-clave-secreta-123" \
  -H "Content-Type: application/json" \
  -d "{\"sepal_length\": 5.1, \"sepal_width\": 3.5, \"petal_length\": 1.4, \"petal_width\": 0.2}"
```

Respuesta esperada:
```json
{
  "predicted_class": "setosa",
  "confidence": 1.0,
  "model_version": "1.0.0",
  "input_received": {...}
}
```

### Sin API Key (debe dar 401)

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"sepal_length\": 5.1, \"sepal_width\": 3.5, \"petal_length\": 1.4, \"petal_width\": 0.2}"
```

### Ejemplo de flores para probar

| Especie | sepal_length | sepal_width | petal_length | petal_width |
|---|---|---|---|---|
| setosa | 5.1 | 3.5 | 1.4 | 0.2 |
| versicolor | 6.0 | 2.9 | 4.5 | 1.5 |
| virginica | 6.9 | 3.1 | 5.4 | 2.1 |

---

## Monitoring

### Grafana

Abrir: http://localhost:3000

- Usuario: `admin`
- Password: el valor de `GRAFANA_ADMIN_PASSWORD` en tu `.env`

El dashboard "ML Serving Infrastructure — Overview" se carga automaticamente.
Si no aparece, ir a Dashboards > Browse.

### Prometheus

Abrir: http://localhost:9090

Queries utiles:
```
# Total de predicciones por clase
inference_api_predictions_total

# Latencia promedio
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Estado del modelo (1=cargado, 0=no disponible)
inference_api_model_loaded
```

Para generar trafico y ver metricas en tiempo real, ejecutar varias veces el curl de prediccion.

---

## Correr los tests

Requiere Python 3.11 instalado localmente. Si no tenes Python, usar Docker.

### Con Python local

```bash
# Instalar dependencias del servicio
cd services/inference-api
pip install -r requirements.txt

# Correr unit tests
python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing

cd ../..
```

### Con make (corre los 3 servicios)

```bash
make unit-test
```

### Integration tests (requiere servicios corriendo)

```bash
make integration-test
```

---

## Detener el stack

```bash
make stop
```

O:
```bash
docker compose down
```

Para eliminar tambien los volumenes (borra el modelo entrenado, Prometheus data, Grafana data):

```bash
docker compose down --volumes
```

---

## Troubleshooting

### "API_KEY es requerida" al levantar

El archivo `.env` no existe o no tiene `API_KEY` seteada.
Verificar que hiciste `cp .env.example .env` y que editaste el valor.

### inference-api no levanta (espera a model-manager)

El `inference-api` espera que `model-manager` este `healthy` antes de arrancar.
El model-manager necesita ~30-60 segundos para entrenar el modelo la primera vez.
Esperar y revisar: `docker compose logs -f model-manager`

### curl no reconocido en Windows

Usar Git Bash en lugar de PowerShell/CMD. O en PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

### Error de permisos en Docker Desktop

Asegurarse de que Docker Desktop tiene WSL2 integration habilitada:
Docker Desktop > Settings > Resources > WSL Integration

### Puerto en uso

Si alguno de los puertos 8000/8001/8002/9090/3000 esta ocupado:
```bash
netstat -ano | findstr :8000
```
Cambiar el puerto en `.env` y en `docker-compose.yml` si es necesario.

### Reiniciar servicios limpios

```bash
make clean
make run
```

---

## Resumen rapido (happy path)

```bash
# En Git Bash, parado en ml-serving-infrastructure/
cp .env.example .env
# Editar .env: cambiar API_KEY y GRAFANA_ADMIN_PASSWORD
docker compose up --build -d
# Esperar ~2 minutos
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"sepal_length\":5.1,\"sepal_width\":3.5,\"petal_length\":1.4,\"petal_width\":0.2}"
# Abrir http://localhost:3000 para Grafana
```
