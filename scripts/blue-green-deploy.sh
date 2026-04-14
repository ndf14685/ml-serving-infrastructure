#!/usr/bin/env bash
# ============================================================
# blue-green-deploy.sh — Deploy Blue-Green para inference-api
#
# 🧒 PARA NIÑOS:
# Imagina que tienes dos casas (AZUL y VERDE). La gente
# vive en una mientras preparamos la otra. Cuando está
# lista, movemos a todos en un instante. Si algo falla,
# volvemos a la casa anterior sin que nadie se dé cuenta.
#
# 📘 TÉCNICO:
# 1. Despliega el nuevo deployment (green)
# 2. Espera a que esté Ready
# 3. Corre smoke tests contra green
# 4. Cambia el Service selector → green
# 5. Si smoke tests fallan: revierte selector → blue
#
# 📘 USO:
#   ./scripts/blue-green-deploy.sh \
#     --image ghcr.io/user/inference-api:v1.1.0 \
#     --namespace ml-serving
# ============================================================

set -euo pipefail

# ── Parámetros ────────────────────────────────────────────
NAMESPACE="${NAMESPACE:-ml-serving}"
NEW_IMAGE=""
SMOKE_TEST_RETRIES=10
SMOKE_TEST_DELAY=5

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Parsear argumentos ────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)     NEW_IMAGE="$2"; shift 2 ;;
    --namespace) NAMESPACE="$2"; shift 2 ;;
    *) error "Argumento desconocido: $1"; exit 1 ;;
  esac
done

[[ -z "$NEW_IMAGE" ]] && { error "Usa --image <imagen:tag>"; exit 1; }

# ── Detectar color activo ─────────────────────────────────
get_active_color() {
  kubectl get service inference-api -n "$NAMESPACE" \
    -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue"
}

# ── Smoke tests ───────────────────────────────────────────
run_smoke_tests() {
  local pod_ip="$1"
  local api_key="$2"

  info "Corriendo smoke tests contra $pod_ip..."

  for i in $(seq 1 $SMOKE_TEST_RETRIES); do
    # Health check
    if ! kubectl exec -n "$NAMESPACE" deploy/inference-api-green -- \
        python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
      warn "Intento $i/$SMOKE_TEST_RETRIES: health check falló, esperando..."
      sleep $SMOKE_TEST_DELAY
      continue
    fi

    # Prediction test
    local result
    result=$(kubectl exec -n "$NAMESPACE" deploy/inference-api-green -- \
      python -c "
import urllib.request, json
req = urllib.request.Request(
  'http://localhost:8000/predict',
  data=json.dumps({'sepal_length':5.1,'sepal_width':3.5,'petal_length':1.4,'petal_width':0.2}).encode(),
  headers={'Content-Type':'application/json','X-API-Key':'$api_key'},
  method='POST'
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
print(data['predicted_class'])
" 2>/dev/null || echo "error")

    if [[ "$result" == "setosa" ]]; then
      success "Smoke tests OK (predicción: $result)"
      return 0
    fi

    warn "Intento $i/$SMOKE_TEST_RETRIES: predicción inesperada ($result)"
    sleep $SMOKE_TEST_DELAY
  done

  error "Smoke tests fallaron después de $SMOKE_TEST_RETRIES intentos"
  return 1
}

# ── Rollback ──────────────────────────────────────────────
rollback() {
  local from_color="$1"
  local to_color="$2"

  warn "ROLLBACK: Revirtiendo de $from_color → $to_color"
  kubectl patch service inference-api -n "$NAMESPACE" \
    -p "{\"spec\":{\"selector\":{\"app\":\"inference-api\",\"color\":\"$to_color\"}}}"

  kubectl delete deployment "inference-api-$from_color" -n "$NAMESPACE" --ignore-not-found
  error "Rollback completado. Tráfico en: $to_color"
  exit 1
}

# ── Main ──────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BLUE}Blue-Green Deploy — ML Serving Infrastructure${NC}"
  echo ""

  local active_color
  active_color=$(get_active_color)
  local new_color
  [[ "$active_color" == "blue" ]] && new_color="green" || new_color="blue"

  info "Color activo: $active_color → desplegando: $new_color"
  info "Imagen nueva: $NEW_IMAGE"

  # Obtener API key desde secret
  local api_key
  api_key=$(kubectl get secret ml-api-secrets -n "$NAMESPACE" \
    -o jsonpath='{.data.api-key}' | base64 --decode 2>/dev/null || echo "")

  # Step 1: Crear deployment nuevo (green)
  info "Creando deployment inference-api-$new_color..."
  kubectl get deployment "inference-api-$active_color" -n "$NAMESPACE" -o yaml | \
    sed "s/inference-api-$active_color/inference-api-$new_color/g" | \
    sed "s/color: $active_color/color: $new_color/g" | \
    sed "s|image: .*|image: $NEW_IMAGE|g" | \
    kubectl apply -f -

  # Step 2: Esperar a que esté Ready
  info "Esperando que inference-api-$new_color esté Ready..."
  kubectl rollout status deployment/"inference-api-$new_color" -n "$NAMESPACE" --timeout=300s

  # Step 3: Smoke tests
  if ! run_smoke_tests "" "$api_key"; then
    rollback "$new_color" "$active_color"
  fi

  # Step 4: Cambiar Service selector → new_color
  info "Cambiando tráfico: $active_color → $new_color"
  kubectl patch service inference-api -n "$NAMESPACE" \
    -p "{\"spec\":{\"selector\":{\"app\":\"inference-api\",\"color\":\"$new_color\"}}}"

  success "Tráfico migrado a $new_color"

  # Step 5: Verificar post-switch
  sleep 5
  if ! run_smoke_tests "" "$api_key"; then
    rollback "$new_color" "$active_color"
  fi

  # Step 6: Eliminar deployment anterior (o dejarlo como standby)
  info "Eliminando deployment $active_color..."
  kubectl delete deployment "inference-api-$active_color" -n "$NAMESPACE" --ignore-not-found

  echo ""
  success "Deploy blue-green completado. Activo: $new_color ($NEW_IMAGE)"
}

main "$@"
