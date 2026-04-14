#!/usr/bin/env bash
# ============================================================
# run-tests.sh — Ejecuta todos los tests del proyecto
#
# 🧒 PARA NIÑOS:
# Este script ejecuta todas las pruebas para asegurarse
# de que todo funciona correctamente.
#
# 📘 USO:
#   ./scripts/run-tests.sh              # Todos los tests
#   ./scripts/run-tests.sh --unit       # Solo tests unitarios
#   ./scripts/run-tests.sh --integration # Solo integration tests
#   ./scripts/run-tests.sh --coverage   # Con reporte de cobertura
# ============================================================

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
error()   { echo -e "${RED}[FAIL]${NC}  $*"; }

# ── Flags ─────────────────────────────────────────────────
RUN_UNIT=true
RUN_INTEGRATION=false
RUN_COVERAGE=false

for arg in "$@"; do
  case $arg in
    --unit)        RUN_UNIT=true; RUN_INTEGRATION=false ;;
    --integration) RUN_UNIT=false; RUN_INTEGRATION=true ;;
    --all)         RUN_UNIT=true; RUN_INTEGRATION=true ;;
    --coverage)    RUN_COVERAGE=true ;;
  esac
done

FAILED_SERVICES=()

# ── Tests unitarios ───────────────────────────────────────
run_unit_tests() {
  local services=("inference-api" "preprocessing-service" "model-manager")

  for service in "${services[@]}"; do
    info "Tests unitarios: $service"
    local service_dir="$ROOT_DIR/services/$service"

    if docker compose -f "$ROOT_DIR/docker-compose.yml" run --rm \
        -v "$service_dir":/app \
        --no-deps \
        "${service//-/_}" \
        sh -c "pip install pytest pytest-cov pytest-asyncio httpx --quiet && \
               pytest tests/unit/ -v \
               --cov=app \
               --cov-report=term-missing \
               --cov-fail-under=80" 2>/dev/null; then
      success "$service: tests unitarios OK"
    else
      error "$service: tests unitarios FALLARON"
      FAILED_SERVICES+=("$service (unit)")
    fi
  done
}

# ── Tests de integración ──────────────────────────────────
run_integration_tests() {
  info "Levantando servicios para integration tests..."

  cd "$ROOT_DIR"
  docker compose -f docker-compose.test.yml up -d --build

  info "Esperando servicios..."
  sleep 15

  local services=("inference-api" "preprocessing-service" "model-manager")
  for service in "${services[@]}"; do
    info "Integration tests: $service"
    if docker compose -f docker-compose.test.yml run --rm test-runner \
        sh -c "pip install pytest httpx pytest-asyncio --quiet && \
               pytest services/$service/tests/integration/ -v --tb=short"; then
      success "$service: integration tests OK"
    else
      error "$service: integration tests FALLARON"
      FAILED_SERVICES+=("$service (integration)")
    fi
  done

  info "Parando servicios de test..."
  docker compose -f docker-compose.test.yml down -v
}

# ── Main ──────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BLUE}ML Serving Infrastructure — Test Runner${NC}"
  echo ""

  [[ "$RUN_UNIT" == "true" ]] && run_unit_tests
  [[ "$RUN_INTEGRATION" == "true" ]] && run_integration_tests

  echo ""
  if [[ ${#FAILED_SERVICES[@]} -eq 0 ]]; then
    success "Todos los tests pasaron!"
  else
    error "Tests fallaron en: ${FAILED_SERVICES[*]}"
    exit 1
  fi
}

main "$@"
