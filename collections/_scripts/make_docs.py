#!/usr/bin/env python3
import json,os,re,datetime as dt
B='/workspace/gurumaxx'; REPO='/workspace/li-gong-repo'; C=REPO+'/collections'; U='https://x.com/z9_s8_y_9/status/'
tx=json.load(open(B+'/coll/tx_full.json')); clusters=json.load(open(B+'/coll/clusters.json'))
state=json.load(open(B+'/collections_state.json')) if os.path.exists(B+'/collections_state.json') else {'clusters':{}}
raw={}
for l in open(B+'/raw/posts.jsonl'):
    p=json.loads(l); raw[p['id']]=p
K=dt.timezone(dt.timedelta(hours=9))
def kd(i): return dt.datetime.fromisoformat(raw[i]['created_at'].replace('Z','+00:00')).astimezone(K)
def split(i):
    t=tx[i]
    if t.startswith('# '):
        title,_,body=t[2:].partition('\n'); return title.strip(),body.strip(),True
    return None,t.strip(),False
def fixlinks(s):
    s=s.replace('](../../README.md)','](../../graph/translated/README.md)')
    s=re.sub(r'\]\(\.\./(\d\d)/(\d{4}-\d\d-\d\d)\.md\)',r'](../../graph/translated/2026/\1/\2.md)',s)
    s=s.replace('](../../../../notes/','](../../notes/')
    return s
def mmss(x):
    x=int(round(x)); h,m,s=x//3600,(x%3600)//60,x%60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
RT={'2117867158470599075':'Reply: heels lifted, the index finger bending with the breath',
'2121520137807556933':'Reply: thumb toward the little finger, then the index finger, then both together',
'2124110202287149064':'Reply: warmth at L2–L3, tension at T5',
'2125200655971447192':"Reply: notice the ribcage; don't control the breath",
'2125234376791461993':'Reply: T5 → solar plexus → lower dantian, with Om',
'2125134647520907272':'Reply: oxygen stored in the muscles',
'2125803981629018323':'Reply: the breath enters the heart from below',
'2120493794915443011':'Reply: kundalini as the Former Heaven original qi',
'2124333535507132564':'Reply: energy waking in Mingmen and running along the microtubules'}
def title_of(i):
    t,b,_=split(i)
    if t: return t
    if i in RT: return RT[i]
    w=re.sub(r'@\w+\s*','',b); w=re.sub(r'\s+',' ',w)
    return 'Reply: '+(w[:70].rsplit(' ',1)[0]+'…' if len(w)>70 else w)
