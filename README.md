# 仁王3 攻略武庫 Nioh 3 Guide Hub

本機自用攻略聚合站。所有資料僅存放於本工作區 `data/`，每日由排程自動更新。

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
| 攻略庫 | 全網搜尋文字／圖文攻略，累積式攻略庫，分中文區與 English，再依 Boss、配裝、武器、新手、流程、收集、白金、情報等類別分區 | `data/guides_zh.json` `data/guides_en.json` |
| 熱門影片 TOP10 | YouTube 每日熱門攻略影片（依觀看數），分中英文區 | `data/videos_hot_{zh,en}.json` |
| 最新影片 | YouTube 每日最新發布攻略影片各 10 部，分中英文區 | `data/videos_new_{zh,en}.json` |
| 巴哈討論區 | 巴哈姆特仁王哈啦區（bsn=8448）最新 10 篇討論（已排除置頂公告） | `data/bahamut.json` |

頂部搜尋框可跨全部內容（攻略＋影片＋討論）以關鍵字搜尋。

## 每日更新

cron 已設定每天 08:00 執行 `update.sh`（呼叫 `scraper.py`）。

手動更新：`./update.sh`

更新來源：
- 攻略庫：DuckDuckGo 網頁搜尋（ddgs）
- YouTube：yt-dlp（不需 API key）
- 巴哈姆特：HTML 解析

## 日誌

- `logs/scraper.log` — scraper 完整記錄
- `logs/cron.log` — cron 執行輸出
- `logs/server.log` — 網站伺服器輸出
