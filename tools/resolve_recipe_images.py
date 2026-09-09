import concurrent.futures, json, os, re, time
from pathlib import Path
from urllib.parse import quote, urlparse
import requests
from bs4 import BeautifulSoup

RAW_FILES = {
    "ar": "https://raw.githubusercontent.com/kz882/recipe/master/recipes_raw_nosource_ar.json",
    "epi": "https://raw.githubusercontent.com/kz882/recipe/master/recipes_raw_nosource_epi.json",
    "fn": "https://raw.githubusercontent.com/kz882/recipe/master/recipes_raw_nosource_fn.json",
}
DOMAINS = {"ar": "allrecipes.com", "epi": "epicurious.com", "fn": "foodnetwork.com"}
OUT = Path("build/recipe_image_map.json")
TIMEOUT = 20
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def tokens(s):
    return {x for x in norm(s).split() if len(x) > 2}


def selected_rows():
    rows = []
    for source, url in RAW_FILES.items():
        data = requests.get(url, timeout=60).json()
        # Reproduce the exact v2 selector from the committed corpus instead of reimplementing it.
        # The corpus file is authoritative for the 8043 IDs/titles.
    corpus = Path("data/recipe_box_v2/equilibre_selected_v2.ndjson")
    for line in corpus.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        rows.append(r)
    return rows


def get(url):
    return requests.get(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}, timeout=TIMEOUT, allow_redirects=True)


def search_links(source, title):
    domain = DOMAINS[source]
    q = quote(f'site:{domain} "{title}"')
    urls = [
        f"https://www.google.com/search?q={q}&num=10",
        f"https://www.bing.com/search?q={q}&count=10",
        f"https://html.duckduckgo.com/html/?q={q}",
    ]
    out = []
    for su in urls:
        try:
            html = get(su).text
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if href.startswith("/url?q="):
                    href = href[7:].split("&", 1)[0]
                if href.startswith("http") and domain in urlparse(href).netloc and href not in out:
                    out.append(href)
            if out:
                break
        except Exception:
            continue
    return out[:10]


def recipe_metadata(html):
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    for sel in [("meta", {"property": "og:title"}), ("meta", {"name": "twitter:title"})]:
        tag = soup.find(*sel)
        if tag and tag.get("content"):
            title = tag["content"]
            break
    image = ""
    for sel in [("meta", {"property": "og:image"}), ("meta", {"name": "twitter:image"})]:
        tag = soup.find(*sel)
        if tag and tag.get("content"):
            image = tag["content"]
            break
    ingredients = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            obj = json.loads(script.string or script.get_text())
            objs = obj if isinstance(obj, list) else [obj]
            for o in objs:
                if isinstance(o, dict) and o.get("@type") == "Recipe":
                    title = title or o.get("name", "")
                    image = image or (o.get("image", [""])[0] if isinstance(o.get("image"), list) else o.get("image", ""))
                    ingredients.extend(o.get("recipeIngredient", []) or [])
        except Exception:
            pass
    return norm(title), image, [norm(x) for x in ingredients]


def resolve(row):
    source, title = row["source_name"], row["title"]
    nt = norm(title)
    tt = tokens(title)
    best = None
    for page in search_links(source, title):
        try:
            r = get(page)
            if r.status_code != 200:
                continue
            pt, image, ings = recipe_metadata(r.text)
            if not image or not image.startswith("http"):
                continue
            title_score = 1.0 if pt == nt else (len(tt & tokens(pt)) / max(1, len(tt)))
            if title_score < 0.75:
                continue
            wanted = tokens(" ".join(row.get("ingredients", [])))
            page_ing = tokens(" ".join(ings))
            ingredient_score = len(wanted & page_ing) / max(1, min(20, len(wanted)))
            score = title_score * 0.75 + ingredient_score * 0.25
            cand = {"source_recipe_id": row["source_recipe_id"], "source_name": source, "title": title, "image_url": image, "page_url": page, "score": round(score, 4)}
            if best is None or score > best["score"]:
                best = cand
        except Exception:
            continue
    return best


def main():
    rows = selected_rows()
    print(f"Resolving {len(rows)} selected recipe images")
    results = []
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(resolve, r): r for r in rows}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            row = futs[fut]
            try:
                x = fut.result()
            except Exception:
                x = None
            if x:
                results.append(x)
            else:
                failures.append({"source_recipe_id": row["source_recipe_id"], "source_name": row["source_name"], "title": row["title"]})
            if i % 100 == 0:
                print(i, "resolved", len(results), "failed", len(failures), flush=True)
    results.sort(key=lambda x: x["source_recipe_id"])
    failures.sort(key=lambda x: x["source_recipe_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"version": 1, "total": len(rows), "resolved": len(results), "failed": len(failures), "results": results, "failures": failures}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("DONE", len(results), "resolved", len(failures), "failed")
    if len(results) < len(rows) * 0.8:
        raise SystemExit("Too few images resolved; refusing to publish a poor map")


if __name__ == "__main__":
    main()
