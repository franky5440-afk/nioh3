# 仁王3 攻略武庫 Nioh 3 Guide Hub

**線上版：https://franky5440-afk.github.io/nioh3/**

本機自用攻略聚合站。所有資料僅存放於本工作區 `data/`，每日由排程自動更新。

- 線上版：GitHub Actions 每日 UTC 00:00（台北 08:00）雲端執行 `scraper.py` → 建置靜態站 → 自動發布 GitHub Pages，並將資料 commit 回本 repo
- 本機版：cron 每天 08:00 執行 `update.sh`，Flask 服務於 `http://127.0.0.1:8765`

## 啟動網站

```bash
./start.sh          # 啟動於 http://127.0.0.1:8765
./stop.sh           # 停止
```

首次使用需先建環境：

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 分頁功能

| 分頁 | 內容 | 資料檔 |
|------|------|--------|
| 攻略庫 | 全網搜尋文字／圖文攻略，累積式攻略庫，分中文區、English、日本語，再依 Boss、配裝、武器、新手、流程、收集、白金、情報等類別分區 | `data/guides_{zh,en,ja}.json` |
| 熱門影片 TOP10 | YouTube 每日熱門攻略影片（依觀看數），分中文、英文、日文區 | `data/videos_hot_{zh,en,ja}.json` |
| 最新影片 | YouTube 每日最新發布攻略影片各 10 部，分中文、英文、日文區 | `data/videos_new_{zh,en,ja}.json` |
| 巴哈討論區 | 巴哈姆特仁王哈啦區（bsn=8448）最新 10 篇討論（已排除置頂公告） | `data/bahamut.json` |

頂部搜尋框可跨全部內容（攻略＋影片＋討論）以關鍵字搜尋。

## 每日更新

- 雲端：GitHub Actions schedule（`.github/workflows/deploy.yml`），可手動觸發：`gh workflow run deploy.yml`
- 本機：cron 已設定每天 08:00 執行 `update.sh`；手動更新：`./update.sh`

更新來源：
- 攻略庫：DuckDuckGo 網頁搜尋（ddgs）
- YouTube：yt-dlp（不需 API key）
- 巴哈姆特：HTML 解析

語言分區判定：標題或摘要含假名、或網域為 .jp → 日文區；含中日韓字元 → 中文區；其餘 → 英文區。三區各自獨立累積，不會互相混雜。

## 專案結構

```
nioh3/
├── app.py                     # Flask 本機伺服器（127.0.0.1:8765）
├── scraper.py                 # 每日爬蟲：攻略庫 / YouTube 熱門+最新 / 巴哈討論
├── build_site.py              # 彙整 data/*.json → site/ 靜態站（Pages artifact）
├── start.sh / stop.sh         # 本機網站啟停
├── update.sh                  # cron 每日更新入口（scraper + build）
├── requirements.txt
├── AGENTS.md                  # 維護規範（給 AI 助手看的工作守則，人也可參考）
├── templates/index.html       # 單頁前端
├── static/style.css, app.js   # 樣式與邏輯（搜尋在瀏覽器本地執行）
├── .github/workflows/deploy.yml  # 每日雲端爬蟲 + Pages 自動部署
└── data/
    ├── guides_{zh,en,ja}.json     # 攻略庫（累積式，URL 去重）
    ├── videos_hot_{zh,en,ja}.json # 熱門影片 TOP10（每日覆寫）
    ├── videos_new_{zh,en,ja}.json # 最新影片（每日覆寫）
    ├── bahamut.json               # 巴哈最新討論（每日覆寫）
    ├── meta.json                  # 各區最後更新時間
    ├── site.json                  # 前端讀取的彙整檔（build_site.py 產生）
    └── thumbs/{video_id}.jpg      # 影片縮圖快取
```

## 疑難排解

- **攻略庫掃不到新資料**：DuckDuckGo 有速率限制，同批關鍵字短時間內重跑會被擋，等隔天排程即可
- **push 被拒**：雲端 bot 每天會 commit 新資料，先 `git pull --rebase`；若 `data/*.json` 衝突，以本地較新資料為準（`git checkout --theirs -- data/`）再 `rebase --continue`
- **線上沒更新**：push 不會自動發布，需 `gh workflow run deploy.yml --ref main`
- **巴哈解析失敗**：scraper 會保留前一日資料並記錄於 `logs/scraper.log`，不會覆蓋成空檔

維護此專案的完整工作規範見 [AGENTS.md](AGENTS.md)。

## 日誌

- `logs/scraper.log` — scraper 完整記錄
- `logs/cron.log` — cron 執行輸出
- `logs/server.log` — 網站伺服器輸出
