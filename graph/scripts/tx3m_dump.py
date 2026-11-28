import sys,json;sys.path.insert(0,'/workspace/gurumaxx/scripts')
from tx3m_lib import *
maxc=int(sys.argv[1]) if len(sys.argv)>1 else 8000
EX={'2116327858205577314','2116194241827467497','2116021334866292917','2116016581625221141'}
import re
ex=open('/workspace/li-gong-repo/graph/translated/2026/10/2026-10-30.md').read()+open('/workspace/li-gong-repo/graph/translated/2026/10/2026-10-31.md').read()
EX=set(re.findall(r'\[Original post\]\(https://x.com/z9_s8_y_9/status/(\d+)\)',ex))
trunc=set(json.load(open(B+'/processed/truncated_ids.json')))
d=done();tot=0;k=0
for p in load():
    if p['id'] in d or p['id'] in EX: continue
    t=text(p)
    if tot and tot+len(t)>maxc: break
    r=','.join(x['type'][0] for x in p.get('referenced_tweets') or [])
    print(f"### {p['id']} {kst(p):%m-%d %H:%M} {p['cls']} {r}{' TRUNC' if p['id'] in trunc else ''}\n{t}\n")
    tot+=len(t);k+=1
print(f"# {k} posts {tot} chars; done {len(d)}")
