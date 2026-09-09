import json
import os
from pathlib import Path

import argostranslate.package
import argostranslate.translate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "recipe_translations"
OUT.mkdir(parents=True, exist_ok=True)

raw_chunks = os.environ.get("CHUNKS", "").strip()
chunk_indexes = [int(x.strip()) for x in raw_chunks.split(",") if x.strip()] if raw_chunks else list(range(17))
print(f"Worker chunks: {chunk_indexes}", flush=True)

print("Updating Argos package index...", flush=True)
argostranslate.package.update_package_index()
pkg = next(p for p in argostranslate.package.get_available_packages() if p.from_code == "en" and p.to_code == "fr")
langs = argostranslate.translate.get_installed_languages()
en = next(x for x in langs if x.code == "en")
fr = next((x for x in langs if x.code == "fr"), None)
if fr is None:
    print("Installing EN->FR model...", flush=True)
    argostranslate.package.install_from_path(pkg.download())
    langs = argostranslate.translate.get_installed_languages()
    en = next(x for x in langs if x.code == "en")
    fr = next(x for x in langs if x.code == "fr")
translator = en.get_translation(fr)
print("EN->FR model ready.", flush=True)

cache = {}
def tr(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if not value:
        return ""
    if value not in cache:
        cache[value] = translator.translate(value)
    return cache[value]

def translate_sequence(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [tr(x) for x in value]
    return [tr(value)]

for idx in chunk_indexes:
    src = ROOT / "data" / "recipe_box_v2" / f"chunk_{idx:02d}.json"
    out = OUT / f"chunk_{idx:02d}.json"
    if out.exists():
        print(f"skip existing chunk {idx}", flush=True)
        continue
    rows = json.loads(src.read_text(encoding="utf-8"))
    result = []
    for n, r in enumerate(rows, 1):
        result.append({
            "source_name": r.get("source_name"),
            "source_recipe_id": r.get("source_recipe_id"),
            "title_fr": tr(r.get("title")),
            "ingredients_fr": translate_sequence(r.get("ingredients")),
            "instructions_fr": translate_sequence(r.get("instructions")),
        })
        if n % 25 == 0:
            print(f"chunk {idx}: {n}/{len(rows)} recipes", flush=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(out)
    print(f"DONE chunk {idx}: {len(result)} recipes", flush=True)

print(f"Worker complete. Cache entries: {len(cache)}", flush=True)
