#!/usr/bin/env python3
"""nextcalls.py: list open segments (newest window first) with exact params for the next call."""
import json
st=json.load(open('/workspace/gurumaxx/state.json'))
o=[(k,s) for k,s in st['segments'].items() if not s.get('done') and (s.get('next_token') or s.get('fresh'))]
o.sort(key=lambda x:x[1].get('start_time') or '',reverse=True)
for k,s in o: print(k,s.get('call_start'),s.get('call_end'),s.get('next_token') if not s.get('fresh') else 'FRESH',(s.get('oldest_date') or '')[:10])
print('left_today',st.get('reads_left_today'),'left_min',st.get('reads_left_minute'),'total',st.get('total_posts'))
