# Hero 視覺改版

逆推 motionsites.ai 的 "Angel Shield" 視覺後重刻的一組 hero 效果，
人物換成日本武士以符合 Nioh 3 人設。**已於 2026-08-27 接進正式站。** 本資料夾保留為設計來源與備援素材。

| 檔案 | 用途 |
|---|---|
| `samurai-hero-prompt.md` | 產主視覺圖的 prompt ＋ 圖必須符合的硬條件 |
| `hero-demo.html` | 武士版成品，單檔自含（圖已內嵌 base64），瀏覽器直接開 |
| `hero-template.html` | 上面兩個共用的模板，圖片位置是 `__ANGEL_B64__` 佔位字串 |
| `assets/hero-samurai.webp` | 早期的暫代圖，留著對照不同構圖 |

主視覺本體不放這裡，只有一份在 `static/hero-samurai.webp`（1376×1824），
`hero-demo.html` 直接相對引用它，避免同一張圖在 repo 裡存兩份。

## 效果由這六層疊出來

1. AI 主視覺 — 佔整體觀感 70%。**分兩層**：重模糊放大的背景牆負責填滿任何螢幕比例，
   人物層用 `contain` 保證頭跟基座不被裁；兩層視差速度不同，順便做出景深
2. 進場 `blur(20px) + scale(1.14)` → 清晰歸位，1.7s
3. 標題逐行 mask reveal（`overflow:hidden` ＋ 內層 `translateY(112%)`，行間錯開 130ms）
4. 滑鼠視差，五層不同深度，用 lerp（每幀走 5.5%）做慣性 — 直接綁滑鼠會很廉價
5. 金色斜向掃光，`mix-blend-mode: soft-light`，9s 一輪
6. 光塵粒子 canvas ＋ 暗角 ＋ SVG 雜訊顆粒，把 AI 圖壓成印刷品質感
7. 左下淡色遮罩（scrim），讓深色襯線標題不必跟白色盔甲的紋理搶對比

全部有 `prefers-reduced-motion` 的降級路徑。

## 正式站的接法（已完成）

| 檔案 | 改了什麼 |
|---|---|
| `static/hero-samurai.webp` | 主視覺，全 repo 唯一一份 |
| `templates/index.html` | `<header>` 之前插入 `<section class="hero">`；補 Cormorant 字體；載入 `hero.js` |
| `static/style.css` | 追加 hero 樣式 ＋「風格延續」段（吸頂玻璃 tab 列、卡片進場、全站雜訊） |
| `static/hero.js` | 新檔：視差、捲動推近、光塵粒子 |
| `static/app.js` | `switchView()` 的 `scrollTo(top:0)` → `scrollToContent()`，避免切 tab 飛回主視覺 |

### 兩個踩過的坑（改圖時要留意）

1. **`contain` 的切邊**：人物層若用 `inset:0` + `background-size:contain`，左右會出現銳利切邊。
   羽化遮罩必須落在**圖片**邊緣而不是視窗邊緣 → `.hero-img` 做成 `aspect-ratio` 跟圖一致的盒子，
   遮罩才對得準。換不同比例的圖時記得同步改 `aspect-ratio`。
2. **canvas 不會被 `inset:0` 撐開**：它是替換元素、內建尺寸 300×150，
   必須在 CSS 明寫 `width:100%; height:100%`。

### 換圖檢查清單

- `static/style.css` 裡 `hero-samurai.webp` 出現**三處**（`.hero-wall`、`.hero-img`、`.hero-detail i`）
- `.hero-img` 的 `aspect-ratio` 要對上新圖的長寬
- `.hero-halo` 的 `top` 對準圖裡的發光圓盤
- `.hero-detail i` 的 `background-position` 框住頭部
- 換完跑 `node tests/site_contract.mjs`
