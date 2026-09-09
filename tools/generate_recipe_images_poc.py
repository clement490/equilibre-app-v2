#!/usr/bin/env python3
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote
import requests

STYLE = """Professional food photography for the Équilibre recipe app. Use exactly the same camera angle, framing, lighting, color palette and visual style for every image: close-up, slightly top-down approximately 35-degree camera angle, dish filling most of the frame, centered, warm natural daylight, realistic food textures, shallow depth of field, softly blurred neutral warm kitchen or countertop background, elegant but realistic everyday home cooking. The food is the only subject. Photorealistic professional food photography, appetizing but natural, not CGI, not illustration, not excessively styled. No people, no hands, no fork, no knife, no spoon, no utensils, no text, no logo, no watermark, no graphic elements, no collage, no split screen, no UI, no border, no multiple dishes, no dramatic flat-lay, no front-on camera, no excessive props."""

NEGATIVE = "Avoid utensils, hands, people, text, labels, logos, watermarks, collage, grid, multiple dishes, flat-lay overhead view, front-facing view, excessive garnish, unrelated ingredients, impossible food combinations, plastic-looking food, CGI or illustration artifacts."

PANTRY_MINOR = {
    "salt", "black pepper", "ground black pepper", "white pepper", "pepper", "baking powder",
    "baking soda", "vanilla extract", "water", "ice", "cooking spray"
}

VESSEL_RULES = [
    (("waffle", "pancake", "toast", "pizza", "muffin", "meatloaf", "enchilada", "eggplant parmesan"), "a simple flat ceramic plate"),
    (("parfait", "yogurt", "pudding", "mousse", "chia", "verrine"), "a clear transparent glass or verrine"),
    (("soup", "stew", "chili", "curry", "mac and cheese", "pasta", "ziti", "potatoes", "cauliflower"), "a shallow ceramic bowl or oven-safe serving dish appropriate to the finished food"),
    (("salad", "bowl"), "a wide shallow ceramic bowl"),
    (("wings", "chicken", "salmon", "steak", "fish"), "a simple shallow ceramic plate"),
]


def vessel_for(title: str) -> str:
    t = title.lower()
    for keywords, vessel in VESSEL_RULES:
        if any(k in t for k in keywords):
            return vessel
    return "a simple neutral ceramic plate or bowl, whichever naturally suits the finished dish"


def ingredient_core(s: str) -> str:
    s = re.sub(r"^\s*\d+(?:[./]\d+)?(?:\s*[-–]\s*\d+(?:[./]\d+)?)?\s*", "", s)
    s = re.sub(r"^\s*(?:a|an)\s+", "", s, flags=re.I)
    s = re.sub(r"^\s*\([^)]*\)\s*", "", s)
    s = re.sub(r"\s+for\s+(?:garnish|serving|frying).*$", "", s, flags=re.I)
    return s.strip(" ,.")


def principal_ingredients(ingredients):
    cores = [ingredient_core(x) for x in ingredients]
    useful = [x for x in cores if x.lower() not in PANTRY_MINOR]
    return useful[:7]


def build_prompt(recipe):
    title = recipe["title"]
    mains = principal_ingredients(recipe["ingredients"])
    vessel = vessel_for(title)
    ingredient_text = ", ".join(mains)
    return f"""{STYLE}\n\nRecipe: {title}.\nMain ingredients that must be represented naturally in the finished dish: {ingredient_text}.\nServing vessel: {vessel}.\nShow the finished dish accurately as it would look after following the recipe. The recipe title and ingredients are culinary guidance only and must never appear as text in the image. Keep the same 35-degree close-up camera angle, crop, lighting, depth of field and visual identity used for every Équilibre recipe image. The dish should occupy most of the frame and remain centered. {NEGATIVE}"""


def load_first_ten():
    path = Path("data/recipe_box_v2/chunk_00.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data[:10]


def generate(recipe, out_dir, index):
    prompt = build_prompt(recipe)
    params = {
        "model": "flux",
        "width": 1024,
        "height": 768,
        "enhance": "false",
        "nologo": "true",
        "private": "true",
    }
    # Anonymous/legacy Pollinations image endpoint. No API key is sent.
    url = "https://image.pollinations.ai/prompt/" + quote(prompt, safe="")
    started = time.time()
    r = requests.get(url, params=params, timeout=300)
    elapsed = int((time.time() - started) * 1000)
    if r.status_code != 200:
        detail = r.text[:1000]
        raise RuntimeError(f"Pollinations anonymous HTTP {r.status_code}: {detail}")
    ctype = r.headers.get("content-type", "")
    if not ctype.startswith("image/"):
        raise RuntimeError(f"Unexpected content-type: {ctype}; body={r.text[:500]}")
    ext = ".jpg" if "jpeg" in ctype else ".png"
    filename = f"{index:02d}_{recipe['source_name']}_{recipe['source_recipe_id']}{ext}"
    (out_dir / filename).write_bytes(r.content)
    return {
        "index": index,
        "source_name": recipe["source_name"],
        "source_recipe_id": recipe["source_recipe_id"],
        "title": recipe["title"],
        "principal_ingredients": principal_ingredients(recipe["ingredients"]),
        "vessel": vessel_for(recipe["title"]),
        "model": params["model"],
        "width": params["width"],
        "height": params["height"],
        "prompt_version": "equilibre-food-v1-anonymous",
        "image_path": str(out_dir / filename),
        "http_status": r.status_code,
        "mime_type": ctype,
        "bytes": len(r.content),
        "generation_time_ms": elapsed,
        "status": "generated",
    }


def main():
    out_dir = Path("poc_images_v1")
    out_dir.mkdir(parents=True, exist_ok=True)
    recipes = load_first_ten()
    manifest_path = out_dir / "results.json"
    results = []
    if manifest_path.exists():
        try:
            results = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            results = []
    done_ids = {x.get("source_recipe_id") for x in results if x.get("status") == "generated"}

    for pos, recipe in enumerate(recipes, start=1):
        if recipe["source_recipe_id"] in done_ids:
            print(f"[{pos}/10] already generated: {recipe['title']}")
            continue
        print(f"[{pos}/10] generating anonymously: {recipe['title']}", flush=True)
        try:
            result = generate(recipe, out_dir, pos)
            results.append(result)
            manifest_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{pos}/10] OK {result['bytes']} bytes", flush=True)
        except Exception as exc:
            result = {
                "index": pos,
                "source_name": recipe["source_name"],
                "source_recipe_id": recipe["source_recipe_id"],
                "title": recipe["title"],
                "status": "failed",
                "error": str(exc),
            }
            results.append(result)
            manifest_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            raise
        if pos < len(recipes):
            print("Waiting 120 seconds before the next generation...", flush=True)
            time.sleep(120)

    print("POC complete: 10 individual recipe images processed anonymously.")


if __name__ == "__main__":
    main()
