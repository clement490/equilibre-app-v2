import json
import os
import re
from pathlib import Path

import argostranslate.package
import argostranslate.translate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "recipe_translations"
OUT.mkdir(parents=True, exist_ok=True)

UNIT_FACTORS = {
    "cup": (240.0, "ml"), "cups": (240.0, "ml"),
    "tablespoon": (15.0, "ml"), "tablespoons": (15.0, "ml"), "tbsp": (15.0, "ml"),
    "teaspoon": (5.0, "ml"), "teaspoons": (5.0, "ml"), "tsp": (5.0, "ml"),
    "fluid ounce": (29.57, "ml"), "fluid ounces": (29.57, "ml"),
    "ounce": (28.35, "g"), "ounces": (28.35, "g"), "oz": (28.35, "g"),
    "pound": (453.592, "g"), "pounds": (453.592, "g"), "lb": (453.592, "g"), "lbs": (453.592, "g"),
    "pint": (473.176, "ml"), "pints": (473.176, "ml"),
    "quart": (946.353, "ml"), "quarts": (946.353, "ml"),
    "gallon": (3.78541, "l"), "gallons": (3.78541, "l"),
    "inch": (2.54, "cm"), "inches": (2.54, "cm"),
}
NUMBER = r"(?:\d+(?:\.\d+)?|\d+\s+\d+/\d+|\d+/\d+)"


def parse_number(value: str) -> float:
    value = value.strip()
    if " " in value and "/" in value:
        whole, frac = value.split(None, 1)
        a, b = frac.split("/", 1)
        return float(whole) + float(a) / float(b)
    if "/" in value:
        a, b = value.split("/", 1)
        return float(a) / float(b)
    return float(value)


def fmt_number(value: float) -> str:
    if value >= 1000:
        return f"{value:.0f}"
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def convert_units(text: str) -> str:
    text = str(text or "")
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*degrees?\s*F(?:ahrenheit)?\s*\(\s*(\d+(?:\.\d+)?)\s*degrees?\s*C(?:elsius)?\s*\)",
        lambda m: f"{m.group(2)} °C", text, flags=re.I)
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*°\s*F\s*\(\s*(\d+(?:\.\d+)?)\s*°\s*C\s*\)",
        lambda m: f"{m.group(2)} °C", text, flags=re.I)

    def temp_repl(m):
        return f"{round((float(m.group(1)) - 32) * 5 / 9)} °C"

    text = re.sub(r"(\d+(?:\.\d+)?)\s*degrees?\s*F(?:ahrenheit)?\b", temp_repl, text, flags=re.I)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\s*F\b", temp_repl, text, flags=re.I)

    def dimension_repl(m):
        return f"{fmt_number(float(m.group(1)) * 2.54)} x {fmt_number(float(m.group(2)) * 2.54)} cm"

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:inch|inches|in)\b",
        dimension_repl, text, flags=re.I)

    unit_pattern = "|".join(sorted((re.escape(k) for k in UNIT_FACTORS), key=len, reverse=True))
    pattern = re.compile(rf"(?P<num>{NUMBER})\s+(?P<unit>{unit_pattern})\b", re.I)

    def unit_repl(m):
        value = parse_number(m.group("num")) * UNIT_FACTORS[m.group("unit").lower()][0]
        target = UNIT_FACTORS[m.group("unit").lower()][1]
        if target == "ml" and value >= 1000:
            value /= 1000
            target = "l"
        return f"{fmt_number(value)} {target}"

    return pattern.sub(unit_repl, text)


# Translate only the requested chunks. The workflow splits the 17 chunks across
# several workers so a single long-running process cannot hold the whole corpus.
raw_chunks = os.environ.get("CHUNKS", "").strip()
if raw_chunks:
    chunk_indexes = [int(x.strip()) for x in raw_chunks.split(",") if x.strip()]
else:
    chunk_indexes = list(range(17))

print(f"Worker chunks: {chunk_indexes}", flush=True)

# Argos' package index/model is installed once per worker, then reused for all
# chunks handled by that worker.
print("Updating Argos package index...", flush=True)
argostranslate.package.update_package_index()
pkg = next(
    p for p in argostranslate.package.get_available_packages()
    if p.from_code == "en" and p.to_code == "fr"
)
langs = argostranslate.translate.get_installed_languages()
if not any(x.code == "fr" for x in langs):
    print("Installing EN->FR model...", flush=True)
    argostranslate.package.install_from_path(pkg.download())
langs = argostranslate.translate.get_installed_languages()
translator = next(x for x in langs if x.code == "en").get_translation(
    next(x for x in langs if x.code == "fr")
)
print("EN->FR model ready.", flush=True)

# Cache repeated strings aggressively. Ingredient phrases repeat heavily across
# the corpus; translating each occurrence independently wastes most of the time.
translation_cache = {}

def tr(s: str) -> str:
    s = str(s or "").strip()
    if not s:
        return ""
    if s not in translation_cache:
        translation_cache[s] = translator.translate(s)
    return translation_cache[s]

for idx in chunk_indexes:
    src = ROOT / "data" / "recipe_box_v2" / f"chunk_{idx:02d}.json"
    out = OUT / f"chunk_{idx:02d}.json"
    if out.exists():
        print(f"skip existing chunk {idx}", flush=True)
        continue

    rows = json.loads(src.read_text())
    result = []
    for n, r in enumerate(rows, 1):
        ingredients = [convert_units(x) for x in (r.get("ingredients") or [])]
        instructions = convert_units(r.get("instructions") or "")
        result.append({
            "source_name": r.get("source_name"),
            "source_recipe_id": r.get("source_recipe_id"),
            "title_fr": tr(r.get("title")),
            "ingredients_fr": [tr(x) for x in ingredients],
            "instructions_fr": tr(instructions),
        })
        if n % 25 == 0:
            print(f"chunk {idx}: {n}/{len(rows)} recipes", flush=True)

    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    tmp.replace(out)
    print(f"DONE chunk {idx}: {len(result)} recipes", flush=True)

print(f"Worker complete. Cache entries: {len(translation_cache)}", flush=True)
