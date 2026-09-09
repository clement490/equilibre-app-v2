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
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
)
model = model.to(device).eval()
print(f"Using {'CUDA/FP16' if device == 'cuda' else 'CPU/FP32'}", flush=True)

cache = {}


def translate_batch(values):
    clean = [str(v).strip() if v is not None else "" for v in values]
    missing = [x for x in clean if x and x not in cache]
    if missing:
        for start in range(0, len(missing), 16):
            batch = missing[start:start + 16]
            inputs = tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)
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


# Équilibre culinary rules: these are intentionally user-facing French kitchen values,
# not exact US physical-volume conversions.
US_VOLUME_ML = {
    "cup": 240.0, "cups": 240.0,
    "pint": 480.0, "pints": 480.0,
    "quart": 960.0, "quarts": 960.0,
    "gallon": 3840.0, "gallons": 3840.0,
    "fl oz": 30.0, "fluid ounce": 30.0, "fluid ounces": 30.0,
    "tbsp": 15.0, "tablespoon": 15.0, "tablespoons": 15.0,
    "tsp": 5.0, "teaspoon": 5.0, "teaspoons": 5.0,
    "ml": 1.0, "milliliter": 1.0, "milliliters": 1.0,
    "l": 1000.0, "liter": 1000.0, "liters": 1000.0,
}
US_MASS_G = {
    "g": 1.0, "gram": 1.0, "grams": 1.0,
    "kg": 1000.0, "kilogram": 1000.0, "kilograms": 1000.0,
    "oz": 28.3495, "ounce": 28.3495, "ounces": 28.3495,
    "lb": 453.592, "lbs": 453.592, "pound": 453.592, "pounds": 453.592,
}

# Explicit values required by the Équilibre specification.
CUP_SOLID_G = {
    "all purpose flour": 120.0,
    "plain flour": 120.0,
    "flour": 120.0,
    "whole wheat flour": 120.0,
    "sugar": 200.0,
    "granulated sugar": 200.0,
    "white sugar": 200.0,
    "brown sugar": 220.0,
    "powdered sugar": 120.0,
    "confectioners sugar": 120.0,
    "butter": 225.0,
}

# Generic densities are only a fallback for solid ingredients not covered explicitly.
DENSITY_G_PER_ML = {
    "water": 1.00, "milk": 1.03, "cream": 1.01, "heavy cream": 0.99,
    "olive oil": 0.91, "vegetable oil": 0.92, "canola oil": 0.92, "oil": 0.92,
    "honey": 1.42, "maple syrup": 1.32, "syrup": 1.32,
    "soy sauce": 1.06, "vinegar": 1.01, "lemon juice": 1.03, "lime juice": 1.03,
    "orange juice": 1.04, "yogurt": 1.03, "yoghurt": 1.03,
    "salt": 1.22, "rice": 0.85, "rolled oats": 0.40, "oats": 0.40,
    "breadcrumbs": 0.50, "bread crumbs": 0.50, "cocoa powder": 0.43,
    "cornstarch": 0.54, "corn starch": 0.54, "peanut butter": 1.06,
    "mayonnaise": 0.91, "mustard": 1.01,
    "chopped onion": 0.68, "onion": 0.68, "chopped tomato": 0.76, "tomato": 0.76,
    "shredded cheese": 0.42, "grated cheese": 0.42, "cheese": 0.42,
    "chopped carrot": 0.64, "carrot": 0.64, "chopped celery": 0.50, "celery": 0.50,
}

NUMBER = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
UNIT_NAMES = sorted(US_VOLUME_ML | US_MASS_G, key=len, reverse=True)
UNIT_RE = re.compile(
    rf"^\s*(?P<qty>{NUMBER})\s+(?P<unit>{'|'.join(re.escape(x) for x in UNIT_NAMES)})\b(?P<rest>.*)$",
    re.I,
)
FRACTION = {"1/2": 0.5, "1/3": 1/3, "2/3": 2/3, "1/4": 0.25, "3/4": 0.75, "1/8": 0.125}


def parse_number(s):
    s = s.strip().replace(",", ".")
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


def solid_cup_grams(rest):
    text = re.sub(r"[^a-z0-9 ]", " ", rest.lower())
    text = re.sub(r"\s+", " ", text).strip()
    for key in sorted(CUP_SOLID_G, key=len, reverse=True):
        if key in text:
            return CUP_SOLID_G[key]
    density = density_for(rest)
    return density * 240.0 if density is not None else None


