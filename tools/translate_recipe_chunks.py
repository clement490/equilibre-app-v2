import json
import os
import re
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "recipe_translations"
OUT.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("TRANSLATION_MODEL", "facebook/nllb-200-distilled-600M")
raw_chunks = os.environ.get("CHUNKS", "").strip()
chunk_indexes = [int(x.strip()) for x in raw_chunks.split(",") if x.strip()] if raw_chunks else list(range(17))

print(f"Worker chunks: {chunk_indexes}", flush=True)
print(f"Loading NLLB model: {MODEL}", flush=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained(MODEL, src_lang="eng_Latn", tgt_lang="fra_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL, torch_dtype=torch.float16 if device == "cuda" else torch.float32)
model = model.to(device).eval()
if device == "cuda":
    print("Using CUDA/FP16", flush=True)
else:
    print("Using CPU/FP32", flush=True)

cache = {}

def translate_batch(values):
    clean = [str(v).strip() if v is not None else "" for v in values]
    missing = [x for x in clean if x and x not in cache]
    if missing:
        for start in range(0, len(missing), 16):
            batch = missing[start:start + 16]
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
            with torch.inference_mode():
                tokens = model.generate(
                    **inputs,
                    forced_bos_token_id=tokenizer.convert_tokens_to_ids("fra_Latn"),
                    max_length=512,
                    num_beams=2,
                )
            outputs = tokenizer.batch_decode(tokens, skip_special_tokens=True)
            cache.update(zip(batch, outputs))
            print(f"Translated {min(start + 16, len(missing))}/{len(missing)} new strings", flush=True)
    return [cache.get(x, "") if x else "" for x in clean]

# Common culinary units. Ingredient-specific density is used when a volume must become grams.
UNIT_TO_ML = {
    "ml": 1.0, "milliliter": 1.0, "milliliters": 1.0,
    "l": 1000.0, "liter": 1000.0, "liters": 1000.0,
    "tsp": 4.92892, "teaspoon": 4.92892, "teaspoons": 4.92892,
    "tbsp": 14.7868, "tablespoon": 14.7868, "tablespoons": 14.7868,
    "fl oz": 29.5735, "fluid ounce": 29.5735, "fluid ounces": 29.5735,
    "cup": 236.588, "cups": 236.588,
    "pint": 473.176, "pints": 473.176,
    "quart": 946.353, "quarts": 946.353,
    "gallon": 3785.41, "gallons": 3785.41,
}
MASS_TO_G = {
    "g": 1.0, "gram": 1.0, "grams": 1.0,
    "kg": 1000.0, "kilogram": 1000.0, "kilograms": 1000.0,
    "oz": 28.3495, "ounce": 28.3495, "ounces": 28.3495,
    "lb": 453.592, "lbs": 453.592, "pound": 453.592, "pounds": 453.592,
}
DENSITY_G_PER_ML = {
    "water": 1.0, "milk": 1.03, "cream": 1.01, "heavy cream": 0.99,
    "olive oil": 0.91, "vegetable oil": 0.92, "canola oil": 0.92, "oil": 0.92,
    "honey": 1.42, "maple syrup": 1.32, "syrup": 1.32,
    "soy sauce": 1.06, "vinegar": 1.01, "lemon juice": 1.03, "lime juice": 1.03,
    "orange juice": 1.04, "yogurt": 1.03, "yoghurt": 1.03,
    "flour": 0.53, "all purpose flour": 0.53, "plain flour": 0.53,
    "whole wheat flour": 0.48, "sugar": 0.85, "brown sugar": 0.72,
    "powdered sugar": 0.56, "confectioners sugar": 0.56, "salt": 1.22,
    "rice": 0.85, "rolled oats": 0.40, "oats": 0.40,
    "breadcrumbs": 0.50, "bread crumbs": 0.50, "cocoa powder": 0.43,
    "cornstarch": 0.54, "corn starch": 0.54, "peanut butter": 1.06,
    "butter": 0.96, "mayonnaise": 0.91, "mustard": 1.01,
}

NUMBER = r"(?:\d+(?:\.\d+)?|\d+\s+\d+/\d+|\d+/\d+)"
UNIT_RE = re.compile(rf"^\s*(?P<qty>{NUMBER})\s+(?P<unit>[a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b(?P<rest>.*)$", re.I)
FRACTION = {"1/2": 0.5, "1/3": 1/3, "2/3": 2/3, "1/4": 0.25, "3/4": 0.75, "1/8": 0.125}

def parse_number(s):
    s = s.strip()
    if " " in s and "/" in s:
        a, b = s.split()
        return float(a) + parse_number(b)
    if s in FRACTION:
        return FRACTION[s]
    if "/" in s:
        a, b = s.split("/", 1)
        return float(a) / float(b)
    return float(s)

def density_for(rest):
    text = re.sub(r"[^a-z0-9 ]", " ", rest.lower())
    text = re.sub(r"\s+", " ", text).strip()
    for key in sorted(DENSITY_G_PER_ML, key=len, reverse=True):
        if key in text:
            return DENSITY_G_PER_ML[key]
    return None

def normalize_ingredient(source, translated):
    if not source:
        return translated
    m = UNIT_RE.match(source)
    if not m:
        return translated
    qty = parse_number(m.group("qty"))
    unit_raw = m.group("unit").strip().lower()
    rest = m.group("rest").strip()
    unit = unit_raw
    if unit in MASS_TO_G:
        grams = qty * MASS_TO_G[unit]
    elif unit in UNIT_TO_ML:
        density = density_for(rest)
        if density is None:
            return translated
        grams = qty * UNIT_TO_ML[unit] * density
    else:
        return translated
    grams_s = f"{grams:.0f} g"
    # Replace only the leading quantity/unit in the French translation.
    fr = re.sub(r"^\s*\d+(?:[.,]\d+)?(?:\s+\d+/\d+)?\s*(?:g|kg|ml|l|oz|lb|lbs|cup|cups|tbsp|tsp|teaspoon|tablespoon|ounce|pound|liter|liters|milliliter|milliliters)\b\s*", "", translated, count=1, flags=re.I)
    return f"{grams_s} {fr.strip()}".strip()

for idx in chunk_indexes:
    src = ROOT / "data" / "recipe_box_v2" / f"chunk_{idx:02d}.json"
    out = OUT / f"chunk_{idx:02d}.json"
    if out.exists():
        print(f"skip existing chunk {idx}", flush=True)
        continue
    rows = json.loads(src.read_text(encoding="utf-8"))
    result = []
    for n, r in enumerate(rows, 1):
        title = translate_batch([r.get("title")])[0]
        source_ingredients = r.get("ingredients") if isinstance(r.get("ingredients"), list) else [r.get("ingredients")]
        source_instructions = r.get("instructions") if isinstance(r.get("instructions"), list) else [r.get("instructions")]
        ingredients_fr = translate_batch(source_ingredients)
        ingredients_fr = [normalize_ingredient(src_i, fr_i) for src_i, fr_i in zip(source_ingredients, ingredients_fr)]
        instructions_fr = translate_batch(source_instructions)
        result.append({
            "source_name": r.get("source_name"),
            "source_recipe_id": r.get("source_recipe_id"),
            "title_fr": title,
            "ingredients_fr": ingredients_fr,
            "instructions_fr": instructions_fr,
        })
        if n % 25 == 0:
            print(f"chunk {idx}: {n}/{len(rows)} recipes", flush=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(out)
    print(f"DONE chunk {idx}: {len(result)} recipes", flush=True)

print(f"Worker complete. Cache entries: {len(cache)}", flush=True)
