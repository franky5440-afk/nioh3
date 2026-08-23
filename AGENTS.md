# nioh3 專案規範

仁王3 攻略聚合站。Flask 本機版 + GitHub Pages 線上版共用同一套前端與資料。
全域規範見 `~/.config/opencode/AGENTS.md`，本檔只列專案特有規則。

## 語言

一律使用繁體中文回覆。程式碼、指令、變數名稱維持英文。

## 架構與資料流

```
scraper.py ──> data/*.json ──> build_site.py ──> site/（靜態站，Pages artifact）
                     │
                     └──> app.py（Flask 本機版，直接讀 data/）
```

- `data/*.json` 是唯一資料來源，所有內容只能存放在本工作區
- `site/` 是建置產物，已列入 `.gitignore`，**絕不 commit**；Pages 用 `actions/upload-pages-artifact` 上傳，不是 gh-pages branch
- 攻略庫（`guides_*.json`）是**累積式**：URL 正規化去重後併入，永不清空；影片區與巴哈區是每日覆寫快照
- `meta.json` 記錄各區最後更新時間，`_last_run` 是完整掃描時間

## 語言分區規則（不可破壞）

三區 zh / en / ja 由 `detect_lang()` 判定：

1. 標題或摘要含**平/片假名** → ja
2. 網域以 `.jp` 結尾 → ja
3. 含 CJK 字元 → zh
4. 其餘 → en

影片區的 `keep()` 過濾同邏輯：ja 要有假名；zh 必須「含 CJK 且**無**假名」。新增任何抓取來源都要套用此規則，避免日文混入中文區。

## 各來源已知陷阱

### yt-dlp（v2026.08+）
- **沒有 `ytsearchdate` 前綴**了，按上傳時間排序要用搜尋 URL：`https://www.youtube.com/results?search_query={q}&sp=CAI%3D`——注意 `CAI%3D` 只能單能單層編碼，寫成 `%253D` 會被 parse_qs 解碼成無效參數、排序靜默失效
- flat playlist 搜尋自帶 `view_count`，但**沒有 upload_date**，顯示日期需對選出的影片做完整 extract（每部約 1–2 秒，記得 sleep）
- 影片縮圖下載到 `data/thumbs/{video_id}.jpg`，前端以相對路徑 `thumbs/...jpg` 引用，onerror fallback 到 i.ytimg.com

### DuckDuckGo（ddgs）
- 同一批 query **短時間內重跑**會回 "No results found" 或引擎 429/403——這是速率限制，不是程式壞掉。攻略庫每天只掃一次所以不受影響；除錯時不要連續重跑 `update_guides()`，誤判會浪費時間
- 中文用 `region="tw-zh"`、英文 `us-en`、日文 `jp-jp`

### 巴哈姆特
- `RSS.php` 已失效（302 導向 missing.html），只能解析 `B.php?bsn=8448` HTML
- 列表有兩種列結構：帶 `.b-list__summary__mark` 的是置頂/公告/精華（**跳過**），其標題是 `<a class="b-list__main__title">`；一般列的標題是 `<p class="b-list__main__title">` 包在外層 `<a>` 內，href 在外層 a 上，摘要用 `.b-list__brief`
- 解析失敗時保留舊資料並記 log，不要覆蓋成空檔

## Git 與部署流程

1. push 前依全域規範做機密掃描
2. **push 之後線上不會自動更新**，必須手動觸發：`gh workflow run deploy.yml --ref main`（workflow 也負責當天的雲端爬蟲）
3. 雲端 bot 每天 UTC 00:00 會產生 "daily data update" commit。本機 push 若被拒或 rebase 撞到 `data/*.json` 衝突，標準解法：

```bash
git pull --rebase
git checkout --theirs -- data/   # 衝突時以本地較新資料為準
git add -A && git -c core.editor=true rebase --continue && git push
```

4. repo 必須保持 public（免費 Pages 限制），資料皆為公開網頁內容無敏感性問題

## 驗證清單

改動後必須實際執行驗證，順序：

1. `./venv/bin/python -c "import ast; ast.parse(open('scraper.py').read())"` — Python 語法
2. `node --check static/app.js` — JS 語法
3. 跑 scraper 後檢查各區筆數與**語言誤配 = 0**（用 `detect_lang(title)` 對照 item["lang"]）
4. `./start.sh` 後 curl 三項：`/` 200、`/data/site.json` 可解析、任一 `/thumbs/<id>.jpg` 200
5. push 後觸發 workflow，確認 run success 再 curl 線上 site.json

## 其他約定

- 本機 cron 與雲端 Actions 雙排程並存是刻意設計（互為備援），攻略庫去重機制保證不衝突，不要「幫忙」移除其中一個
- `venv/`、`logs/`、`site/` 都不入 git；臨時探測腳本用完即刪，不留根目錄
- 使用者環境是 2012 年老 iMac：scraper 全程約 3–5 分鐘屬正常，不要為了加速建議需要大量運算的方案
