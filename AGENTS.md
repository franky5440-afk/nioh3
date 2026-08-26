# nioh3 專案規範

仁王3 攻略聚合站。Flask 本機版 + GitHub Pages 線上版共用同一套前端與資料。
全域規範見 `~/.codex/AGENTS.md`，本檔只列專案特有規則。
（2026-08-26：builder 已由 opencode 換成 codex，全域規範隨之搬到該路徑；舊的 `~/.config/opencode/AGENTS.md` 已停用，不要再引用。）

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
- 攻略庫（`guides_*.json`）是**累積式**：URL 正規化去重後併入，永不清空；X 推文區（`tweets_*.json`）同為累積式但每語言上限 250 筆（超出裁最舊）；影片區與巴哈區是每日覆寫快照
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
- **沒有 `ytsearchdate` 前綴**了；而且 `sp=CAI%3D`（上傳時間排序）**已被 YouTube 靜默忽略**——不論 innertube API 或 HTML 頁、單層或雙層編碼都一樣，回傳順序是相關性排序。2026-08-24 實測確認，不要再嘗試用 sp 排序找新片
- 找「最新影片」的正解：flat 搜尋結果自帶 `channel_id`，改抓候選頻道的上傳 RSS `https://www.youtube.com/feeds/videos.xml?channel_id={id}`——免費附發佈日期與觀看數，不必逐部完整 extract（見 `yt_rss_latest()`）
- flat playlist 搜尋自帶 `view_count`，但**沒有 upload_date**，顯示日期需對選出的影片做完整 extract（每部約 1–2 秒，記得 sleep）
- flat 搜尋結果會混入**播放清單項目**（id 是 PL… 共 34 碼），組 pool 時要過濾（只收 id 長度 11 的影片），否則完整 extract 會靜默失敗
- 影片縮圖**不下載、不入 repo**（避免再散布第三方素材）：前端直接引用 `https://i.ytimg.com/vi/{video_id}/mqdefault.jpg`，載入失敗即隱藏。`data/thumbs/` 已列入 `.gitignore`，不要重新加回下載邏輯

### DuckDuckGo（ddgs）
- 同一批 query **短時間內重跑**會回 "No results found" 或引擎 429/403——這是速率限制，不是程式壞掉。攻略庫每天只掃一次所以不受影響；除錯時不要連續重跑 `update_guides()`，誤判會浪費時間
- 中文用 `region="tw-zh"`、英文 `us-en`、日文 `jp-jp`

### 巴哈姆特
- `RSS.php` 已失效（302 導向 missing.html），只能解析 `B.php?bsn=8448` HTML
- 列表有兩種列結構：帶 `.b-list__summary__mark` 的是置頂/公告/精華（**跳過**），其標題是 `<a class="b-list__main__title">`；一般列的標題是 `<p class="b-list__main__title">` 包在外層 `<a>` 內，href 在外層 a 上，摘要用 `.b-list__brief`
- 解析失敗時保留舊資料並記 log，不要覆蓋成空檔

### X（Twitter）
- 免費讀取只有兩條活路：embed 用的 syndication 端點（`syndication.twitter.com/srv/timeline-profile/screen-name/`）與 ddgs 站內搜尋（`site:x.com`）。官方 API 要錢、Nitter 公開實例已死，不要再試
- syndication **極敏感於連續請求**（連打兩下就 429，且封鎖窗期以分鐘計）：每天只打官方帳號一次（目前僅 `@nioh_game`），失敗就保留舊資料（同巴哈模式）。回應是 `__NEXT_DATA__` JSON 包在 HTML 裡
- 推文發文日期由 status id（snowflake）右移 22 bits 加 1288834974657 換算，不需另外抓推文頁
- ddgs 撿到的標題格式是「顯示名稱 on X: 推文內容」，解析後仍要過 `GAME_TERMS` 關鍵字過濾；`tweets_*.json` 以 tid 去重累積，每語言上限 250 筆

## Git 與部署流程

🔴 **本 repo 是 PUBLIC，builder 一律不得執行 `git push`。**
公開後會被爬取、快取、索引，刪掉也收不回來。你的工作到 **commit 為止**，然後在回報裡寫清楚
「已 commit 哪幾個、可以推」就停下來，交給主對話與 Frank。**不要問要不要 push，直接停。**

⚠️ **下方步驟 2–3 裡出現的 `git push` 與 `gh workflow run` 不是給你執行的**——那是在描述整條
部署流程（含主對話與 Frank 負責的部分）。指令範例出現在文件裡不等於授權你執行。

細則（什麼可以自己做、機密掃描指令長什麼樣）一律見 `~/.codex/AGENTS.md` 的
「Git：本機操作自由，push 是閘門」一節，**此處不另立一套說法**。

1. push 前依全域規範做機密掃描（＝ `~/.codex/AGENTS.md` 裡那條 `git ls-files -z | xargs -0 grep -nE ...`；
   注意要用 `git ls-files` 而非 `grep -r`，否則會掃到 `venv/` 產生大量假警報）
2. **push 之後線上不會自動更新**，必須手動觸發：`gh workflow run deploy.yml --ref main`（workflow 也負責當天的雲端爬蟲）
3. 雲端 bot 每天 UTC 00:00 會產生 "daily data update" commit。本機 push 若被拒或 rebase 撞到 `data/*.json` 衝突，標準解法：

```bash
# ⚠️ 含推送，僅限已獲 Frank 授權者執行；builder 做到 rebase --continue 為止即停
git pull --rebase
git checkout --theirs -- data/   # 衝突時以本地較新資料為準
git add data/ && git -c core.editor=true rebase --continue && git push
```

（`git add data/` 而非 `git add -A`：這段是在解 `data/` 的衝突，不需要全域暫存，
而 `-A` 會把非預期的檔案一起帶進 commit，跟機密掃描紀律相衝。）

4. repo 必須保持 public（免費 Pages 限制），資料皆為公開網頁內容無敏感性問題

## 驗證清單

改動後必須實際執行驗證，順序：

1. `./venv/bin/python -c "import ast; ast.parse(open('scraper.py').read())"` — Python 語法
2. `node --check static/app.js` — JS 語法
3. **`node tests/site_contract.mjs` — 站台回歸契約，必須全綠**（含「初次載入內容區就可見」與 tab 切換互斥）。不需額外套件，
   它會自己建站、起 server、驅動本機 Chrome headless
4. 跑 scraper 後檢查各區筆數與**語言誤配 = 0**（用 `detect_lang(title)` 對照 item["lang"]）
5. `./start.sh` 後 curl 兩項：`/` 200、`/data/site.json` 可解析（`/thumbs/` 路由已移除，縮圖由前端直連 YouTube）
6. push 後觸發 workflow，確認 run success 再 curl 線上 site.json

## 其他約定

- 本機 cron 與雲端 Actions 雙排程並存是刻意設計（互為備援），攻略庫去重機制保證不衝突，不要「幫忙」移除其中一個
- `venv/`、`logs/`、`site/` 都不入 git；臨時探測腳本用完即刪，不留根目錄
- 使用者環境是 2012 年老 iMac：scraper 全程約 3–5 分鐘屬正常，不要為了加速建議需要大量運算的方案
