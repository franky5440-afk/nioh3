#!/usr/bin/env python3
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse

import requests
import yt_dlp
from bs4 import BeautifulSoup
from ddgs import DDGS

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
LOGS = BASE / "logs"
DATA.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOGS / "scraper.log", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("nioh3")

BAHA_URL = "https://forum.gamer.com.tw/B.php?bsn=8448"
BAHA_BASE = "https://forum.gamer.com.tw/"
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.5",
}

VIDEO_DOMAINS = ("youtube.com", "youtu.be", "bilibili.com", "twitch.tv", "nicovideo.jp")

NEW_CUTOFF_DAYS = 21
RSS_CHANNEL_CAP = 60
NEW_FLAT_LIMIT = 150
GAME_TERMS = ("仁王", "nioh")

CATEGORIES = [
    ("boss", ["boss", "頭目", "尾王", "打法", "弱點", "怎麼打", "打不死", "攻略 boss"]),
    ("build", ["build", "配裝", "流派", "詞綴", "恩寵", "強度", "最強", "傷害", "疊", "meta", "op ", "broken"]),
    ("weapon", ["武器", "太刀", "大太刀", "鎖鐮", "手甲", "薙刀", "双刀", "雙刀", "斧", "槍", "弓", "銃", "炮", "盾鉾", "旋棍", "weapon", "katana", "odachi", "spear", "tonfa", "hatchet", "kusarigama", "bow", "rifle"]),
    ("beginner", ["新手", "入門", "開局", "初期", "初學", "beginner", "tips", "basics", "starter", "getting started", "early game", "guide to"]),
    ("walkthrough", ["流程", "主線", "支線", "任務", "章節", "全收集流程", "walkthrough", "mission", "chapter", "playthrough", "let's play"]),
    ("collect", ["收集", "木靈", "溫泉", "隱藏", "地點", "入手", "道具", "裝備", "kodama", "location", "collectible", "item", "where to find", "shrine"]),
    ("trophy", ["白金", "獎盃", "成就", "trophy", "achievement", "platinum", "100%"]),
    ("news", ["更新", "dlc", "情報", "資料片", "改版", "patch", "update", "news", "review", "評價"]),
]

CATEGORY_LABELS = {
    "boss": {"zh": "Boss 攻略", "en": "Boss Guides"},
    "build": {"zh": "配裝 Build", "en": "Builds"},
    "weapon": {"zh": "武器流派", "en": "Weapons"},
    "beginner": {"zh": "新手入門", "en": "Beginner"},
    "walkthrough": {"zh": "流程任務", "en": "Walkthrough"},
    "collect": {"zh": "收集要素", "en": "Collectibles"},
    "trophy": {"zh": "白金成就", "en": "Trophies"},
    "news": {"zh": "情報更新", "en": "News & DLC"},
    "general": {"zh": "綜合討論", "en": "General"},
}


def now_str():
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def load_json(name, default):
    p = DATA / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def save_json(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def set_meta(section):
    meta = load_json("meta.json", {})
    meta[section] = now_str()
    save_json("meta.json", meta)


CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
KANA_RE = re.compile(r"[\u3040-\u30ff]")


def has_cjk(s):
    return bool(CJK_RE.search(s or ""))


def detect_lang(text, url=""):
    t = text or ""
    if KANA_RE.search(t):
        return "ja"
    d = domain_of(url)
    if d.endswith(".jp"):
        return "ja"
    if has_cjk(t):
        return "zh"
    return "en"


def norm_url(u):
    u = u.split("#")[0].rstrip("/")
    return u.lower()


def domain_of(u):
    netloc = urlparse(u).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def classify(text):
    t = text.lower()
    for key, words in CATEGORIES:
        if any(w in t for w in words):
            return key
    return "general"


def is_video_url(url):
    d = domain_of(url)
    return any(d == vd or d.endswith("." + vd) for vd in VIDEO_DOMAINS)


def yt_flat_search(query, n, sort_by_date=False, flat_limit=None):
    if sort_by_date:
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}&sp=CAI%3D"
    else:
        url = f"ytsearch{n}:{query}"
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True, "socket_timeout": 30}
    if flat_limit:
        opts["playlist_items"] = f"1:{flat_limit}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    out = []
    for e in info.get("entries") or []:
        if not isinstance(e, dict):
            continue
        vid = e.get("id")
        if not vid or len(vid) != 11:
            continue
        out.append({
            "video_id": vid,
            "title": e.get("title") or "",
            "channel": e.get("channel") or e.get("uploader") or "",
            "channel_id": e.get("channel_id") or "",
            "view_count": e.get("view_count"),
            "duration": e.get("duration"),
            "url": f"https://www.youtube.com/watch?v={vid}",
        })
    return out


