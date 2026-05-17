#!/bin/sh
set -e
docker build -t tsuba-proxy:test ./proxy
docker run --rm --entrypoint sh -v "$(pwd)/proxy:/proxy" tsuba-proxy:test \
  -c "pip install -q pytest && cd /proxy && python -m pytest tests/ -v"
