/* Hero 動效：滑鼠視差、捲動推近、光塵粒子。
   設計拆解見 docs/hero-redesign/README.md。
   這支獨立於 app.js：hero 不在頁面上時整支安靜跳過。 */
(() => {
  const hero = document.getElementById("hero");
  if (!hero) return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  /* ---------- 視差：多層不同深度，用 lerp 做出慣性 ---------- */
  const wall = document.getElementById("heroWall");
  const img = document.getElementById("heroImg");
  const layers = [
    { el: wall, d: 5 },                                 // 背景走最慢
    { el: img, d: 18 },
    { el: document.getElementById("heroHalo"), d: 18 }, // 跟人物同步，日輪才不會脫節
    { el: document.getElementById("heroTitle"), d: -8 },
    { el: document.querySelector(".hero-detail"), d: -22 },
  ].filter((l) => l.el);

  let tx = 0, ty = 0, cx = 0, cy = 0, scrollT = 0, t0 = 0;
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);

  addEventListener("pointermove", (e) => {
    tx = (e.clientX / innerWidth - 0.5) * 2;   // -1 .. 1
    ty = (e.clientY / innerHeight - 0.5) * 2;
  }, { passive: true });

  addEventListener("scroll", () => {
    scrollT = Math.min(scrollY / Math.max(hero.offsetHeight, 1), 1);
  }, { passive: true });

  const tick = (now) => {
    if (!t0) t0 = now;
    // 進場的 1.14 → 1.00 推近，跟 CSS 的 blur 淡入同時發生
    const introScale = 1.14 - 0.14 * Math.max(easeOut(Math.min((now - t0 - 100) / 1700, 1)), 0);

    cx += (tx - cx) * 0.055;
    cy += (ty - cy) * 0.055;

    for (const { el, d } of layers) {
      const isWall = el === wall;
      const extra = (el === img || isWall)
        ? ` scale(${(isWall ? 1.15 : 1) * (introScale + scrollT * 0.12)})`
        : ` translateY(${-scrollT * 90}px)`;
      el.style.transform = `translate3d(${cx * d}px, ${cy * d}px, 0)` + extra;
    }
    // 捲出視線後就停手，不必一直算
    if (scrollT < 1) requestAnimationFrame(tick);
    else requestAnimationFrame(() => requestAnimationFrame(tick));
  };
  requestAnimationFrame(tick);

  /* ---------- 光塵粒子 ---------- */
  const cv = document.getElementById("heroMotes");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  let motes = [], W = 0, H = 0;

  const resize = () => {
    const r = devicePixelRatio || 1;
    // 用畫布自己被 inset:0 撐出來的實際尺寸，不要拿 hero.clientWidth 回頭去設
    // style.width —— 兩者在載入早期不一致時，粒子會整片被拉伸。
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w || !h) return;
    W = cv.width = w * r; H = cv.height = h * r;
    motes = Array.from({ length: Math.round(w / 26) }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: (Math.random() * 1.8 + 0.5) * r,
      vy: (Math.random() * 0.22 + 0.06) * r,
      vx: (Math.random() - 0.5) * 0.12 * r,
      a: Math.random() * 0.32 + 0.1,
      ph: Math.random() * Math.PI * 2,
    }));
  };
  resize();
  addEventListener("resize", resize);
  addEventListener("load", resize);   // 字體／圖片載完尺寸才定案

  (function draw(t) {
    requestAnimationFrame(draw);
    if (scrollT >= 1) return;              // hero 捲掉了就不畫
    ctx.clearRect(0, 0, W, H);
    for (const m of motes) {
      m.y += m.vy; m.x += m.vx + Math.sin(t / 1800 + m.ph) * 0.18;
      if (m.y > H + 8) { m.y = -8; m.x = Math.random() * W; }
      ctx.beginPath();
      ctx.fillStyle = `rgba(255,242,214,${m.a * (0.62 + 0.38 * Math.sin(t / 900 + m.ph))})`;
      ctx.shadowBlur = 6; ctx.shadowColor = "rgba(255,226,168,.9)";
      ctx.arc(m.x, m.y, m.r, 0, 6.284);
      ctx.fill();
    }
  })(0);
})();
