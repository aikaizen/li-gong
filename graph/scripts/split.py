#!/usr/bin/env python3
"""split.py SEG CUT1 [CUT2...]: supersede open chain SEG by fresh sub-chains over [start_time, oldest_date) split at the given cut dates (YYYY-MM-DD)."""
import json,sys
p='/workspace/gurumaxx/state.json'; st=json.load(open(p)); S=st['segments']
seg=sys.argv[1]; s=S[seg]
end=s['oldest_date'].replace('.000Z','Z'); start=s['start_time']
cuts=[start]+[c+'T00:00:00Z' for c in sys.argv[2:]]+[end]
for i in range(len(cuts)-1):
    k=f'{seg}_{i+1}'
    S[k]=dict(start_time=cuts[i],end_time=cuts[i+1],call_start=cuts[i],call_end=cuts[i+1],count=0,next_token=None,done=False,fresh=True,note=f'split from {seg} (2026-10-31 run)')
    print(k,cuts[i],cuts[i+1])
s['done']=True; s['note']=(s.get('note','')+f'; superseded by split into {seg}_1..{seg}_{len(cuts)-1} at {end}').strip('; ')
json.dump(st,open(p,'w'),indent=1,ensure_ascii=False)
