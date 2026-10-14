#!/bin/bash
cd "${APP_DIR:-/app}" && python -m pytest -q "$(dirname "$0")/test_outputs.py"
