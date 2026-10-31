import json,re
P=[json.loads(l) for l in open('raw/posts.jsonl')]
def txt(p): return (p.get('note_tweet') or {}).get('text') or p['text']
W={r'取坎填離|취감전리|추감첨리|취감보리|추감':6, r'坎離|감리|감괘|리괘|☵|☲':3, r'수승화강|水昇火降|心腎|심신상교|水火':3,
 r'하단전':2, r'펌핑|부풀|억지로|힘으로|밀어|아랫배':1.5, r'정수리|백회|열[어리]|상단전|니환|泥丸|천문':2, r'단전호흡':2,
 r'응축|소주천|임독|임맥|독맥':1, r'내단|金丹|금단|연정화기|환정보뇌|還精':2}
out=[]
for p in P:
    t=txt(p); s=0; hits=[]
    for k,w in W.items():
        m=re.findall(k,t)
        if m: s+=w*min(len(m),3); hits.append(m[0])
    if s>=5: out.append((s,p['created_at'][:10],p['id'],hits,t.replace('\n',' ')))
out.sort(key=lambda x:(-x[0],x[1]))
json.dump([dict(score=s,date=d,url=f'https://x.com/z9_s8_y_9/status/{i}',hits=h,text=t) for s,d,i,h,t in out],open('processed/ligong_matches.json','w'),ensure_ascii=False,indent=1)
print(len(out))
for s,d,i,h,t in out[:30]: print(s,d,i,h,t[:260],'\n')
