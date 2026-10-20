#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 analysis/run_analysis.py > /dev/null
python3 excel/build_excel.py
python3 tests/test_model.py
python3 brief/build_brief.py
