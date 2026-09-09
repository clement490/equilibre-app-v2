import json
from pathlib import Path
import argostranslate.package
import argostranslate.translate
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build'/'recipe_translations'; OUT.mkdir(parents=True,exist_ok=True)
argostranslate.package.update_package_index()
pkgs=argostranslate.package.get_available_packages(); pkg=next(p for p in pkgs if p.from_code=='en' and p.to_code=='fr')
langs=argostranslate.translate.get_installed_languages()
if not any(x.code=='fr' for x in langs): argostranslate.package.install_from_path(pkg.download())
langs=argostranslate.translate.get_installed_languages(); translator=next(x for x in langs if x.code=='en').get_translation(next(x for x in langs if x.code=='fr'))
def tr(s):
    s=str(s or '').strip(); return translator.translate(s) if s else ''
for idx in range(17):
    src=ROOT/'data'/'recipe_box_v2'/f'chunk_{idx:02d}.json'; out=OUT/f'chunk_{idx:02d}.json'
    if out.exists(): print('skip',idx); continue
    rows=json.loads(src.read_text()); result=[]
    for n,r in enumerate(rows,1):
        result.append({'source_name':r.get('source_name'),'source_recipe_id':r.get('source_recipe_id'),'title_fr':tr(r.get('title')),'ingredients_fr':[tr(x) for x in (r.get('ingredients') or [])],'instructions_fr':[tr(x) for x in (r.get('instructions') or [])]})
        if n%25==0: print(idx,n,flush=True)
    out.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))); print('done',idx,len(result),flush=True)
