import sys,json,re,os,collections,datetime;sys.path.insert(0,'/workspace/gurumaxx/scripts')
from tx3m_lib import *
R='/workspace/li-gong-repo/graph/translated'
U='https://x.com/z9_s8_y_9/status/'
trunc=set(json.load(open(B+'/processed/truncated_ids.json')))
ps=load(); byid={p['id']:p for p in ps}
allp={}
for l in open(B+'/raw/posts.jsonl'):
    q=json.loads(l); allp[q['id']]=q
refd={}
for l in open(B+'/raw/referenced.jsonl'):
    q=json.loads(l); refd[q['id']]=q
# preserve original 5 verbatim
ORIG=json.load(open(B+'/translated/orig5.json')) if os.path.exists(B+'/translated/orig5.json') else None
if ORIG is None:
    ORIG={}
    for f in ['2026/10/2026-10-30.md','2026/10/2026-10-31.md']:
        body=open(f'{R}/{f}').read().split('\n## ',1)[1]
        for blk in ('## '+body).split('\n---\n'):
            blk=blk.strip(); i=re.search(r'status/(\d+)\)',blk).group(1); ORIG[i]=blk
    json.dump(ORIG,open(B+'/translated/orig5.json','w'),ensure_ascii=False,indent=1)
d=done()
def mdate(i):
    q=allp.get(i) or refd.get(i)
    if q and q.get('created_at'): return (datetime.datetime.fromisoformat(q['created_at'].replace('Z','+00:00'))+datetime.timedelta(hours=9)).strftime('%b %-d')
def qlink(p):
    out=[]
    for r in p.get('referenced_tweets') or []:
        if r['type']=='quoted':
            q=allp.get(r['id']) or refd.get(r['id']) or {}
            au=q.get('author_id'); own = r['id'] in allp or au=='1364400702789804035'
            dt=mdate(r['id'])
            url=U+r['id'] if own else f"https://x.com/i/status/{r['id']}"
            lab=(f"the {dt} post" if own else f"a post by another account") if dt else "a post"
            out.append(f"quotes [{lab}]({url})")
    return out
days=collections.defaultdict(list); jl=[]
for p in ps:
    i=p['id']; k=kst(p).date()
    if i in ORIG:
        blk=ORIG[i]; days[k].append(('main',blk))
        jl.append({'id':i,'url':U+i,'date_kst':str(k),'cls':p['cls'],'en':re.sub(r'^\[Original post\].*$','',blk,flags=re.M).strip()}); continue
    if i not in d: continue
    t=d[i]
    tn = i in trunc and 'cut off' not in t
    if t.startswith('# '):
        title,_,body=t[2:].partition('\n'); body=body.strip()
        if tn: body+="\n\n*(Translator's note: the post is cut off here by X.)*"
        ql=qlink(p); link=f"[Original post]({U+i})"+(f" ({'; '.join(ql)})" if ql else '')
        days[k].append(('main',f"## {title.strip()}\n{link}\n\n{body}"))
        en=title.strip()+'\n\n'+body
    else:
        body=' '.join(t.split('\n')).strip()
        if tn: body+=" *(cut off by X)*"
        rep=[r for r in p.get('referenced_tweets') or [] if r['type']=='replied_to']
        ctx=''
        if rep:
            rid=rep[0]['id']; ctx=f" ↳ [in reply to](https://x.com/i/status/{rid})"
        days[k].append(('reply',f"- [{kst(p):%H:%M}]({U+i}){ctx}: {body}"))
        en=body
    jl.append({'id':i,'url':U+i,'date_kst':str(k),'cls':p['cls'],'en':en})
idxl=[]
for k in sorted(days,reverse=True):
    m=[b for t,b in days[k] if t=='main']; r=[b for t,b in days[k] if t=='reply']
    s=f"# {k}: 마리지천 teachings, translated\n\nThese are posts by [@z9_s8_y_9](https://x.com/z9_s8_y_9), newest first. The date is in Korea time.\n\n"
    s+='\n\n---\n\n'.join(m)
    if r: s+=('\n\n---\n\n' if m else '')+"### Replies\nShort replies and social posts, newest first (time in KST).\n\n"+'\n'.join(r)
    os.makedirs(f"{R}/{k:%Y/%m}",exist_ok=True); open(f"{R}/{k:%Y/%m}/{k}.md",'w').write(s.rstrip()+'\n')
    total=len(m)+len(r)
    idxl.append(f"- [{k}]({k:%Y/%m}/{k}.md): {total} post{'s' if total!=1 else ''}"+(f" ({len(m)} main, {len(r)} repl{'ies' if len(r)!=1 else 'y'})" if r else ''))
rd=open(R+'/README.md').read().split('## Index')[0]
rd=rd.replace("This folder holds English translations of 마리지천's ([@z9_s8_y_9](https://x.com/z9_s8_y_9)) teaching posts.","This folder holds English translations of 마리지천's ([@z9_s8_y_9](https://x.com/z9_s8_y_9)) posts, from 2026-08-01 onward (KST). Teachings and essays have their own titled sections; short replies are grouped at the end of each day under *Replies*. Key terms are listed in [GLOSSARY.md](GLOSSARY.md), and [posts_en.jsonl](posts_en.jsonl) has every translation in machine-readable form.")
open(R+'/README.md','w').write(rd+'## Index\n'+'\n'.join(idxl)+'\n')
jl.sort(key=lambda x:(x['date_kst'],x['id']),reverse=True)
with open(R+'/posts_en.jsonl','w') as f:
    for x in jl: f.write(json.dumps(x,ensure_ascii=False)+'\n')
st={'scope':'KST 2026-08-01..newest','total_in_scope':len(ps),'translated':len(jl),'days_written':len(days),'oldest_day_written':str(min(days)) if days else None,'updated':datetime.datetime.now().isoformat()}
json.dump(st,open(B+'/translate_state.json','w'),indent=1); print(st)