os.makedirs(C,exist_ok=True); index=[]
for cl in clusters:
    slug=cl['slug']; d=f"{C}/{slug}"; os.makedirs(d,exist_ok=True)
    st=state['clusters'].get(slug,{}); clips={c['post_id']:c for c in st.get('clips',[])}
    dates=[kd(i) for i in cl['posts']]; dr=f"{min(dates):%b %-d} – {max(dates):%b %-d, %Y}"
    # README
    r=[f"# {cl['title']}",f"### {cl['native']}","",f"*A collection of {len(cl['posts'])} posts by 마리지천 摩利支天 ([@z9_s8_y_9](https://x.com/z9_s8_y_9)), {dr} (Korea time), translated from the Korean.*","",
       "## What this cluster teaches","",cl['overview'],"",
       "## Read and listen","",f"- **Full text:** [teaching.md](teaching.md), all {len(cl['posts'])} posts in reading order."]
    if st.get('full'): r.append(f"- **Full audio:** [audio/{st['full']}](audio/{st['full']}) ({mmss(st['full_duration'])}), narrated in English: an introduction, then every post in the order below, with 0.8 s between clips.")
    r+=["","## Posts, in reading order","","| # | Date (KST) | Post | Audio |","|---|---|---|---|"]
    for n,i in enumerate(cl['posts'],1):
        c=clips.get(i); a=f"[{mmss(c['duration'])}](audio/{c['file']})" if c else ''
        day=kd(i).date()
        r.append(f"| {n} | [{day}](../../graph/translated/{day:%Y/%m}/{day}.md) | [{title_of(i).replace('|','/')}]({U+i}) | {a} |")
    if cl['media']:
        r+=["","## Related diagrams and videos",""]+[f"- [{t}](../../{p})" for t,p in cl['media']]
    r+=["","## Notes","","- The translations are the same as in the day files under [graph/translated/](../../graph/translated/README.md); key terms follow the [glossary](../../graph/translated/GLOSSARY.md). Images attached to the posts are not stored.",
        "- Audio: Fish Audio TTS (model s2.1-pro, voice \"David\"), mp3 192 kbps mono, loudness-normalized. Each clip has its exact spoken script beside it as a `.txt` (Hangul and Hanja in parentheses are left out of the narration). Every clip was checked with Fish speech recognition for word recall of at least 0.85.",""]
    open(f"{d}/README.md",'w').write('\n'.join(r))
    # teaching.md
    t=[f"# {cl['title']}",f"### {cl['native']}","",f"*Posts by 마리지천 摩利支天 ([@z9_s8_y_9](https://x.com/z9_s8_y_9)), {dr} (KST), in reading order. Translated from the Korean; posts he wrote in English are reproduced as published. Bracketed italic notes are the translator's.*",""]
    for n,i in enumerate(cl['posts'],1):
        ti,body,main=split(i); day=kd(i)
        head=ti if ti else title_of(i)
        t+=["---","",f"## {n}. {head}",f"*{day:%b %-d, %Y} · [original post]({U+i})*" + (f" · [audio](audio/{clips[i]['file']})" if i in clips else ''),"",fixlinks(body),""]
    open(f"{d}/teaching.md",'w').write('\n'.join(t))
    index.append(dict(slug=slug,title=cl['title'],native_title=cl['native'],order=cl['n'],overview=cl['overview'],
        date_range=[str(min(dates).date()),str(max(dates).date())],post_ids=cl['posts'],
        posts=[dict(id=i,date_kst=str(kd(i).date()),title=title_of(i),url=U+i,audio=(f"audio/{clips[i]['file']}" if i in clips else None),
                    audio_duration=(clips[i]['duration'] if i in clips else None),script=(f"audio/{clips[i]['file'][:-4]}.txt" if i in clips else None)) for i in cl['posts']],
        audio=dict(intro=('audio/00-intro.mp3' if None in clips else None),intro_duration=(clips[None]['duration'] if None in clips else None),
                   full=(f"audio/{st['full']}" if st.get('full') else None),full_duration=st.get('full_duration'),
                   clips=[dict(file='audio/'+c['file'],post_id=c['post_id'],duration=c['duration']) for c in st.get('clips',[])]),
        related_media=[dict(title=a,path=p) for a,p in cl['media']],
        readme=f"collections/{slug}/README.md",teaching=f"collections/{slug}/teaching.md"))
json.dump(dict(generated=dt.datetime.now().isoformat(timespec='seconds'),source="https://x.com/z9_s8_y_9",
     voice=dict(provider='Fish Audio',model='s2.1-pro',voice='David',reference_id='72324f5951924b2eb27faaf5630153b4'),collections=index),
     open(C+'/index.json','w'),ensure_ascii=False,indent=1)
L=["# Collections","","The latest teachings of 마리지천 摩利支天 ([@z9_s8_y_9](https://x.com/z9_s8_y_9)), grouped by topic. Each collection has an overview, the full English text in reading order (`teaching.md`), and narrated audio: one clip per post plus a single full-length mp3. Machine-readable index for the website: [index.json](index.json).","",
   "| # | Collection | Posts | Dates (KST) | Full audio |","|---|---|---|---|---|"]
for x in index:
    fa=f"[{mmss(x['audio']['full_duration'])}]({x['slug']}/{x['audio']['full']})" if x['audio']['full'] else '(pending)'
    a,b=x['date_range']; L.append(f"| {x['order']} | [{x['title']}]({x['slug']}/README.md)<br>{x['native_title']} | {len(x['post_ids'])} | {a} to {b} | {fa} |")
L+=["","Source posts so far: Nov 2–27, 2026. Translations of every day, including posts not in any collection, are in [graph/translated/](../graph/translated/README.md).",""]
open(C+'/README.md','w').write('\n'.join(L))
print('ok',len(index))
