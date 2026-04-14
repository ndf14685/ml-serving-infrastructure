#!/usr/bin/env bash
# ============================================================
# rollback.sh — Rollback a la versión anterior del servicio
#
# 🧒 PARA NIÑOS:
# Si algo salió mal después de una actualización, este
# script es como un botón de "deshacer" que vuelve todo
# al estado anterior que funcionaba bien.
#
# 📘 USO:
#   ./scripts/rollback.sh                           # Rollback inference-api
#   ./scripts/rollback.sh --service preprocessing-service
#   ./scripts/rollback.sh --service all
# ============================================================

set -euo pipefail

NAMESPACE="${NAMESPACE:-ml-serving}"
SERVICE="${SERVICE:-inference-api}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)   SERVICE="$2"; shift 2 ;;
    --namespace) NAMESPACE="$2"; shift 2 ;;
    *) error "Argumento desconocido: $1"; exit 1 ;;
  esac
done

rollback_deployment() {
  local name="$1"

  info "Rollback de $name en namespace $NAMESPACE..."

  # Verificar que el deployment existe
  if ! kubectl get deployment "$name" -n "$NAMESPACE" >/dev/null 2>&1; then
    error "Deployment '$name' no encontrado en namespace '$NAMESPACE'"
    return 1
  fi

  # Ver historial antes de revertir
  echo ""
  info "Historial de revisiones:"
  kubectl rollout history deployment/"$name" -n "$NAMESPACE"
  echo ""

  # Ejecutar rollback
  kubectl rollout undo deployment/"$name" -n "$NAMESPACE"

  # Esperar a que esté listo
  info "Esperando que $name esté disponible..."
  kubectl rollout status deployment/"$name" -n "$NAMESPACE" --timeout=120s

  # Verificar health
  sleep 5
  local ready_pods
  ready_pods=$(kubectl get deployment "$name" -n "$NAMESPACE" \
    -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

  if [[ "$ready_pods" -gt 0 ]]; then
    success "Rollback de $name completado ($ready_pods pods listos)"
  else
    error "Rollback de $name: pods no disponibles"
    kubectl describe deployment "$name" -n "$NAMESPACE"
    return 1
  fi
}

main() {
  echo ""
  echo -e "${YELLOW}ROLLBACK — ML Serving Infrastructure${NC}"
  echo ""

  if [[ "$SERVICE" == "all" ]]; then
    warn "Rollback de TODOS los servicios..."
    for svc in inference-api preprocessing-service model-manager; do
      rollback_deployment "$svc" || true
    done
  else
    rollback_deployment "$SERVICE"
  fi
}

main "$@"
