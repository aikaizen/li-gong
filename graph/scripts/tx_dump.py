import json,re,sys
# usage: tx_dump.py CLS N  -> prints next N untranslated posts of class, newest first
cls=sys.argv[1]; N=int(sys.argv[2]); maxchars=int(sys.argv[3]) if len(sys.argv)>3 else 10**9
import glob,os
done=set()
for f in glob.glob('/workspace/gurumaxx/translated/batches/*.txt'):
    for m in re.finditer(r'^### (\d+)',open(f).read(),re.M): done.add(m.group(1))
idx={p['id']:p for p in json.load(open('processed/post_index.json'))}
posts=[json.loads(l) for l in open('raw/posts.jsonl')]
posts.sort(key=lambda t:t['created_at'],reverse=True)
k=0;tot=0
for t in posts:
    if idx[t['id']]['cls']!=cls or t['id'] in done: continue
    txt=(t.get('note_tweet') or {}).get('text') or t['text']
    txt=re.sub(r'https://t\.co/\S+','',txt).strip()
    if tot and tot+len(txt)>maxchars: break
    print(f"### {t['id']} {t['created_at'][:10]}\n{txt}\n")
    k+=1;tot+=len(txt)
    if k>=N: break
print(f"# {k} posts, {tot} chars; done total {len(done)}",file=sys.stderr)
