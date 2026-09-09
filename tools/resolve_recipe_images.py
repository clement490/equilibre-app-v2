import concurrent.futures, json, re
from pathlib import Path
from urllib.parse import quote, urlparse
import requests
from bs4 import BeautifulSoup

DOMAINS={"ar":"allrecipes.com","epi":"epicurious.com","fn":"foodnetwork.com"}
PUNCH={"ar":"Allrecipes","epi":"Epicurious","fn":"Food-Network"}
OUT=Path("build/recipe_image_map.json")
TIMEOUT=8
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"

def norm(s): return re.sub(r"[^a-z0-9]+"," ",(s or "").lower()).strip()
def tokens(s): return {x for x in norm(s).split() if len(x)>2}

def selected_rows():
    corpus=Path("data/recipe_box_v2/equilibre_selected_v2.ndjson")
    if corpus.exists() and corpus.stat().st_size>1000:
        rows=[json.loads(x) for x in corpus.read_text(encoding="utf-8").splitlines() if x.strip()]
        if len(rows)>=8000: return rows
    rows=[]
    for p in sorted(Path("data/recipe_box_v2").glob("chunk_*.json")):
        rows.extend(json.loads(p.read_text(encoding="utf-8")))
    if len(rows)!=8043: raise SystemExit(f"Expected 8043 selected rows, found {len(rows)}")
    return rows

def get(url, ms=TIMEOUT):
    return requests.get(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"},timeout=ms,allow_redirects=True)

def recipe_metadata(html):
    soup=BeautifulSoup(html,"html.parser"); title=""; image=""; ingredients=[]
    for attrs in ({"property":"og:title"},{"name":"twitter:title"}):
        tag=soup.find("meta",attrs=attrs)
        if tag and tag.get("content"): title=tag["content"]; break
    for attrs in ({"property":"og:image"},{"name":"twitter:image"}):
        tag=soup.find("meta",attrs=attrs)
        if tag and tag.get("content"): image=tag["content"]; break
    for script in soup.find_all("script",type="application/ld+json"):
        try:
            obj=json.loads(script.string or script.get_text()); objs=obj if isinstance(obj,list) else [obj]
            for o in objs:
                if isinstance(o,dict) and (o.get("@type")=="Recipe" or "Recipe" in (o.get("@type") or [])):
                    title=title or o.get("name",""); im=o.get("image",""); image=image or (im[0] if isinstance(im,list) and im else im); ingredients.extend(o.get("recipeIngredient",[]) or [])
        except Exception: pass
    return norm(title),image,[norm(x) for x in ingredients]

def punchfork(row):
    slug=re.sub(r"[^a-z0-9]+","-",row["title"].strip(),flags=re.I).strip("-")
    url=f"https://www.punchfork.com/recipe/{slug}-{PUNCH[row['source_name']]}"
    try:
        r=get(url)
        if r.status_code!=200:return None
        pt,image,_=recipe_metadata(r.text)
        if not image.startswith("http"):return None
        nt,tt=norm(row["title"]),tokens(row["title"]); score=1.0 if pt==nt else len(tt&tokens(pt))/max(1,len(tt))
        if score<0.75:return None
        return {"source_recipe_id":row["source_recipe_id"],"source_name":row["source_name"],"title":row["title"],"image_url":image,"page_url":url,"score":round(score,4),"provider":"punchfork-source-index"}
    except Exception:return None

def search_links(source,title):
    domain=DOMAINS[source]; q=quote(f'site:{domain} "{title}"'); out=[]
    urls=[f"https://www.google.com/search?q={q}&num=10",f"https://www.bing.com/search?q={q}&count=10"]
    for su in urls:
        try:
            soup=BeautifulSoup(get(su,6).text,"html.parser")
            for a in soup.select("a[href]"):
                href=a.get("href","")
                if href.startswith("/url?q="): href=href[7:].split("&",1)[0]
                if href.startswith("http") and domain in urlparse(href).netloc and href not in out: out.append(href)
            if out: break
        except Exception: continue
    return out[:5]

def resolve(row):
    direct=punchfork(row)
    if direct:return direct
    source,title=row["source_name"],row["title"]; nt,tt=norm(title),tokens(title); best=None
    for page in search_links(source,title):
        try:
            r=get(page,6)
            if r.status_code!=200:continue
            pt,image,ings=recipe_metadata(r.text)
            if not image.startswith("http"):continue
            title_score=1.0 if pt==nt else len(tt&tokens(pt))/max(1,len(tt))
            if title_score<0.75:continue
            wanted=tokens(" ".join(row.get("ingredients",[]))); page_ing=tokens(" ".join(ings)); ingredient_score=len(wanted&page_ing)/max(1,min(20,len(wanted))); score=title_score*.75+ingredient_score*.25
            cand={"source_recipe_id":row["source_recipe_id"],"source_name":source,"title":title,"image_url":image,"page_url":page,"score":round(score,4),"provider":"source-search"}
            if best is None or score>best["score"]:best=cand
        except Exception:continue
    return best

def main():
    rows=selected_rows(); print(f"Resolving {len(rows)} selected recipe images",flush=True)
    results=[]; failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=48) as ex:
        futs={ex.submit(resolve,r):r for r in rows}
        for i,fut in enumerate(concurrent.futures.as_completed(futs),1):
            row=futs[fut]
            try:x=fut.result()
            except Exception:x=None
            (results if x else failures).append(x or {"source_recipe_id":row["source_recipe_id"],"source_name":row["source_name"],"title":row["title"]})
            if i%100==0:print(i,"resolved",len(results),"failed",len(failures),flush=True)
    results.sort(key=lambda x:x["source_recipe_id"]); failures.sort(key=lambda x:x["source_recipe_id"])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"version":4,"total":len(rows),"resolved":len(results),"failed":len(failures),"results":results,"failures":failures},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("DONE",len(results),"resolved",len(failures),"failed",flush=True)
    if len(results)<len(rows)*.8: raise SystemExit("Too few images resolved; refusing to publish a poor map")

if __name__=="__main__":main()
