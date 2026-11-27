#!/usr/bin/env python3
"""Fish Audio narration for li-gong collections. Resumable via /workspace/gurumaxx/collections_state.json. Never prints the key."""
import json,os,re,sys,subprocess,time,urllib.request,urllib.error,collections,threading,datetime as dt
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); from spoken import spoken
B='/workspace/gurumaxx'; REPO='/workspace/li-gong-repo'; ST=B+'/collections_state.json'
KEY=os.environ['FISH_API_KEY']; VOICE='72324f5951924b2eb27faaf5630153b4'; MODEL='s2.1-pro'
LEAD='[calm, unhurried, contemplative teacher reading a meditation text]'
tx=json.load(open(B+'/coll/tx_full.json')); clusters=json.load(open(B+'/coll/clusters.json'))
raw={}
for l in open(B+'/raw/posts.jsonl'):
    p=json.loads(l); raw[p['id']]=p
K=dt.timezone(dt.timedelta(hours=9))
def kdate(i): return dt.datetime.fromisoformat(raw[i]['created_at'].replace('Z','+00:00')).astimezone(K)
lock=threading.Lock()
state=json.load(open(ST)) if os.path.exists(ST) else {'chars_sent':0,'tts_calls':0,'asr_calls':0,'chunks':{},'clusters':{},'errors':[]}
def save():
    with lock: json.dump(state,open(ST,'w'),indent=1,ensure_ascii=False)
