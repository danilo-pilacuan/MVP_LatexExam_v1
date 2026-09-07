#!/usr/bin/env bash
# ============================================================
# deploy.sh — Despliega la infraestructura del "Generador de
# Exámenes" en el servidor remoto 172.28.230.10 (DGX H200 USFQ)
#
# Uso:
#   ./deploy.sh              # Despliega (copia código + levanta)
#   ./deploy.sh --no-build   # Solo copia y levanta sin rebuild
#   ./deploy.sh --down       # Derriba la infraestructura
#   ./deploy.sh --status     # Muestra el estado de los contenedores
#
# Requisitos:
#   - Clave SSH configurada para 172.28.230.10 (usuario dpilacuan)
#   - tar disponible en la máquina local (Git Bash lo incluye)
# ============================================================
set -euo pipefail

REMOTE_HOST="172.28.230.10"
REMOTE_USER="dpilacuan"
REMOTE_BASE="/home/${REMOTE_USER}/my_containers/exam"

# Directorio raíz del proyecto (sube 1 nivel desde deploy/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ============================================================
# Funciones
# ============================================================
remote() { ssh "${REMOTE_HOST}" "$@"; }

# Copia un conjunto de archivos/directorios al remoto usando tar+ssh
# (más fiable que rsync en entornos Windows/Git Bash).
# Uso: copy_tar <destino_remoto> <archivo1> <dir1> ...
copy_tar() {
  local dest="$1"; shift
  tar -C "${PROJECT_ROOT}" -cf - "$@" | ssh "${REMOTE_HOST}" "tar -xf - -C ${dest}"
}

cmd_up() {
  echo "🚀 Creando directorio remoto..."
  remote "mkdir -p ${REMOTE_BASE}/docker/latex-compiler \
                 ${REMOTE_BASE}/docker/embedding-service \
                 ${REMOTE_BASE}/docker/openwebui-custom \
                 ${REMOTE_BASE}/data/agent_outputs \
                 ${REMOTE_BASE}/data/inputs \
                 ${REMOTE_BASE}/data/postgres \
                 ${REMOTE_BASE}/data/openwebui"

  echo "📦 Copiando código fuente al servidor..."
  copy_tar "${REMOTE_BASE}" \
    main.py alembic.ini requirements.txt src scripts

  echo "🐳 Copiando docker/ (Dockerfiles, css, entrypoint)..."
  remote "mkdir -p ${REMOTE_BASE}/docker"
  copy_tar "${REMOTE_BASE}" \
    docker/latex-compiler docker/embedding-service docker/openwebui-custom docker/app

  # Copiar el docker-compose.yml remoto
  scp -q "$(dirname "${BASH_SOURCE[0]}")/docker-compose.yml" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE}/docker-compose.yml"

  # Crear el .env remoto (las variables `environment` del compose tienen
  # prioridad sobre el .env en pydantic-settings).
  remote "cat > ${REMOTE_BASE}/.env << 'EOF'
LATEX_COMPILER_URL=http://latex-compiler:8080/compile
EOF"

  echo "⬆️  Levantando la infraestructura..."
  if [ "${1:-}" = "--no-build" ]; then
    remote "cd ${REMOTE_BASE} && docker compose up -d"
  else
    remote "cd ${REMOTE_BASE} && docker compose up -d --build"
  fi

  echo "⏳ Esperando a que postgres esté listo..."
  remote "for i in \$(seq 1 30); do docker exec exam_postgres_db pg_isready -U exam_user >/dev/null 2>&1 && break; sleep 2; done"

  echo "🔁 Verificando que exam-app esté corriendo (reintenta si falló por timing)..."
  remote "cd ${REMOTE_BASE} && docker compose up -d exam-app 2>/dev/null || true"
  sleep 5

  echo ""
  echo "✅ Infraestructura desplegada en ${REMOTE_HOST}"
  echo "   - OpenWebUI:  http://${REMOTE_HOST}:39001"
  echo "   - API:        http://${REMOTE_HOST}:39002"
  echo "   - Postgres:   ${REMOTE_HOST}:39000"
  echo ""
  remote "cd ${REMOTE_BASE} && docker compose ps"
}

cmd_down() {
  echo "🛑 Derribando la infraestructura..."
  remote "cd ${REMOTE_BASE} && docker compose down 2>/dev/null || true"
  echo "✅ Contenedores derribados. Los datos (volúmenes) se conservan."
  echo "   Para borrar también los datos: docker compose down -v"
}

cmd_status() {
  echo "📊 Estado de la infraestructura en ${REMOTE_HOST}:"
  remote "cd ${REMOTE_BASE} && docker compose ps 2>/dev/null || echo 'No hay infraestructura desplegada'"
}

# ============================================================
# Main
# ============================================================
case "${1:-up}" in
  up)         cmd_up ;;
  --no-build) cmd_up --no-build ;;
  down)       cmd_down ;;
  --down)     cmd_down ;;
  status)     cmd_status ;;
  --status)   cmd_status ;;
  *)
    echo "Uso: $0 [up|down|status|--no-build]"
    exit 1
    ;;
esac
