#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=. python -m llmwiki build --out ./site
