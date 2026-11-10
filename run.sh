#!/bin/sh
# Запуск depviz без установки: ./run.sh -p curl -r <URL>
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src" exec python3 -m depviz "$@"
