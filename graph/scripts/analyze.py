import json,re,collections,statistics as st
P=[json.loads(l) for l in open('raw/posts.jsonl')]
def txt(p): return (p.get('note_tweet') or {}).get('text') or p['text']
TEACH=re.compile(r'단전|내단|기문|천간|지지|호흡|수련|기운|명상|[괘卦]|坎|離|丹|氣|임맥|독맥|백회|정수리|횡격막|만트라|경락|혈자리|자오유주|선도|태극|오행|음양|☰|☱|☲|☳|☴|☵|☶|☷|감리|수승화강|정기신|연정화기|명문|용천|척추|골반|림프|크루라|신기문|조율|일진|[갑을병정무기경신임계][자축인묘진사오미신유술해]일')
MKT=re.compile(r'비트|BTC|btc|코인|트레이딩|매매|차트|롱|숏|주식|ETF|MSTR|나스닥|금리|법안|달러|이더')
def cls(p):
    t=txt(p); body=re.sub(r'^(@\w+\s*)+','',t)
    ism=body!=t or p.get('in_reply_to_user_id') not in (None,'1364400702789804035')
    if TEACH.search(t) and len(body)>=60: return 'teaching'
    if MKT.search(t): return 'market'
    if ism and len(body)<80: return 'social_reply'
    if len(body)>=120: return 'essay_other'
    return 'chatter'
rows=[]
for p in P:
    t=txt(p); refs=[r['type'] for r in p.get('referenced_tweets') or []]
    rows.append(dict(id=p['id'],date=p['created_at'],cls=cls(p),len=len(t),long=bool(p.get('note_tweet')),
      media=len((p.get('attachments') or {}).get('media_keys') or []),refs=refs,conv=p.get('conversation_id'),
      self_reply=p.get('in_reply_to_user_id')=='1364400702789804035',likes=p['public_metrics']['like_count']))
json.dump(rows,open('processed/post_index.json','w'),ensure_ascii=False)
c=collections.Counter(r['cls'] for r in rows); n=len(rows)
print('N',n,'range',min(r['date'] for r in rows)[:10],max(r['date'] for r in rows)[:10])
print({k:f'{v} ({v/n:.0%})' for k,v in c.most_common()})
for k in c:
    R=[r for r in rows if r['cls']==k]
    print(k,'medlen',st.median(r['len'] for r in R),'media%',round(sum(r['media']>0 for r in R)/len(R)*100),'long%',round(sum(r['long'] for r in R)/len(R)*100),'medlikes',st.median(r['likes'] for r in R))
print('self-reply',sum(r['self_reply'] for r in rows),'quotes',sum('quoted' in r['refs'] for r in rows))
conv=collections.Counter(r['conv'] for r in rows if r['self_reply'])
print('threads with self-replies',len(conv),'max len',conv.most_common(3))
by=collections.defaultdict(collections.Counter)
for r in rows: by[r['date'][:7]][r['cls']]+=1
for m in sorted(by)[-12:]: print(m,dict(by[m]))
# terms in teaching
T=[txt(p) for p,r in zip(P,rows) if r['cls']=='teaching']
terms=collections.Counter()
for t in T:
    for w in re.findall(r'[\u4e00-\u9fff]{2,4}|[☰-☷]|[가-힣]{2,6}',t): terms[w]+=1
stop=set('있습니다 합니다 그리고 하는 것이 있는 되는 이런 그런 하면 하고 됩니다 입니다 아니라 때문에 우리는 것은 수 있다 한다 이다 있다 것을 통해 하지만 이렇게 그래서 그러나 또는'.split())
print([ (w,k) for w,k in terms.most_common(150) if w not in stop][:90])
