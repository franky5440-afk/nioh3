# Nioh 3 Hero 主視覺 — 產圖 Prompt

## 硬條件（不符合的話，網頁那組效果會壞掉）

| 條件 | 值 | 為什麼 |
|---|---|---|
| 長寬比 | **不限**（直式 3:4 也可以） | 網頁已改成雙層：模糊背景牆負責填滿螢幕，人物層用 `contain` 不裁 |
| 構圖 | **正面、置中、左右對稱** | 左上標題／右中卡片要壓在人物兩側的留白上 |
| 兩側 | **有東西張開填滿畫面**（旗幟／披風／煙塵） | 取代天使的翅膀；沒有它畫面會空、視差沒東西可推 |
| 頭部位置 | 畫面**上方 1/3**、後面有**發光圓盤** | 網頁的 `.halo` 呼吸光暈是疊在那個位置 |
| 背景 | 極淡、無雜物、單一色調 | 玻璃卡片 `backdrop-filter` 糊過去才會好看 |
| 配色 | 象牙白為主，**金＋緋紅為重音** | 目前用的圖有紅斗篷，CSS 已把 `--crimson` 納入系統 |
| 邊緣 | 上下左右**留 5% 空白**，主體不貼邊 | 進場會 scale 1.14 → 1；`contain` 模式下影響已很小，但留白仍比較保險 |

## Prompt（英文，直接貼）

```
Ivory-white marble statue of a Japanese samurai warrior, front-facing, standing
tall and imposing, ornate kabuto helmet with a large golden maedate crest and
golden horns, menpo face mask, elaborate o-yoroi lamellar armor with delicate
gold lacing and gold family crests, long flowing haori cloak, katana held
vertically in front, enormous billowing silk war banners spreading wide to the
left and right like wings and filling the frame, soft glowing golden sun disc
halo behind the helmet, background of swirling pale ivory silk ribbons and cream
mist, cinematic studio lighting, hyper-detailed carved marble, luxury editorial
photography, strictly ivory cream and white palette with warm gold accents only,
centered symmetrical composition, 8k
```

## Negative prompt（有支援的話加）

```
dark background, black, neon, saturated colors, red, blue, multiple characters,
text, watermark, logo, cropped limbs, cluttered background, low contrast,
cartoon, anime, 3d render look
```

## 想換調性時只改這幾格

- **暗黑血戰版**：`ivory cream and white` → `charcoal black and deep crimson`，
  `warm gold` 保留；`marble` → `blackened iron and lacquer`。
  （網頁的 `--ivory` / `--ink` 兩個 CSS 變數對調即可）
- **妖異版**：加 `faint ghostly blue ember particles drifting, yokai mist`
- **武器換薙刀／二刀**：`katana held vertically` → `naginata` / `dual katana crossed`

## 產完怎麼放進去

1. 轉成 `.webp`，寬度壓到 1600px（60KB 上下就夠，主視覺不需要 4K）
2. 打開 `hero-demo.html`，搜尋 `data:image/webp;base64,`（**有兩處**：
   主視覺 `.hero-img` 和右下角特寫卡 `.detail i`），把 base64 換掉
3. 或者更乾淨：把那兩段 `url("data:...")` 改成 `url("/static/hero-samurai.webp")`
