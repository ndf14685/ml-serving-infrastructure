#!/usr/bin/env bash
# ============================================================
# setup-local.sh — Configura el entorno local de desarrollo
#
# 🧒 PARA NIÑOS:
# Este script prepara todo lo que necesitas para trabajar
# en el proyecto: crea el archivo de configuración,
# instala las herramientas y arranca los servicios.
#
# 📘 USO:
#   chmod +x scripts/setup-local.sh
#   ./scripts/setup-local.sh
# ============================================================

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly ENV_FILE="$ROOT_DIR/.env"
readonly ENV_EXAMPLE="$ROOT_DIR/.env.example"

# ── Colores para output ───────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── Verificar prerequisitos ───────────────────────────────
check_prerequisites() {
  info "Verificando prerequisitos..."

  command -v docker >/dev/null 2>&1  || error "Docker no está instalado. Instálalo desde https://docs.docker.com/get-docker/"
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 || error "Docker Compose no está disponible."
  command -v python3 >/dev/null 2>&1 || warn "Python3 no encontrado. Necesario para tests locales."

  success "Prerequisitos OK"
}

# ── Crear archivo .env ────────────────────────────────────
setup_env_file() {
  if [[ -f "$ENV_FILE" ]]; then
    warn ".env ya existe. Saltando creación."
    return
  fi

  info "Creando .env desde .env.example..."
  cp "$ENV_EXAMPLE" "$ENV_FILE"

  # Generar API Key aleatoria
  local api_key
  api_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || \
            openssl rand -hex 32 2>/dev/null || \
            echo "local-dev-key-$(date +%s)")

  # Reemplazar el placeholder con la key generada
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/your-secret-api-key-here/$api_key/" "$ENV_FILE"
  else
    sed -i "s/your-secret-api-key-here/$api_key/" "$ENV_FILE"
  fi

  # Generar password de Grafana
  local grafana_pass
  grafana_pass=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))" 2>/dev/null || echo "admin123")

  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/change-me-in-production/$grafana_pass/" "$ENV_FILE"
  else
    sed -i "s/change-me-in-production/$grafana_pass/" "$ENV_FILE"
  fi

  success ".env creado con credenciales generadas automáticamente"
  echo ""
  echo -e "  ${YELLOW}API_KEY${NC}: $(grep API_KEY "$ENV_FILE" | cut -d= -f2)"
  echo -e "  ${YELLOW}Grafana${NC}: http://localhost:3000 (admin / $grafana_pass)"
  echo ""
}

# ── Construir imágenes ────────────────────────────────────
build_images() {
  info "Construyendo imágenes Docker..."
  cd "$ROOT_DIR"
  docker compose build --parallel
  success "Imágenes construidas"
}

# ── Arrancar servicios ────────────────────────────────────
start_services() {
  info "Arrancando servicios..."
  cd "$ROOT_DIR"
  docker compose up -d
  success "Servicios arrancados"
}

# ── Esperar a que los servicios estén saludables ──────────
wait_for_services() {
  info "Esperando a que los servicios estén listos..."

  local max_attempts=30
  local attempt=0

  while [[ $attempt -lt $max_attempts ]]; do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1 && \
       curl -sf http://localhost:8001/health >/dev/null 2>&1 && \
       curl -sf http://localhost:8002/health >/dev/null 2>&1; then
      success "Todos los servicios están saludables"
      return
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 3
  done

  echo ""
  error "Los servicios no respondieron en $(( max_attempts * 3 ))s. Revisa: docker compose logs"
}

# ── Mostrar resumen final ─────────────────────────────────
print_summary() {
  echo ""
  echo -e "${GREEN}============================================${NC}"
  echo -e "${GREEN}  Entorno local listo!${NC}"
  echo -e "${GREEN}============================================${NC}"
  echo ""
  echo "  Inference API:         http://localhost:8000"
  echo "  Preprocessing Service: http://localhost:8001"
  echo "  Model Manager:         http://localhost:8002"
  echo "  Prometheus:            http://localhost:9090"
  echo "  Grafana:               http://localhost:3000"
  echo ""
  echo "  Comandos útiles:"
  echo "    make test        → Correr tests unitarios"
  echo "    make health      → Verificar estado de servicios"
  echo "    make logs        → Ver logs en tiempo real"
  echo "    make stop        → Parar todos los servicios"
  echo ""
}

# ── Main ──────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BLUE}ML Serving Infrastructure — Setup Local${NC}"
  echo ""

  check_prerequisites
  setup_env_file
  build_images
  start_services
  wait_for_services
  print_summary
}

main "$@"
