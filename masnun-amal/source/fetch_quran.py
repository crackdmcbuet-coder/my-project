import json, urllib.request, re
API="https://api.quran.com/api/v4"
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl/8.5.0","Accept":"application/json"})) as r: return json.load(r)
def chapter(ch, tr):
    out=[]; page=1
    while True:
        d=get(f"{API}/verses/by_chapter/{ch}?translations={tr}&fields=text_indopak&per_page=50&page={page}")
        for v in d['verses']:
            t=v['translations'][0]['text']
            out.append({"key":v['verse_key'],"ar":v['text_indopak'],"bn":t})
        if d['pagination']['next_page'] is None: break
        page+=1
    return out
res={}
for tr in (161,213):
    for ch in (1,2,3,32,43,67,109,112,113,114):
        res[f"{tr}:{ch}"]=chapter(ch,tr)
json.dump(res,open("quran_raw.json","w"),ensure_ascii=False,indent=0)
