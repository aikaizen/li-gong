#!/usr/bin/env python3
"""ingest_auto.py FILE...: infer segment from post dates, call ingest per file. Then print open segments + next tokens."""
import sys,json,re,subprocess
st=json.load(open('/workspace/gurumaxx/state.json'))
for fn in sys.argv[1:]:
    t=open(fn).read(); i=t.find('{"'); d,_=json.JSONDecoder().raw_decode(t[i:])
    ds=[p['created_at'] for p in d.get('data',[])]
    seg=None
    if ds:
        mx=max(ds)
        for k,s in st['segments'].items():
            if (s.get('start_time') or '0')<=mx and (s.get('end_time') is None or mx< s['end_time']): seg=k;break
    if seg is None: print('UNKNOWN',fn,d.get('meta')); continue
    subprocess.run(['python3','/workspace/gurumaxx/scripts/ingest.py',seg,fn])
st=json.load(open('/workspace/gurumaxx/state.json'))
for k,s in st['segments'].items():
    if not s.get('done') and (s.get('next_token') or s.get('fresh')): print('OPEN',k,(s.get('oldest_date') or '')[:10],s.get('call_start'),s.get('call_end'),s.get('next_token'))
