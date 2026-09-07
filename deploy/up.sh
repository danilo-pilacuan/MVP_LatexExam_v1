#!/usr/bin/env bash
# up.sh — Levanta la infraestructura del Generador de Exámenes
# en el servidor remoto 172.28.230.10.
#
# Uso: ./up.sh            (copia código y levanta con build)
#      ./up.sh --no-build (levanta sin reconstruir imágenes)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
./deploy.sh "${1:-up}"