def strip_translated_quantity(text):
    return re.sub(
        r"^\s*[\d\s/.,]+\s*(?:g|kg|mg|ml|cl|l|oz|lb|lbs|cup|cups|tasse|tasses|tbsp|tsp|c\.?\s*[àa]\.?\s*soupe|cuillère(?:s)?\s*[àa]\.?\s*soupe|c\.?\s*[àa]\.?\s*café|cuillère(?:s)?\s*[àa]\.?\s*café|teaspoon(?:s)?|tablespoon(?:s)?|ounce(?:s)?|pound(?:s)?|liter(?:s)?|litre(?:s)?|milliliter(?:s)?|millilitre(?:s)?)\b\s*",
        "",
        text,
        count=1,
        flags=re.I,
    ).strip()


def normalize_ingredient(source, translated):
    if not source or not translated:
        return translated
    m = UNIT_RE.match(source)
    if not m:
        return translated
    qty = parse_number(m.group("qty"))
    unit = m.group("unit").strip().lower()
    rest = m.group("rest").strip()

    if unit in US_MASS_G:
        grams = qty * US_MASS_G[unit]
        return f"{grams:.0f} g {strip_translated_quantity(translated)}".strip()

    if unit in {"cup", "cups"}:
        solid = solid_cup_grams(rest)
        if solid is not None:
            # Round to the nearest 5 g; this gives 1/2 cup butter = 115 g.
            grams = round((qty * solid) / 5.0) * 5
            return f"{grams:.0f} g {strip_translated_quantity(translated)}".strip()
        # Unknown cup ingredient: leave for later nutrition/density enrichment rather than inventing.
        density = density_for(rest)
        if density is not None:
            grams = round((qty * 240.0 * density) / 5.0) * 5
            return f"{grams:.0f} g {strip_translated_quantity(translated)}".strip()
        return translated

    if unit in US_VOLUME_ML:
        ml = qty * US_VOLUME_ML[unit]
        # tbsp/tsp/cup liquids are expressed in ml. Keep the user's 15/5/240 rules exact.
        if unit in {"cup", "cups", "pint", "pints", "quart", "quarts", "gallon", "gallons", "fl oz", "fluid ounce", "fluid ounces", "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon", "teaspoons"}:
            amount = round(ml)
            return f"{amount} ml {strip_translated_quantity(translated)}".strip()
        amount = round(ml)
        return f"{amount} ml {strip_translated_quantity(translated)}".strip()

    return translated


# Convert every Fahrenheit temperature appearing in instructions/descriptions/notes.
TEMP_RE = re.compile(
    r"(?P<temp>\d+(?:[.,]\d+)?)\s*(?:°\s*)?(?:F|Fahrenheit|degrees?\s*F)\b",
    re.I,
)


def fahrenheit_to_celsius(text):
    if not text:
        return text

    def repl(match):
        f = float(match.group("temp").replace(",", "."))
        c = (f - 32.0) * 5.0 / 9.0
        rounded = int(round(c / 10.0) * 10)
        return f"{rounded} °C"

    return TEMP_RE.sub(repl, text)


def normalize_text(text):
    if not text:
        return text
    return fahrenheit_to_celsius(text)


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
        description = translate_batch([r.get("description")])[0] if r.get("description") else ""

        source_ingredients = r.get("ingredients") if isinstance(r.get("ingredients"), list) else [r.get("ingredients")]
        source_ingredients = [x for x in source_ingredients if x]
        ingredients_fr = translate_batch(source_ingredients)
        ingredients_fr = [
            normalize_ingredient(src_i, fr_i)
            for src_i, fr_i in zip(source_ingredients, ingredients_fr)
        ]

        source_instructions = r.get("instructions") if isinstance(r.get("instructions"), list) else [r.get("instructions")]
        source_instructions = [x for x in source_instructions if x]
        instructions_fr = translate_batch(source_instructions)
        instructions_fr = [normalize_text(x) for x in instructions_fr]

        notes_source = r.get("notes")
        if isinstance(notes_source, list):
            notes_fr = [normalize_text(x) for x in translate_batch(notes_source) if x]
        elif notes_source:
            notes_fr = normalize_text(translate_batch([notes_source])[0])
        else:
            notes_fr = ""

        result.append({
            "source_name": r.get("source_name"),
            "source_recipe_id": r.get("source_recipe_id"),
            "title_fr": normalize_text(title),
            "description_fr": normalize_text(description),
            "ingredients_fr": ingredients_fr,
            "instructions_fr": instructions_fr,
            "notes_fr": notes_fr,
        })

        if n % 25 == 0:
            print(f"chunk {idx}: {n}/{len(rows)} recipes", flush=True)

    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(out)
    print(f"DONE chunk {idx}: {len(result)} recipes", flush=True)

print(f"Worker complete. Cache entries: {len(cache)}", flush=True)
