#!/usr/bin/env bash
# down.sh — Derriba la infraestructura del Generador de Exámenes
# en el servidor remoto 172.28.230.10.
#
# Comportamiento:
#   ./down.sh        → Elimina contenedores + volúmenes Docker,
#                      PERO CONSERVA los datos (que viven en el home
#                      como bind mounts, no en volúmenes Docker).
#   ./down.sh --full → Además borra los datos del home (postgres,
#                      openwebui, agent_outputs, inputs).
#   ./down.sh --purge→ Borra TODO (contenedores, volúmenes, datos,
#                      imágenes construidas y el directorio remoto).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

REMOTE_HOST="172.28.230.10"
REMOTE_BASE="/home/dpilacuan/my_containers/exam"

case "${1:-}" in
  --full)
    echo "🛑 Eliminando contenedores, volúmenes y DATOS del home..."
    ssh "${REMOTE_HOST}" "cd ${REMOTE_BASE} && docker compose down -v 2>/dev/null || true"
    ssh "${REMOTE_HOST}" "rm -rf ${REMOTE_BASE}/data/postgres ${REMOTE_BASE}/data/openwebui ${REMOTE_BASE}/data/agent_outputs/* ${REMOTE_BASE}/data/inputs/* 2>/dev/null || true"
    echo "✅ Contenedores, volúmenes y datos eliminados."
    ;;
  --purge)
    echo "💥 PURGA TOTAL — eliminando contenedores, volúmenes, datos, imágenes y directorio..."
    ssh "${REMOTE_HOST}" "cd ${REMOTE_BASE} 2>/dev/null && docker compose down -v 2>/dev/null || true"
    ssh "${REMOTE_HOST}" "docker images -q | xargs -r docker rmi -f 2>/dev/null || true" 2>/dev/null || true
    ssh "${REMOTE_HOST}" "rm -rf ${REMOTE_BASE}"
    echo "✅ Todo eliminado. El directorio ${REMOTE_BASE} ya no existe."
    ;;
  *)
    echo "🛑 Eliminando contenedores y volúmenes Docker (los DATOS se conservan en el home)..."
    ssh "${REMOTE_HOST}" "cd ${REMOTE_BASE} 2>/dev/null && docker compose down -v 2>/dev/null || true"
    echo ""
    echo "✅ Contenedores y volúmenes Docker eliminados."
    echo "   Los datos persisten en: ${REMOTE_BASE}/data/"
    echo "   (postgres/, openwebui/, agent_outputs/, inputs/)"
    echo ""
    echo "   Para volver a levantar: ./up.sh"
    echo "   Para borrar también los datos: ./down.sh --full"
    ;;
esac

