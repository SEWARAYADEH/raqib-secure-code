#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r backend/requirements.txt

cd step-one-secure-code-ai-agent-frontend-professional
npm ci
npm run build
