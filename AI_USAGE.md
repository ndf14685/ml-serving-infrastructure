# AI Usage Declaration

Este documento declara de forma transparente el uso de herramientas de IA en este proyecto, según la política del challenge.

## Herramientas utilizadas

| Herramienta | Versión | Uso |
|---|---|---|
| Claude (Anthropic) | claude-sonnet-4-6 | Generación y revisión de código, documentación |

## Metodología

El desarrollo siguió un proceso de "entrevista-planificación-implementación":

1. **Entrevista de requerimientos**: Claude realizó preguntas estructuradas para entender el alcance, tecnologías preferidas y objetivos del portfolio antes de escribir una sola línea de código.

2. **Plan de proyecto**: Se generó un `PROJECT_PLAN.md` como documento maestro antes de la implementación, definiendo fases, principios (TDD, Secure Development, comentarios didácticos) y criterios de aceptación medibles.

3. **Implementación guiada**: Cada archivo fue generado siguiendo el plan, respetando los principios definidos (docstrings para niños + técnicos, tests antes del código de producción, usuario no-root en Docker, etc.).

## Prompts principales utilizados

Los prompts completos están disponibles en el historial de conversación de la sesión de trabajo. Los principales fueron:

1. "Necesito me entrevistes para realizar una práctica de laboratorio que está en este repositorio kinetic..." — Para establecer el scope.
2. "Antes de empezar déjame agregarte peticiones extras: desarrollo usando buenas prácticas, desarrollo seguro, TDD, comentarios para niños de 10 años, documentación clara..." — Para definir los principios de desarrollo.
3. "Usa ese project plan y comienza" — Para iniciar la implementación.

## Código generado vs. escrito manualmente

| Componente | Estado | Modificaciones |
|---|---|---|
| Estructura de directorios | Generado por IA | Ninguna |
| `services/*/app/*.py` | Generado por IA | Revisado y validado lógica de negocio |
| `services/*/tests/**` | Generado por IA (TDD: tests primero) | Verificados casos edge |
| `Dockerfile` (todos) | Generado por IA | Verificado multi-stage y usuario non-root |
| `docker-compose.yml` | Generado por IA | Ajustados nombres de variables |
| `infrastructure/terraform/**` | Generado por IA | Revisados recursos y configuraciones |
| `infrastructure/kubernetes/**` | Generado por IA | Ajustados resource limits |
| `.github/workflows/**` | Generado por IA | Verificados secrets y permisos |
| `infrastructure/monitoring/**` | Generado por IA | Ajustadas queries PromQL |
| `README.md`, `RUNBOOK.md` | Generado por IA | Verificado contenido técnico |

## Justificación del uso de IA

El challenge permite explícitamente el uso de IA con transparencia total. El uso de IA en este proyecto sirvió para:

1. **Acelerar el scaffolding**: Estructura de archivos, boilerplate de FastAPI, Dockerfiles base.
2. **Garantizar consistencia**: Los docstrings "para niños" y el estándar de comentarios se aplicaron uniformemente en todos los archivos.
3. **Reducir errores en IaC**: La sintaxis de Terraform y Kubernetes YAML es verbosa y propensa a errores tipográficos; IA reduce ese riesgo.
4. **Documentación completa**: README, RUNBOOK y ARCHITECTURE se generaron con estructura consistente.

Todo el código generado fue revisado para verificar corrección lógica, seguridad y adherencia a los principios del proyecto.
