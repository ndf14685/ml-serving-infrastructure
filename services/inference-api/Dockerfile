# ============================================================
# Dockerfile — Inference API (Multi-stage build)
#
# 🧒 PARA NIÑOS:
# Imagina que para hacer una pizza necesitas ensuciar muchas
# cosas: harina, tomate, etc. Pero cuando la sirves, solo
# muestras la pizza limpia, no todo el desorden de la cocina.
# Así funciona este Dockerfile: en la primera etapa (builder)
# instalamos todo lo necesario para construir; en la segunda
# etapa (final) solo copiamos lo esencial, resultando en una
# imagen pequeña y limpia.
#
# 📘 TÉCNICO:
# Stage 1 (builder): Instala dependencias en un virtualenv.
# Stage 2 (final):   Imagen mínima que copia solo el venv.
# Resultado: Imagen ~150MB vs ~500MB sin multi-stage.
# El usuario no-root previene privilege escalation.
# ============================================================

# ── STAGE 1: Builder ────────────────────────────────────────
FROM python:3.11-slim AS builder

# Evitar que Python genere archivos .pyc innecesarios
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Ruta del virtualenv
    VIRTUAL_ENV=/opt/venv

# Crear virtualenv aislado para las dependencias
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copiar solo requirements primero (aprovecha cache de Docker)
# Si requirements.txt no cambia, Docker no reinstala dependencias
COPY requirements.txt .

# Instalar dependencias sin archivos de cache (reduce tamaño)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ── STAGE 2: Final (imagen de producción) ───────────────────
FROM python:3.11-slim AS final

# Metadatos de la imagen (buena práctica)
LABEL maintainer="Nestor <david.fleitas@gmail.com>" \
      version="1.0.0" \
      description="ML Inference API — Iris species prediction"

# Variables de entorno de producción
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    # Puerto de escucha (puede sobreescribirse con -e)
    API_PORT=8000 \
    # Entorno por defecto
    ENVIRONMENT=production

# Copiar solo el virtualenv del stage builder (sin compiler, pip, etc.)
COPY --from=builder /opt/venv /opt/venv

# ── Seguridad: crear usuario no-root ────────────────────────
# Los contenedores NO deben correr como root (CIS Benchmark)
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home --shell /bin/false appuser

# Crear directorio de trabajo y carpeta para el modelo
RUN mkdir -p /app/models && \
    chown -R appuser:appgroup /app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación (con permisos correctos)
COPY --chown=appuser:appgroup app/ ./app/

# Cambiar a usuario no-root ANTES de exponer puertos o ejecutar
USER appuser

# Exponer el puerto de la API
EXPOSE 8000

# Health check para Docker Compose y Swarm
# (Kubernetes usa sus propios liveness/readiness probes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de inicio con uvicorn
# --host 0.0.0.0: escucha en todas las interfaces (necesario en contenedor)
# --workers 1: un worker para no duplicar el modelo en memoria
# --no-access-log: los logs de acceso se manejan via middleware
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
