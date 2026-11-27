import re
CJK=r'\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u4dc0-\u4dff\u2630-\u2637\u3000-\u303f\uff00-\uffef'
SPECIAL={
 '2118202700626288779':[('The character 炁 (qi; 既 → 無 + 灬) is not the ordinary 氣 (qi) of breathing.','The Daoist character for qi that is written with fire under nothing is not the ordinary character for the qi of breathing.'),
   ('The very shape of the character, "fire" (灬) placed beneath "nothing" (無),','The very shape of the character, "fire" placed beneath "nothing",'),
   ('as 氣, we distinguish','with the ordinary character, we distinguish'),('by writing it 炁.','by writing it with the character of fire under nothing.'),
   ('the upper "無"','the upper "nothing"'),('The character 炁: fire inside nothingness','The character for qi with fire under nothing: fire inside nothingness'),('this "Ding fire inside nothingness."','this "Ding fire inside nothingness."')],
}
def clean_paren(m):
    inner=m.group(1)
    t=re.sub('['+CJK+']+','',inner)
    t=re.sub(r'\s*[;:·,/]\s*(?=[;:·,/]|$)','',t)
    t=re.sub(r'^[\s;:·,/=+→➔\-]+|[\s;:·,/=+→➔\-]+$','',t)
    t=re.sub(r'\s{2,}',' ',t)
    if not re.search(r'[A-Za-z0-9]',t): return ''
    return ' ('+t+')'
def spoken(md,pid=None):
    s=md
    for a,b in SPECIAL.get(pid,[]): s=s.replace(a,b)
    s=re.sub(r"^\*\(Translator's note.*?\)\*\s*$",'',s,flags=re.M|re.S)
    s=re.sub(r"\*\(cut off by X\)\*",'',s)
    s=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',s)
    s=s.replace('**','')
    s=re.sub(r'^\[([^\]]+)\]\s*',r'\1: ',s,flags=re.M)
    s=re.sub(r'\[([^\]]+)\]',r'\1',s)
    s=re.sub(r'@\w+\s*','',s)
    # parentheticals (allow one level nesting by repeating)
    for _ in range(2): s=re.sub(r'\s*\(([^()]*)\)',clean_paren,s)
    s=re.sub('['+CJK+']+','',s)
    s=re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF]+(?<![→➔↔])','',s) if False else s
    rep=[('↔',' and '),('→',' to '),('➔',' to '),('⇒',' to '),(' > ',', then '),('＞',' then '),
         ('mmHg',' millimeters of mercury'),('CO2','carbon dioxide'),('co2','carbon dioxide'),('•','')]
    for a,b in rep: s=s.replace(a,b)
    s=re.sub(r'(\d)\s*[–~-]\s*(\d)',r'\1 to \2',s)
    s=re.sub(r'([LTC]\d)\s*[–-]\s*([LTC]\d)',r'\1 to \2',s)
    s=re.sub(r'(\d)\s?cm\b',r'\1 centimeters',s)
    s=re.sub(r'\b(L|T|C)(\d)\b',r'\1 \2',s)
    s=re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2705\u26A1]','',s)
    s=re.sub(r'\b(Hahaha|Haha|haha|lol)\b[.,!]*','',s)
    s=re.sub(r'\^\^|~+|[*#]','',s)
    s=re.sub(r'\.{2,}\s*(?=[a-z])',', ',s)
    s=re.sub(r'\.{2,}','.',s)
    s=s.replace(' + ',' and ')
    s=re.sub(r'[ \t]+',' ',s)
    s=re.sub(r' ([,.;:!?])',r'\1',s)
    s=re.sub(r',\s*([.;:!?])',r'\1',s)
    s=re.sub(r'\(\s*\)','',s)
    s=re.sub(r'""|“”','',s)
    s='\n'.join(l.strip() for l in s.split('\n'))
    s=re.sub(r'\n{3,}','\n\n',s).strip()
    return s
