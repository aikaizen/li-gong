#!/bin/bash
# ib.sh SEG=FILE ... : ingest each result file into its explicit segment (handles empty/error pages)
cd /workspace/gurumaxx
for a in "$@"; do s=${a%%=*}; f=/workspace/agent-tools/${a#*=}
  if grep -q '"data":\[' "$f"; then python3 scripts/ingest.py $s $f | grep -v '^total'
  else python3 scripts/empty.py $s $f; fi
done
python3 scripts/nextcalls.py