YDL_FULL = {"quiet": True, "no_warnings": True, "skip_download": True, "socket_timeout": 30}


def yt_rss_latest(channel_id):
    """頻道上傳 RSS：回 [(video_id, title, date, views)]，最新 15 筆，含發佈日期與觀看數"""
    out = []
    try:
        r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}", headers=UA, timeout=15)
        r.raise_for_status()
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
              "m": "http://search.yahoo.com/mrss/"}
        for e in ET.fromstring(r.content).findall("a:entry", ns):
            vid = e.findtext("yt:videoId", "", ns)
            title = (e.findtext("a:title", "", ns) or "").strip()
            pub = (e.findtext("a:published", "", ns) or "")[:10]
            views = e.find(".//m:statistics", ns)
            out.append((vid, title, pub, int(views.get("views")) if views is not None and views.get("views", "").isdigit() else None))
    except Exception as e:
        log.warning("yt rss %s: %s", channel_id[:12], e)
    return out


def yt_full_info(vid):
    try:
        with yt_dlp.YoutubeDL(YDL_FULL) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        ud = info.get("upload_date")
        date = f"{ud[:4]}-{ud[4:6]}-{ud[6:8]}" if ud else None
        vc = info.get("view_count")
        return date, vc if isinstance(vc, int) else None
    except Exception as e:
        log.warning("yt full %s: %s", vid, e)
        return None, None


def collect_videos(lang):
    if lang == "zh":
        hot_queries, new_queries = ["仁王3 攻略"], ["仁王3 攻略"]

        def keep(title):
            return has_cjk(title) and not KANA_RE.search(title)
    elif lang == "ja":
        hot_queries, new_queries = ["仁王3 攻略", "仁王3 実況 攻略"], ["仁王3 攻略"]

        def keep(title):
            return bool(KANA_RE.search(title))
    else:
        hot_queries, new_queries = ["Nioh 3 guide", "Nioh 3 tips"], ["Nioh 3 guide"]

        def keep(title):
            return not has_cjk(title)

    pool_hot = []
    seen = set()
    for q in hot_queries:
        for v in yt_flat_search(q, 25):
            k = v["video_id"]
            if k in seen:
                continue
            seen.add(k)
            if not keep(v["title"]):
                continue
            pool_hot.append(v)

    def to_item(v, date, vc):
        return {
            "video_id": v["video_id"],
            "title": v["title"],
            "channel": v["channel"],
            "url": v["url"],
            "views": vc,
            "date": date,
            "lang": lang,
        }

    pool_new = []
    seen2 = set()
    for q in new_queries:
        for v in yt_flat_search(q, 25, sort_by_date=True, flat_limit=NEW_FLAT_LIMIT):
            k = v["video_id"]
            if k in seen2:
                continue
            seen2.add(k)
            if not keep(v["title"]):
                continue
            pool_new.append(v)

    # 候選頻道 RSS 查表：雲端 IP 會被 YouTube 擋完整 extract，RSS（純 requests）不受限
    # 熱門候選按觀看數排序優先佔位（RSS 每頻道僅回最近 ~15 支，活躍頻道的老熱門片可能查不到）
    chans = []
    for v in sorted(pool_hot, key=lambda x: -(x.get("view_count") or 0)):
        cid = v.get("channel_id")
        if cid and cid not in chans:
            chans.append(cid)
    for v in pool_new:
        cid = v.get("channel_id")
        if cid and cid not in chans:
            chans.append(cid)
    rss_map = {}
    for cid in chans[:RSS_CHANNEL_CAP]:
        for vid, title, pub, views in yt_rss_latest(cid):
            if pub and len(pub) == 10:
                rss_map[vid] = {"title": title, "date": pub, "views": views}
        time.sleep(0.3)
    log.info("videos [%s]: %d channels rss -> %d videos", lang, min(len(chans), RSS_CHANNEL_CAP), len(rss_map))

    def pick_hot(pool, top_n):
        known = [v for v in pool if isinstance(v.get("view_count"), int)]
        unknown = [v for v in pool if not isinstance(v.get("view_count"), int)]
        need = max(0, top_n * 2 - len(known))
        for v in unknown[:need]:
            if v["video_id"] in rss_map:
                v["view_count"] = rss_map[v["video_id"]]["views"]
                if isinstance(v["view_count"], int):
                    known.append(v)
                    continue
            _, vc = yt_full_info(v["video_id"])
            time.sleep(0.5)
            if isinstance(vc, int):
                v["view_count"] = vc
                known.append(v)
        picked = sorted(known, key=lambda x: -(x["view_count"] or 0))[:top_n]
        out = []
        for v in picked:
            date = (rss_map.get(v["video_id"]) or {}).get("date")
            if not date:
                date, _ = yt_full_info(v["video_id"])
                time.sleep(0.4)
            out.append(to_item(v, date, v.get("view_count")))
        return out

    def pick_new(pool, top_n):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=NEW_CUTOFF_DAYS)).date()
        chan_of = {v["video_id"]: v["channel"] for v in pool}
        cands = {}
        for vid, info in rss_map.items():
            try:
                recent = datetime.strptime(info["date"], "%Y-%m-%d").date() >= cutoff
            except ValueError:
                continue
            if not (recent and keep(info["title"]) and any(t in info["title"].lower() for t in GAME_TERMS)):
                continue
            cands[vid] = to_item({"video_id": vid, "title": info["title"], "channel": chan_of.get(vid, ""), "url": f"https://www.youtube.com/watch?v={vid}"}, info["date"], info["views"])
        items = sorted(cands.values(), key=lambda x: x["date"] or "", reverse=True)[:top_n]
        if items:
            return items
        log.warning("videos new [%s]: rss empty, falling back to full-extract scan", lang)
        recent, scanned = [], 0
        for v in pool:
            if len(recent) >= top_n or scanned >= 40:
                break
            scanned += 1
            date, vc = yt_full_info(v["video_id"])
            time.sleep(0.4)
            try:
                is_recent = bool(date) and datetime.strptime(date, "%Y-%m-%d").date() >= cutoff
            except ValueError:
                is_recent = False
            if is_recent:
                recent.append(to_item(v, date, vc))
        return sorted(recent, key=lambda x: x["date"] or "", reverse=True)

    log.info("videos hot [%s]: %d candidates", lang, len(pool_hot))
    hot = pick_hot(pool_hot, 10)

    log.info("videos new [%s]: %d candidates", lang, len(pool_new))
    new = pick_new(pool_new, 10)

    return hot, new


