#!/usr/bin/env python3
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SITE = BASE / "site"

SECTIONS = [
    "guides_zh", "guides_en",
    "videos_hot_zh", "videos_hot_en",
    "videos_new_zh", "videos_new_en",
    "bahamut", "meta",
]


def main():
    merged = {}
    for name in SECTIONS:
        p = DATA / f"{name}.json"
        merged[name] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else ([] if name != "meta" else {})

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "data").mkdir(parents=True)
    payload = json.dumps(merged, ensure_ascii=False)
    (DATA / "site.json").write_text(payload, encoding="utf-8")
    (SITE / "data" / "site.json").write_text(payload, encoding="utf-8")
    shutil.copy(BASE / "templates" / "index.html", SITE / "index.html")
    shutil.copytree(BASE / "static", SITE / "static")
    shutil.copytree(DATA / "thumbs", SITE / "thumbs")
    print(f"site built: {len(merged['guides_zh']) + len(merged['guides_en'])} guides, "
          f"{sum(len(merged[k]) for k in ('videos_hot_zh', 'videos_hot_en', 'videos_new_zh', 'videos_new_en'))} videos")


if __name__ == "__main__":
    main()
