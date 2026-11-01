import sys,json,re,shutil,datetime
seg,fn=sys.argv[1],sys.argv[2]; t=open(fn).read()
ST='/workspace/gurumaxx/state.json'; st=json.load(open(ST))
m=re.search(r'(\d+) of 1000 today',t); mm=re.search(r'(\d+) of 30 this minute',t)
if m: st['reads_left_today']=int(m.group(1))
if mm: st['reads_left_minute']=int(mm.group(1))
if '"result_count":0' in t and '"errors"' not in t and '"detail"' not in t:
    s=st['segments'][seg]; s['done']=True; s['next_token']=None; s['fresh']=False; st['calls_used']+=1
    shutil.copy(fn,f'/workspace/gurumaxx/raw/pages/{seg}_{datetime.datetime.now():%Y%m%dT%H%M%S%f}.txt')
    print(seg,'EMPTY -> done')
else: print(seg,'ERROR/UNKNOWN:',t[:400])
json.dump(st,open(ST,'w'),indent=1,ensure_ascii=False)
