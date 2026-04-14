# ============================================================
# Dockerfile — Model Manager Service (Multi-stage build)
#
# 🧒 PARA NIÑOS: Este servicio necesita más espacio porque
# guarda el modelo aprendido. Pero igual usamos dos etapas
# para que la imagen sea lo más pequeña posible.
#
# 📘 TÉCNICO: Incluye volumen para persistencia del modelo.
# El modelo se entrena al iniciar si no existe el archivo.
# ============================================================

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS final

LABEL maintainer="Nestor <david.fleitas@gmail.com>" \
      version="1.0.0" \
      description="Model Manager Service — ML model lifecycle management"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    MODEL_MANAGER_PORT=8002 \
    MODEL_PATH=/app/models/iris_model.pkl \
    MODEL_VERSION=1.0.0 \
    ENVIRONMENT=production

COPY --from=builder /opt/venv /opt/venv

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home --shell /bin/false appuser && \
    mkdir -p /app/models && chown -R appuser:appgroup /app

WORKDIR /app
COPY --chown=appuser:appgroup app/ ./app/

USER appuser
EXPOSE 8002

# Volumen para persistir el modelo entre reinicios del contenedor
VOLUME ["/app/models"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
