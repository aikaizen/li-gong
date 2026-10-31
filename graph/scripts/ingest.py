#!/usr/bin/env python3
"""ingest.py SEG FILE [FILE...]: parse x MCP search_posts_all result files, append to raw jsonl (dedupe), update state.json"""
import sys, json, re, os, shutil, datetime
BASE='/workspace/gurumaxx'; RAW=BASE+'/raw'; ST=BASE+'/state.json'
def load_ids(fn):
    s=set()
    if os.path.exists(fn):
        for l in open(fn):
            try: s.add(json.loads(l).get('id') or json.loads(l).get('media_key'))
            except: pass
    return s
st=json.load(open(ST)) if os.path.exists(ST) else {"query":"from:z9_s8_y_9 -is:retweet","user_id":"1364400702789804035","segments":{},"calls_used":0}
seg=sys.argv[1]
ids={k:load_ids(f'{RAW}/{k}.jsonl') for k in ('posts','referenced','media')}
for fn in sys.argv[2:]:
    t=open(fn).read()
    i=t.find('{"'); d,end=json.JSONDecoder().raw_decode(t[i:])
    m=re.search(r'(\d+) of 1000 today',t[i+end:]); mm=re.search(r'(\d+) of 30 this minute',t[i+end:])
    ts=datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f')
    shutil.copy(fn,f'{RAW}/pages/{seg}_{ts}.txt')
    new=0
    with open(f'{RAW}/posts.jsonl','a') as o:
        for p in d.get('data',[]):
            if p['id'] in ids['posts']: continue
            p['_seg']=seg; o.write(json.dumps(p,ensure_ascii=False)+'\n'); ids['posts'].add(p['id']); new+=1
    inc=d.get('includes',{})
    with open(f'{RAW}/referenced.jsonl','a') as o:
        for p in inc.get('tweets',[]):
            if p['id'] in ids['referenced']: continue
            o.write(json.dumps(p,ensure_ascii=False)+'\n'); ids['referenced'].add(p['id'])
    with open(f'{RAW}/media.jsonl','a') as o:
        for p in inc.get('media',[]):
            if p['media_key'] in ids['media']: continue
            o.write(json.dumps(p,ensure_ascii=False)+'\n'); ids['media'].add(p['media_key'])
    dates=[p['created_at'] for p in d.get('data',[])]
    meta=d.get('meta',{}); s=st['segments'].setdefault(seg,{"count":0})
    s['count']+=new; s['next_token']=meta.get('next_token'); s['fresh']=False
    s['done']=(not meta.get('next_token')) or (bool(dates) and s.get('start_time') and min(dates)<s['start_time'])
    if meta.get('oldest_id'): s['oldest_id']=meta['oldest_id']
    if dates: s['oldest_date']=min(dates)
    st['calls_used']+=1
    if m: st['reads_left_today']=int(m.group(1))
    if mm: st['reads_left_minute']=int(mm.group(1))
    st['last_run']=datetime.datetime.now().astimezone().isoformat()
    st['total_posts']=len(ids['posts'])
    print(f"{seg}: +{new} oldest={s.get('oldest_date')} done={s['done']} next={s['next_token']}")
json.dump(st,open(ST,'w'),indent=1,ensure_ascii=False)
print('total',st['total_posts'],'calls',st['calls_used'],'left_today',st.get('reads_left_today'),'left_min',st.get('reads_left_minute'))
os.system(f'cp -a {BASE}/. /home/box/gurumaxx_backup/')
