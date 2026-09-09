#!/usr/bin/env python3
"""Build static Pages artifact: merge JSON data + convert story MD → HTML JSON."""
import json
import re
import shutil
from pathlib import Path

import markdown as md_lib

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SITE = BASE / "site"
STORY_SRC = BASE / "content" / "story"
DLC01_SRC = STORY_SRC / "dlc01"

SECTIONS = [
    "guides_zh", "guides_en", "guides_ja",
    "videos_hot_zh", "videos_hot_en", "videos_hot_ja",
    "videos_new_zh", "videos_new_en", "videos_new_ja",
    "bahamut",
    "tweets_zh", "tweets_en", "tweets_ja",
    "meta",
]

# Reader chapters (ordered). 目錄大綱 / 全稿 stay in content/story for maintenance only.
STORY_PUBLISH = [
    "00_前言與劇透警告.md",
    "01_繼任日血祭.md",
    "02_亂世初至.md",
    "03_二俣與三方原.md",
    "04_濱松熔爐.md",
    "05_鞍馬天狗.md",
    "06_三障靈樹.md",
    "07_邪馬台裂隙.md",
    "08_歸日初刃.md",
    "09_幕末希望.md",
    "10_靈樹成林.md",
    "11_改命異城.md",
    "12_天守蛭子.md",
    "13_斬與赦.md",
    "99_人物小傳與時間線.md",
]

# DLC01 reader chapters. 目錄大綱 / 全稿 stay in content/story/dlc01 for maintenance only.
DLC01_PUBLISH = [
    "DLC01_00_慶安地獄變_導讀與本篇連結.md",  # 導讀與本篇連結（必先）
    "DLC01_01_夢導慶安.md",
    "DLC01_02_隻眼與使節.md",
    "DLC01_03_張孔堂風雲.md",
    "DLC01_04_道灌山正雪.md",
    "DLC01_05_暫歇與未完.md",
    "DLC01_99_人物與缺口.md",
]

MD = md_lib.Markdown(extensions=["tables", "fenced_code", "nl2br", "sane_lists"])


def chapter_id(filename: str, prefix: str = "ch") -> str:
    stem = Path(filename).stem
    # DLC01_00_… / DLC01_99_… → dlc01-00
    m = re.match(r"^DLC0*(\d+)_(\d+)", stem, flags=re.I)
    if m:
        return f"dlc{int(m.group(1)):02d}-{m.group(2)}"
    m = re.match(r"^(\d+)", stem)
    return f"{prefix}-{m.group(1)}" if m else f"{prefix}-{stem}"


def chapter_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def _plain_h2_title(h2_html: str) -> str:
    inner = re.sub(r"^<h2>|</h2>$", "", h2_html, flags=re.I)
    return re.sub(r"<[^>]+>", "", inner).strip()


def wrap_ending_sections(html: str) -> str:
    """Wrap A｜/B｜/共通 h2 blocks so dual endings stay visually distinct."""
    parts = re.split(r"(<h2>.*?</h2>)", html, flags=re.I | re.S)
    out = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if re.match(r"<h2>", part, flags=re.I):
            title = _plain_h2_title(part)
            body = parts[i + 1] if i + 1 < len(parts) else ""
            cls = badge = None
            if title.startswith("A｜") or title.startswith("A|"):
                cls, badge = "story-ending story-ending-a", "結局 A｜處刑"
            elif title.startswith("B｜") or title.startswith("B|"):
                cls, badge = "story-ending story-ending-b", "結局 B｜影武者"
            elif title.startswith("共通"):
                cls, badge = "story-ending story-ending-common", "共通收束"
            if cls:
                out.append(
                    f'<div class="{cls}">'
                    f'<div class="story-ending-badge">{badge}</div>'
                    f"<h2>{title}</h2>{body}</div>"
                )
                i += 2
                continue
            out.append(part)
            i += 1
            continue
        out.append(part)
        i += 1
    return "".join(out)


def _load_chapters(src: Path, filenames: list[str], wrap_13: bool = False) -> list[dict]:
    chapters = []
    for fname in filenames:
        path = src / fname
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        title = chapter_title(raw, Path(fname).stem)
        MD.reset()
        html = MD.convert(raw)
        if wrap_13 and fname.startswith("13_"):
            html = wrap_ending_sections(html)
        chapters.append({
            "id": chapter_id(fname),
            "file": fname,
            "title": title,
            "html": html,
        })
    return chapters


def build_story() -> dict:
    """Convert published chapter markdown → HTML payload for the 劇情小說 tab.

    Schema (volumes): one JSON for a single loadStory() call.
      {
        title, subtitle,
        volumes: [ { id, title, short_title, blurb, chapters, chapter_count }, … ],
        chapters,          # backward-compat alias = 本篇 chapters
        chapter_count      # 本篇章數（既有 UI 語意）
      }
    """
    if not STORY_SRC.is_dir():
        return {
            "title": "仁王3｜章回小說",
            "volumes": [],
            "chapters": [],
            "chapter_count": 0,
            "error": "content/story 目錄不存在",
        }

    main_chapters = _load_chapters(STORY_SRC, STORY_PUBLISH, wrap_13=True)
    dlc01_chapters = _load_chapters(DLC01_SRC, DLC01_PUBLISH, wrap_13=False)

    volumes = [
        {
            "id": "main",
            "title": "本篇",
            "short_title": "本篇",
            "blurb": "元和八年繼任日 → 天守決戰與斬／赦雙結局",
            "chapters": main_chapters,
            "chapter_count": len(main_chapters),
        },
        {
            "id": "dlc01",
            "title": "DLC01 慶安地獄變",
            "short_title": "DLC01 慶安地獄變",
            "blurb": "家光就任後 → 1651 慶安；A斬／B赦皆可接；請先讀導讀",
            "chapters": dlc01_chapters,
            "chapter_count": len(dlc01_chapters),
        },
    ]

    return {
        "title": "仁王3｜章回小說體全稿",
        "subtitle": "原創敘事改寫 · 非官方劇本 · 含本篇與 DLC01",
        "volumes": volumes,
        # Backward compatible: flat chapters = 本篇 only (既有 15 章語意不變)
        "chapters": main_chapters,
        "chapter_count": len(main_chapters),
    }


def main():
    merged = {}
    for name in SECTIONS:
        p = DATA / f"{name}.json"
        merged[name] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else ([] if name != "meta" else {})

    story = build_story()

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "data").mkdir(parents=True)
    payload = json.dumps(merged, ensure_ascii=False)
    (DATA / "site.json").write_text(payload, encoding="utf-8")
    (SITE / "data" / "site.json").write_text(payload, encoding="utf-8")

    story_payload = json.dumps(story, ensure_ascii=False)
    (DATA / "story.json").write_text(story_payload, encoding="utf-8")
    (SITE / "data" / "story.json").write_text(story_payload, encoding="utf-8")

    shutil.copy(BASE / "templates" / "index.html", SITE / "index.html")
    shutil.copytree(BASE / "static", SITE / "static")
    vol_summary = ", ".join(
        f"{v['id']}={v['chapter_count']}" for v in story.get("volumes", [])
    )
    print(
        f"site built: {sum(len(merged[k]) for k in merged if k.startswith('guides'))} guides, "
        f"{sum(len(merged[k]) for k in ('videos_hot_zh', 'videos_hot_en', 'videos_new_zh', 'videos_new_en'))} videos, "
        f"story volumes=[{vol_summary}] main_chapters={story.get('chapter_count', 0)}"
    )


if __name__ == "__main__":
    main()