GUIDE_QUERIES = {
    "zh": [
        "仁王3 攻略", "仁王3 圖文攻略", "仁王3 boss 打法", "仁王3 配裝 build",
        "仁王3 新手 入門 開局", "仁王3 武器 推薦", "仁王3 白金 獎盃", "仁王3 收集 木靈 溫泉",
    ],
    "en": [
        "Nioh 3 guide", "Nioh 3 walkthrough", "Nioh 3 boss guide", "Nioh 3 best build",
        "Nioh 3 beginner tips", "Nioh 3 weapons tier list", "Nioh 3 trophy guide", "Nioh 3 kodama locations",
    ],
    "ja": [
        "仁王3 攻略", "仁王3 攻略 wiki", "仁王3 ボス 攻略方法", "仁王3 ビルド 最強",
        "仁王3 初心者 序盤 攻略", "仁王3 武器 おすすめ", "仁王3 トロフィー コンプ", "仁王3 収集要素 場所",
    ],
}

QUERY_REGIONS = {"zh": "tw-zh", "en": "us-en", "ja": "jp-jp"}


def update_guides():
    pool = {}
    for lang in ("zh", "en", "ja"):
        for g in load_json(f"guides_{lang}.json", []):
            k = norm_url(g["url"])
            g["lang"] = detect_lang(g["title"] + " " + g.get("snippet", ""), g["url"])
            pool[k] = g
    added = 0
    with DDGS() as d:
        for qkey, queries in GUIDE_QUERIES.items():
            region = QUERY_REGIONS[qkey]
            for q in queries:
                try:
                    results = list(d.text(q, region=region, max_results=12))
                except Exception as e:
                    log.warning("ddgs %s %s: %s", qkey, q, e)
                    time.sleep(2)
                    continue
                for r in results:
                    url = r.get("href") or ""
                    title = (r.get("title") or "").strip()
                    if not url.startswith("http") or is_video_url(url):
                        continue
                    k = norm_url(url)
                    if k in pool:
                        continue
                    body = (r.get("body") or "").strip()
                    item = {
                        "id": re.sub(r"[^a-f0-9]", "", __import__("hashlib").md5(k.encode()).hexdigest()),
                        "title": title,
                        "url": url,
                        "snippet": body,
                        "source": domain_of(url),
                        "category": classify(title + " " + body),
                        "lang": detect_lang(title + " " + body, url),
                        "found_date": now_str()[:10],
                    }
                    pool[k] = item
                    added += 1
                time.sleep(1.5)
    buckets = {"zh": [], "en": [], "ja": []}
    for it in pool.values():
        lang = it.get("lang") if it.get("lang") in buckets else detect_lang(it["title"] + " " + it.get("snippet", ""), it["url"])
        buckets[lang].append(it)
    for lang, items in buckets.items():
        save_json(f"guides_{lang}.json", items)
        set_meta(f"guides_{lang}")
    log.info("guides: +%d -> zh=%d en=%d ja=%d", added, len(buckets["zh"]), len(buckets["en"]), len(buckets["ja"]))


