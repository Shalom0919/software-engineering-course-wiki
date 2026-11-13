#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=. python -m llmwiki serve --dir ./site --port "${1:-8765}"
