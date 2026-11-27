import json,re,os,datetime as dt
B='/workspace/gurumaxx'; R='/workspace/li-gong-repo/graph/translated'; U='https://x.com/z9_s8_y_9/status/'
K=dt.timezone(dt.timedelta(hours=9))
tx=json.load(open(B+'/coll/tx_all.json'))
src={x['id']:x for x in json.load(open(B+'/coll/src.json'))}
raw={}
for l in open(B+'/raw/posts.jsonl'):
    p=json.loads(l); raw[p['id']]=p
def kdt(i): return dt.datetime.fromisoformat(raw[i]['created_at'].replace('Z','+00:00')).astimezone(K)
ENG={i for i in tx if len(re.findall(r'[\uac00-\ud7a3]',src[i]['text']))<15}
def qlink(i):
    out=[]
    for t,r in src[i]['refs']:
        if t=='quoted':
            own=r in raw
            lab=f"the {kdt(r):%b %-d} post" if own else "a post by another account"
            out.append(f"quotes [{lab}]({(U+r) if own else 'https://x.com/i/status/'+r})")
    return out
def parse(path):
    mains={}; reps={}
    if not os.path.exists(path): return mains,reps
    s=open(path).read()
    body=s.split('\n\n',2)[2] if s.count('\n\n')>=2 else ''
    rp=''
    if '### Replies' in body:
        body,rp=body.split('### Replies',1)
    for blk in body.split('\n\n---\n\n'):
        blk=blk.strip().strip('-').strip()
        m=re.search(r'status/(\d+)\)',blk)
        if blk.startswith('## ') and m: mains[m.group(1)]=blk
    for line in rp.split('\n'):
        m=re.match(r'- \[\d\d:\d\d\]\(https://x.com/z9_s8_y_9/status/(\d+)\)',line)
        if m: reps[m.group(1)]=line
    return mains,reps
days={}
for i in tx: days.setdefault(kdt(i).date(),[]).append(i)
jl=[]
for d in sorted(days):
    path=f"{R}/{d:%Y/%m}/{d}.md"
    mains,reps=parse(path)
    for i in days[d]:
        t=tx[i]; en_flag=' · written in English' if i in ENG else ''
        if t.startswith('# '):
            title,_,body=t[2:].partition('\n')
            ql=qlink(i); link=f"[Original post]({U+i})"+(f" ({'; '.join(ql)})" if ql else '')+en_flag
            mains[i]=f"## {title.strip()}\n{link}\n\n{body.strip()}"
            en=title.strip()+'\n\n'+body.strip()
        else:
            b=' '.join(x.strip() for x in t.split('\n') if x.strip())
            rep=[r for tt,r in src[i]['refs'] if tt=='replied_to']
            ctx=f" ↳ [in reply to](https://x.com/i/status/{rep[0]})" if rep else ''
            reps[i]=f"- [{kdt(i):%H:%M}]({U+i}){ctx}: {b}"
            en=b
        rec={'id':i,'url':U+i,'date_kst':str(d),'cls':src[i]['cls'] if src[i]['cls']!='added' else 'teaching','en':en}
        if i in ENG: rec['original_lang']='en'
        jl.append(rec)
    mo=sorted(mains,key=lambda i:kdt(i),reverse=True); ro=sorted(reps,key=lambda i:kdt(i),reverse=True)
    s=f"# {d}: 마리지천 teachings, translated\n\nThese are posts by [@z9_s8_y_9](https://x.com/z9_s8_y_9), newest first. The date is in Korea time.\n\n"
    s+='\n\n---\n\n'.join(mains[i] for i in mo)
    if ro: s+=('\n\n---\n\n' if mo else '')+"### Replies\nShort replies and social posts, newest first (time in KST).\n\n"+'\n'.join(reps[i] for i in ro)
    os.makedirs(os.path.dirname(path),exist_ok=True); open(path,'w').write(s.rstrip()+'\n')
    print(d,len(mo),len(ro))
# posts_en.jsonl merge
P=R+'/posts_en.jsonl'; old=[json.loads(l) for l in open(P)]
ids={r['id'] for r in jl}; allr=[r for r in old if r['id'] not in ids]+jl
allr.sort(key=lambda x:(x['date_kst'],x['id']),reverse=True)
with open(P,'w') as f:
    for r in allr: f.write(json.dumps(r,ensure_ascii=False)+'\n')
print('jsonl',len(allr),'eng',sorted(ENG))
