#!/bin/bash
# ingest all agent-tools result files newer than marker
cd /workspace/gurumaxx
M=.marker; [ -f $M ] || touch -d '2000-01-01' $M
F=$(find /workspace/agent-tools -name '*.txt' -newer $M -size +1k | xargs grep -l 'z9_s8_y_9\|"meta"' 2>/dev/null | xargs -r ls -tr 2>/dev/null)
touch $M
[ -n "$F" ] && python3 scripts/ingest_auto.py $F 2>&1 | grep -v '^total' ; python3 -c "import json;s=json.load(open('state.json'));print('TOTAL',s['total_posts'],'left',s.get('reads_left_today'),'min',s.get('reads_left_minute'))"