class Billing(Exception): pass
def tts(text):
    body=dict(text=text,reference_id=VOICE,format='mp3',mp3_bitrate=192,normalize=True,temperature=0.88,top_p=0.85,
              prosody=dict(speed=1,volume=0,normalize_loudness=True),latency='normal')
    for a in range(4):
        req=urllib.request.Request('https://api.fish.audio/v1/tts',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json','model':MODEL})
        with lock: state['chars_sent']+=len(text); state['tts_calls']+=1
        try:
            with urllib.request.urlopen(req,timeout=300) as r: return r.read()
        except urllib.error.HTTPError as e:
            msg=e.read()[:300].decode('utf-8','replace')
            if e.code in (401,402,403) or re.search(r'credit|balance|quota|payment|insufficient',msg,re.I): raise Billing(f'{e.code} {msg}')
            state['errors'].append(f'tts {e.code} {msg}'); time.sleep(5*(a+1))
        except Exception as e:
            state['errors'].append(f'tts exc {e}'); time.sleep(5*(a+1))
    raise RuntimeError('tts failed 4x')
def asr(f):
    for a in range(4):
        with lock: state['asr_calls']+=1
        o=subprocess.run(['curl','-s','--max-time','300','-H','Authorization: Bearer '+KEY,'-F','audio=@'+f,'-F','language=en',
                          '-F','ignore_timestamps=true','https://api.fish.audio/v1/asr'],capture_output=True).stdout
        try: return json.loads(o)['text']
        except Exception: time.sleep(4*(a+1))
    return ''
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
def words(s): return re.findall(r"[a-z0-9]+",s.lower().replace("’","'").replace("'",""))
def recall(ref,hyp):
    r=collections.Counter(words(ref)); h=collections.Counter(words(hyp))
    n=sum(r.values()); return sum(min(c,h[w]) for w,c in r.items())/max(n,1), n
def is_heading(p): return len(p)<120 and not re.search(r'[.!?:;)"”]$',p) and '\n' not in p
def build_script(i,title_override=None):
    t=tx[i]; title,_,body=t[2:].partition('\n') if t.startswith('# ') else (None,None,t)
    sp_body=spoken(body,i); sp_title=spoken(title,i) if title else None
    if i=='2118202700626288779': sp_title='The character for qi with fire under nothing: fire inside nothingness'
    d=kdate(i); when=f"{d:%B} {d.day}"
    paras=[p for p in sp_body.split('\n\n') if p.strip()]
    out=[]
    for k,p in enumerate(paras):
        p=p.replace('\n',' ' if not is_heading(p.split('\n')[0]) else '\n')
        if is_heading(p.split('\n')[0]): p=p.rstrip()+'.'
        if k>0 and is_heading(p.split('\n')[0].rstrip('.')): out.append('[break] '+p)
        else: out.append(p)
    head=(f"{sp_title.rstrip('.')}. A post from {when}." if sp_title else f"A reply from {when}.")
    return head, out
def chunks(head,paras,limit=3300):
    cs=[]; cur=[head,'[break]']
    for p in paras:
        if sum(len(x) for x in cur)+len(p)>limit and len(cur)>0 and cur!=[head,'[break]']:
            cs.append(cur); cur=[]
        cur.append(p)
    cs.append(cur)
    return [LEAD+' '+'\n\n'.join(c).replace('\n\n[break]\n\n',' [break] ') for c in cs]
def plain(s): return re.sub(r'\[[^\]]*\]','',s)
def render_chunk(key,text,outf):
    c=state['chunks'].get(key)
    if c and c.get('ok') and c.get('text')==text and os.path.exists(outf): return c
    best=None
    for att in range(3):
        b=tts(text); open(outf,'wb').write(b)
        d=dur(outf); heard=asr(outf); rc,n=recall(plain(text),heard); spw=d/max(n,1)
        rec=dict(text=text,chars=len(text),dur=round(d,2),recall=round(rc,3),words=n,spw=round(spw,3),attempt=att+1,heard=heard[:20000])
        rec['ok']= rc>=0.85 and 0.25<=spw<=0.75
        print(f"  {key} att{att+1} {d:.1f}s recall={rc:.3f} spw={spw:.2f} ok={rec['ok']}",flush=True)
        if best is None or rec['recall']>best['recall']:
            best=rec; os.replace(outf,outf+'.best.mp3')
        if rec['ok']: break
    os.replace(outf+'.best.mp3',outf)
    with lock: state['chunks'][key]=best
    save(); return best
def concat(parts,gap,outf,loudnorm=True):
    tmp=outf+'.list.txt'; sil=f'/tmp/sil_{gap}.wav'
    if not os.path.exists(sil): subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','anullsrc=r=44100:cl=mono','-t',str(gap),sil],check=True)
    wavs=[]
    for p in parts:
        w=p+'.wav'; subprocess.run(['ffmpeg','-y','-v','error','-i',p,'-ac','1','-ar','44100',w],check=True); wavs.append(w)
    with open(tmp,'w') as f:
        for k,w in enumerate(wavs):
            if k: f.write(f"file '{sil}'\n")
            f.write(f"file '{w}'\n")
    af=['-af','loudnorm=I=-16:TP=-1.5:LRA=11'] if loudnorm else []
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',tmp]+af+['-ar','44100','-ac','1','-c:a','libmp3lame','-b:a','192k',outf],check=True)
    for w in wavs: os.remove(w)
    os.remove(tmp)
def do_post(cl,n,i,adir,tmpd):
    head,paras=build_script(i); cs=chunks(head,paras)
    name=f"{n:02d}-{i}"; parts=[]
    for k,c in enumerate(cs):
        f=f"{tmpd}/{name}-c{k}.mp3"; render_chunk(f"{cl['slug']}/{name}/c{k}",c,f); parts.append(f)
    out=f"{adir}/{name}.mp3"
    concat(parts,0.6,out)
    open(f"{adir}/{name}.txt",'w').write('\n\n'.join(cs)+'\n')
    return dict(file=f"{name}.mp3",post_id=i,duration=round(dur(out),2),chunks=len(cs))
def do_cluster(cl,workers=4):
    slug=cl['slug']; adir=f"{REPO}/collections/{slug}/audio"; tmpd=f"{B}/coll/audio_tmp/{slug}"
    os.makedirs(adir,exist_ok=True); os.makedirs(tmpd,exist_ok=True)
    jobs=[(0,'intro')]+[(k+1,i) for k,i in enumerate(cl['posts'])]
    # intro
    intro=f"{LEAD} {cl['title']}. [break] {spoken(cl['overview'])} [break] {len(cl['posts'])} posts by Marici, translated from the Korean."
    res={}
    def run(job):
        n,i=job
        if i=='intro':
            f=f"{tmpd}/00-intro-c0.mp3"; render_chunk(f"{slug}/00-intro/c0",intro,f)
            out=f"{adir}/00-intro.mp3"; concat([f],0.6,out); open(f"{adir}/00-intro.txt",'w').write(intro+'\n')
            return n,dict(file='00-intro.mp3',post_id=None,duration=round(dur(out),2),chunks=1)
        return n,do_post(cl,n,i,adir,tmpd)
    with ThreadPoolExecutor(workers) as ex:
        for n,r in ex.map(run,jobs): res[n]=r
    files=[f"{adir}/{res[n]['file']}" for n in sorted(res)]
    full=f"{adir}/{slug}-full.mp3"; concat(files,0.8,full,loudnorm=False)
    cs={'clips':[res[n] for n in sorted(res)],'full':f"{slug}-full.mp3",'full_duration':round(dur(full),2),'done':True}
    with lock: state['clusters'][slug]=cs
    save(); return cs
if __name__=='__main__':
    want=sys.argv[1:]
    for cl in clusters:
        if want and cl['slug'] not in want: continue
        if state['clusters'].get(cl['slug'],{}).get('done') and not want: continue
        print('CLUSTER',cl['slug'],flush=True)
        try: r=do_cluster(cl)
        except Billing as e:
            state['errors'].append('BILLING '+str(e)); save(); print('BILLING STOP',e); sys.exit(2)
        print('DONE',cl['slug'],r['full_duration'],'chars_sent',state['chars_sent'],flush=True)
