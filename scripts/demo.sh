#!/usr/bin/env bash

# === Configuration ===
DATA_DIR="../data"    # e.g. ~/projects/data
TICKER="AAPL"
START_DATE="2025-01-01"
END_DATE="2025-06-01"
EVAL_DELAY=5
RESOLUTION="D"        # Finnhub resolution: 1,5,15,30,60,D,W,M

# === Run the bench ===
python ../examples/demo.py  \
  --ticker      "${TICKER}" \
  --start_date  "${START_DATE}" \
  --end_date    "${END_DATE}" \
  --data_dir    "${DATA_DIR}" \
  --eval_delay  "${EVAL_DELAY}" \
  --resolution  "${RESOLUTION}"
