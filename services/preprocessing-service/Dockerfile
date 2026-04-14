# ============================================================
# Dockerfile — Preprocessing Service (Multi-stage build)
#
# 🧒 PARA NIÑOS: Igual que el de la API, construimos en
# dos pasos: primero instalamos todo (cocina sucia),
# luego solo nos quedamos con lo necesario (pizza lista).
#
# 📘 TÉCNICO: Multi-stage build con usuario no-root.
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
      description="Preprocessing Service — Feature validation and transformation"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PREPROCESSING_PORT=8001 \
    ENVIRONMENT=production

COPY --from=builder /opt/venv /opt/venv

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home --shell /bin/false appuser && \
    mkdir -p /app && chown -R appuser:appgroup /app

WORKDIR /app
COPY --chown=appuser:appgroup app/ ./app/

USER appuser
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
