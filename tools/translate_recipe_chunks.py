import json
import re
from pathlib import Path

import argostranslate.package
import argostranslate.translate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "recipe_translations"
OUT.mkdir(parents=True, exist_ok=True)

# Recipe Box uses US customary units. Équilibre displays metric/French units.
# These conversions are deliberately deterministic and applied BEFORE translation,
# so Argos never has to guess what a unit means.
UNIT_FACTORS = {
    "cup": (240.0, "ml"),
    "cups": (240.0, "ml"),
    "tablespoon": (15.0, "ml"),
    "tablespoons": (15.0, "ml"),
    "tbsp": (15.0, "ml"),
    "teaspoon": (5.0, "ml"),
    "teaspoons": (5.0, "ml"),
    "tsp": (5.0, "ml"),
    "fluid ounce": (29.57, "ml"),
    "fluid ounces": (29.57, "ml"),
    "ounce": (28.35, "g"),
    "ounces": (28.35, "g"),
    "oz": (28.35, "g"),
    "pound": (453.592, "g"),
    "pounds": (453.592, "g"),
    "lb": (453.592, "g"),
    "lbs": (453.592, "g"),
    "pint": (473.176, "ml"),
    "pints": (473.176, "ml"),
    "quart": (946.353, "ml"),
    "quarts": (946.353, "ml"),
    "gallon": (3.78541, "l"),
    "gallons": (3.78541, "l"),
    "inch": (2.54, "cm"),
    "inches": (2.54, "cm"),
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
    """Normalize common US recipe units to metric units without changing food names."""
    text = str(text or "")

    # Where both temperatures are supplied, keep the authoritative Celsius value
    # and avoid producing duplicate temperatures after conversion.
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*degrees?\s*F(?:ahrenheit)?\s*\(\s*(\d+(?:\.\d+)?)\s*degrees?\s*C(?:elsius)?\s*\)",
        lambda m: f"{m.group(2)} °C",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*°\s*F\s*\(\s*(\d+(?:\.\d+)?)\s*°\s*C\s*\)",
        lambda m: f"{m.group(2)} °C",
        text,
        flags=re.I,
    )

    # Fahrenheit -> Celsius for remaining temperatures.
    def temp_repl(m):
        f = float(m.group(1))
        c = round((f - 32) * 5 / 9)
        return f"{c} °C"

    text = re.sub(r"(\d+(?:\.\d+)?)\s*degrees?\s*F(?:ahrenheit)?\b", temp_repl, text, flags=re.I)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\s*F\b", temp_repl, text, flags=re.I)

    # Dimensions such as 9x13 inch -> 23x33 cm.
    def dimension_repl(m):
        a = float(m.group(1))
        b = float(m.group(2))
        return f"{fmt_number(a * 2.54)} x {fmt_number(b * 2.54)} cm"

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:inch|inches|in)\b",
        dimension_repl,
        text,
        flags=re.I,
    )

    # Fractions / mixed numbers followed by a unit.
    unit_pattern = "|".join(sorted((re.escape(k) for k in UNIT_FACTORS), key=len, reverse=True))
    pattern = re.compile(rf"(?P<num>{NUMBER})\s+(?P<unit>{unit_pattern})\b", re.I)

    def unit_repl(m):
        number = parse_number(m.group("num"))
        unit = m.group("unit").lower()
        factor, target = UNIT_FACTORS[unit]
        value = number * factor
        # Use litres for large liquid amounts.
        if target == "ml" and value >= 1000:
            value /= 1000
            target = "l"
        return f"{fmt_number(value)} {target}"

    return pattern.sub(unit_repl, text)


argostranslate.package.update_package_index()
pkgs = argostranslate.package.get_available_packages()
pkg = next(p for p in pkgs if p.from_code == "en" and p.to_code == "fr")
langs = argostranslate.translate.get_installed_languages()
if not any(x.code == "fr" for x in langs):
    argostranslate.package.install_from_path(pkg.download())
langs = argostranslate.translate.get_installed_languages()
translator = next(x for x in langs if x.code == "en").get_translation(
    next(x for x in langs if x.code == "fr")
)


def tr(s):
    s = str(s or "").strip()
    return translator.translate(s) if s else ""


for idx in range(17):
    src = ROOT / "data" / "recipe_box_v2" / f"chunk_{idx:02d}.json"
    out = OUT / f"chunk_{idx:02d}.json"
    if out.exists():
        print("skip", idx)
        continue

    rows = json.loads(src.read_text())
    result = []
    for n, r in enumerate(rows, 1):
        ingredients = [convert_units(x) for x in (r.get("ingredients") or [])]
        instructions = convert_units(r.get("instructions") or "")
        result.append(
            {
                "source_name": r.get("source_name"),
                "source_recipe_id": r.get("source_recipe_id"),
                "title_fr": tr(r.get("title")),
                "ingredients_fr": [tr(x) for x in ingredients],
                "instructions_fr": tr(instructions),
            }
        )
        if n % 25 == 0:
            print(idx, n, flush=True)

    out.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    print("done", idx, len(result), flush=True)
