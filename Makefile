# ============================================================
# Makefile — ML Serving Infrastructure
#
# 🧒 PARA NIÑOS: Este archivo es como un control remoto con
# botones. Cada botón (comando) hace algo diferente. En vez
# de escribir comandos largos, simplemente escribes
# "make nombre-del-boton".
#
# 📘 USO: make <target>
#   Ejemplo: make test    → corre todos los tests
#            make run     → levanta todos los servicios
#            make lint    → revisa que el código esté limpio
# ============================================================

.PHONY: help setup run stop test unit-test integration-test lint format security-check \
        build build-all push clean logs health

# Colores para output legible
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
RESET  := \033[0m

# Variables configurables
REGISTRY        ?= ghcr.io/ndf14685
IMAGE_TAG       ?= latest
K8S_NAMESPACE   ?= ml-serving
SERVICES        := inference-api preprocessing-service model-manager

# ── AYUDA ────────────────────────────────────────────────────
help: ## Muestra esta ayuda
	@echo ""
	@echo "$(GREEN)ML Serving Infrastructure — Comandos disponibles$(RESET)"
	@echo "────────────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── SETUP ────────────────────────────────────────────────────
setup: ## Configura el entorno local completo (primera vez)
	@echo "$(GREEN)▶ Configurando entorno local...$(RESET)"
	@test -f .env || (cp .env.example .env && echo "$(YELLOW)⚠  Se creó .env desde .env.example. Edita los valores secretos.$(RESET)")
	@pip install pre-commit --break-system-packages -q 2>/dev/null || true
	@pre-commit install 2>/dev/null || echo "$(YELLOW)⚠  pre-commit no disponible, instálalo manualmente$(RESET)"
	@echo "$(GREEN)✅ Setup completo$(RESET)"

# ── EJECUCIÓN LOCAL ──────────────────────────────────────────
run: ## Levanta todos los servicios con Docker Compose
	@echo "$(GREEN)▶ Iniciando servicios...$(RESET)"
	docker compose up --build -d
	@echo "$(GREEN)✅ Servicios corriendo. Usa 'make logs' para ver los logs$(RESET)"
	@echo "   API:        http://localhost:8000"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Grafana:    http://localhost:3000"

stop: ## Detiene todos los servicios
	@echo "$(YELLOW)▶ Deteniendo servicios...$(RESET)"
	docker compose down
	@echo "$(GREEN)✅ Servicios detenidos$(RESET)"

logs: ## Muestra logs de todos los servicios en tiempo real
	docker compose logs -f

health: ## Verifica que todos los servicios estén saludables
	@echo "$(GREEN)▶ Verificando salud de los servicios...$(RESET)"
	@curl -sf http://localhost:8000/health > /dev/null && echo "  ✅ inference-api: OK" || echo "  $(RED)❌ inference-api: FAIL$(RESET)"
	@curl -sf http://localhost:8001/health > /dev/null && echo "  ✅ preprocessing-service: OK" || echo "  $(RED)❌ preprocessing-service: FAIL$(RESET)"
	@curl -sf http://localhost:8002/health > /dev/null && echo "  ✅ model-manager: OK" || echo "  $(RED)❌ model-manager: FAIL$(RESET)"

# ── TESTING ──────────────────────────────────────────────────
test: unit-test ## Corre todos los tests unitarios (alias de unit-test)

unit-test: ## Corre los tests unitarios de todos los servicios con cobertura
	@echo "$(GREEN)▶ Corriendo unit tests...$(RESET)"
	@for svc in $(SERVICES); do \
		echo "$(YELLOW)  Testing $$svc...$(RESET)"; \
		cd services/$$svc && \
		python -m pytest tests/unit/ -v \
			--cov=app \
			--cov-report=term-missing \
			--cov-fail-under=80 \
			-q && \
		cd ../..; \
	done
	@echo "$(GREEN)✅ Unit tests completados$(RESET)"

integration-test: ## Corre los tests de integración (requiere servicios corriendo)
	@echo "$(GREEN)▶ Corriendo integration tests...$(RESET)"
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker compose -f docker-compose.test.yml down
	@echo "$(GREEN)✅ Integration tests completados$(RESET)"

# ── CALIDAD DE CÓDIGO ────────────────────────────────────────
lint: ## Verifica calidad del código (flake8 + black check)
	@echo "$(GREEN)▶ Verificando calidad del código...$(RESET)"
	@for svc in $(SERVICES); do \
		echo "$(YELLOW)  Linting $$svc...$(RESET)"; \
		cd services/$$svc && \
		python -m flake8 app/ --max-line-length=100 --statistics && \
		python -m black app/ --check --diff && \
		cd ../..; \
	done
	@echo "$(GREEN)✅ Lint completado$(RESET)"

format: ## Formatea el código automáticamente con black
	@echo "$(GREEN)▶ Formateando código...$(RESET)"
	@for svc in $(SERVICES); do \
		cd services/$$svc && python -m black app/ tests/ && cd ../..; \
	done
	@echo "$(GREEN)✅ Formato aplicado$(RESET)"

security-check: ## Analiza el código en busca de vulnerabilidades (bandit)
	@echo "$(GREEN)▶ Analizando seguridad del código...$(RESET)"
	@for svc in $(SERVICES); do \
		echo "$(YELLOW)  Escaneando $$svc...$(RESET)"; \
		cd services/$$svc && \
		python -m bandit -r app/ -ll -q && \
		cd ../..; \
	done
	@echo "$(GREEN)✅ Security check completado$(RESET)"

# ── DOCKER ───────────────────────────────────────────────────
build: ## Construye las imágenes Docker de todos los servicios
	@echo "$(GREEN)▶ Construyendo imágenes Docker...$(RESET)"
	@for svc in $(SERVICES); do \
		echo "$(YELLOW)  Building $$svc...$(RESET)"; \
		docker build -t $(REGISTRY)/$$svc:$(IMAGE_TAG) services/$$svc/; \
	done
	@echo "$(GREEN)✅ Imágenes construidas$(RESET)"

scan: ## Escanea imágenes Docker en busca de vulnerabilidades (trivy)
	@echo "$(GREEN)▶ Escaneando vulnerabilidades en imágenes...$(RESET)"
	@for svc in $(SERVICES); do \
		echo "$(YELLOW)  Escaneando $(REGISTRY)/$$svc:$(IMAGE_TAG)...$(RESET)"; \
		trivy image --exit-code 1 --severity CRITICAL $(REGISTRY)/$$svc:$(IMAGE_TAG); \
	done
	@echo "$(GREEN)✅ Scan completado$(RESET)"

push: build ## Construye y sube imágenes al registry
	@echo "$(GREEN)▶ Subiendo imágenes al registry...$(RESET)"
	@for svc in $(SERVICES); do \
		docker push $(REGISTRY)/$$svc:$(IMAGE_TAG); \
	done
	@echo "$(GREEN)✅ Imágenes subidas$(RESET)"

# ── KUBERNETES ───────────────────────────────────────────────
k8s-apply: ## Aplica todos los manifests de Kubernetes
	@echo "$(GREEN)▶ Aplicando manifests Kubernetes...$(RESET)"
	kubectl apply -f infrastructure/kubernetes/base/ -R -n $(K8S_NAMESPACE)
	@echo "$(GREEN)✅ Manifests aplicados$(RESET)"

k8s-status: ## Muestra el estado de los pods en el cluster
	kubectl get all -n $(K8S_NAMESPACE)

k8s-logs: ## Muestra logs del pod de inference-api
	kubectl logs -f -l app=inference-api -n $(K8S_NAMESPACE)

# ── LIMPIEZA ─────────────────────────────────────────────────
clean: ## Limpia archivos generados y contenedores detenidos
	@echo "$(YELLOW)▶ Limpiando...$(RESET)"
	docker compose down --volumes --remove-orphans 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpieza completa$(RESET)"

.DEFAULT_GOAL := help
