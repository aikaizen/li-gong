import json,re,datetime,glob
B='/workspace/gurumaxx'
START=datetime.date(2026,8,1)
def kst(p): return datetime.datetime.fromisoformat(p['created_at'].replace('Z','+00:00'))+datetime.timedelta(hours=9)
def text(p):
    t=(p.get('note_tweet') or {}).get('text') or p['text']
    a=p.get('article')
    if a: t=(t+'\n[ARTICLE] '+json.dumps(a,ensure_ascii=False))
    return re.sub(r'https://t\.co/\S+','',t).strip()
def load():
    idx={q['id']:q for q in json.load(open(B+'/processed/post_index.json'))}
    ps=[json.loads(l) for l in open(B+'/raw/posts.jsonl')]
    ps=[p for p in ps if kst(p).date()>=START]
    for p in ps: p['cls']=idx.get(p['id'],{}).get('cls','social_reply')
    ps.sort(key=lambda p:p['created_at'],reverse=True)
    return ps
def done():
    d={}
    for f in sorted(glob.glob(B+'/translated/tx3m/*.txt')):
        for m in re.finditer(r'^### (\d+)\n(.*?)(?=^### \d+\n|\Z)',open(f).read(),re.M|re.S):
            d[m.group(1)]=m.group(2).strip()
    return d