def update_videos():
    cache = load_json("video_dates.json", {})
    for lang in ("zh", "en", "ja"):
        hot, new = collect_videos(lang)
        # 日期快取：本機 yt_full_info 可用、雲端被 bot 驗證擋住，靠累積互補
        for it in [*hot, *new]:
            vid = it["video_id"]
            if it["date"]:
                cache[vid] = it["date"]
            elif vid in cache:
                it["date"] = cache[vid]
        save_json(f"videos_hot_{lang}.json", hot)
        save_json(f"videos_new_{lang}.json", new)
        set_meta(f"videos_hot_{lang}")
        set_meta(f"videos_new_{lang}")
        log.info("videos [%s]: hot=%d new=%d", lang, len(hot), len(new))
    save_json("video_dates.json", cache)


def parse_baha_rows(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for row in soup.select("tr.b-list__row"):
        if row.select_one(".b-list__summary__mark"):
            continue
        main_link = row.select_one("td.b-list__main > a[href*='C.php']")
        if not main_link:
            continue
        title_el = row.select_one(".b-list__main__title")
        brief = row.select_one(".b-list__brief")
        num_el = row.select_one(".b-list__count__number span")
        author_el = row.select_one(".b-list__count__user a")
        time_el = row.select_one(".b-list__time__edittime a")
        items.append({
            "title": title_el.get_text(" ", strip=True) if title_el else "",
            "url": urljoin(BAHA_BASE, main_link.get("href", "")),
            "author": author_el.get_text(strip=True) if author_el else "",
            "replies": num_el.get_text(strip=True) if num_el else "",
            "time": time_el.get_text(strip=True) if time_el else "",
            "snippet": brief.get_text(" ", strip=True)[:200] if brief else "",
        })
    return items


def update_bahamut():
    items = []
    try:
        r = requests.get(BAHA_URL, headers=UA, timeout=20)
        r.raise_for_status()
        rows = parse_baha_rows(r.text)
        seen = set()
        for it in rows:
            k = norm_url(it["url"])
            if k in seen:
                continue
            seen.add(k)
            it["id"] = re.sub(r"[^a-f0-9]", "", __import__("hashlib").md5(k.encode()).hexdigest())
            it["source"] = "forum.gamer.com.tw"
            it["category"] = classify(it["title"])
            it["found_date"] = now_str()[:10]
            items.append(it)
            if len(items) >= 10:
                break
    except Exception as e:
        log.error("bahamut failed: %s", e)
    if items:
        save_json("bahamut.json", items)
        set_meta("bahamut")
        log.info("bahamut: %d topics", len(items))
    else:
        log.warning("bahamut: no items parsed, keeping previous data")


def main():
    started = time.time()
    log.info("=" * 50)
    steps = [
        ("guides", update_guides),
        ("videos", update_videos),
        ("bahamut", update_bahamut),
    ]
    failures = []
    for name, fn in steps:
        try:
            fn()
        except Exception as e:
            log.exception("%s crashed: %s", name, e)
            failures.append(name)
    set_meta("_last_run")
    log.info("done in %.1fs%s", time.time() - started, f" | FAILED: {failures}" if failures else "")


if __name__ == "__main__":
    main()
