#!/usr/bin/env node
// 站台回歸契約：確保網站「初次載入就看得到內容」以及既有 tab 切換沒被改壞。
//
// 跑法：node tests/site_contract.mjs
// 不需要任何 npm 套件：用 Node 22 內建 WebSocket 直接講 CDP，驅動本機 Chrome headless。
//
// R0 的由來：2026-08-26 發現 init 從未呼叫 switchView() 做初始顯示，
// 而所有 view 的初始 class 都是 "view hidden"，導致網站載入後內容區全空、
// 必須先點一次 tab 才看得到東西。這個 bug 自初始建置就存在、沒有任何測試守著。

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const BASE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE = path.join(BASE, "site");
const HTTP_PORT = 8802;
const CDP_PORT = 9348;

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
               ".json": "application/json", ".webp": "image/webp", ".png": "image/png",
               ".jpg": "image/jpeg", ".svg": "image/svg+xml" };

const CONTRACT = `(async () => {
  const results = [];
  const check = (name, fn) => {
    try { const r = fn(); results.push({ name, ok: r === true, detail: r === true ? "" : String(r) }); }
    catch (e) { results.push({ name, ok: false, detail: "EXCEPTION: " + e.message }); }
  };
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  for (let i = 0; i < 60; i++) {
    if (document.querySelector("#guideSections")?.children.length) break;
    await sleep(100);
  }

  // 最重要的一條：必須放在任何點擊之前
  check("R0 初次載入內容區就可見（不需先點 tab）", () => {
    const v = document.querySelector("#view-guides");
    if (!v) return "找不到 #view-guides";
    if (v.classList.contains("hidden")) return "#view-guides 初次載入就是 hidden — init 沒有做初始 switchView";
    const h = Math.round(v.getBoundingClientRect().height);
    return h > 0 ? true : "#view-guides 可見但高度是 " + h;
  });

  check("R1 恰好一個 view 是顯示的（切換互斥）", () => {
    const shown = [...document.querySelectorAll(".view")].filter(e => !e.classList.contains("hidden"));
    return shown.length === 1 ? true : "顯示中的 view 有 " + shown.length + " 個：" + shown.map(e => e.id).join(",");
  });

  check("R2 五個 tab 按鈕齊全且順序正確", () => {
    const got = [...document.querySelectorAll("nav.tabs .tab")].map(e => e.dataset.tab);
    const want = ["guides", "hot", "new", "bahamut", "tweets"];
    return JSON.stringify(got) === JSON.stringify(want)
      ? true : "實得 " + JSON.stringify(got);
  });

  check("R3 攻略內容有渲染出來（資料流沒斷）", () => {
    const n = document.querySelector("#guideSections")?.children.length ?? 0;
    return n > 0 ? true : "#guideSections 是空的";
  });

  check("R4 點 tab 能切換到對應 view", () => {
    document.querySelector('.tab[data-tab="bahamut"]').click();
    const v = document.querySelector("#view-bahamut");
    const t = document.querySelector('.tab[data-tab="bahamut"]');
    if (!v || v.classList.contains("hidden")) return "#view-bahamut 沒有顯示出來";
    if (!t?.classList.contains("active")) return ".tab[data-tab=bahamut] 沒有 active";
    return true;
  });

  check("R5 切換後原本的 view 已隱藏", () => {
    const v = document.querySelector("#view-guides");
    return v.classList.contains("hidden") ? true : "#view-guides 切走之後仍然顯示";
  });

  return JSON.stringify(results);
})()`;

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map();
    ws.onmessage = e => { const m = JSON.parse(e.data);
      if (m.id && this.pending.has(m.id)) { this.pending.get(m.id)(m); this.pending.delete(m.id); } }; }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise(res => { this.pending.set(id, res);
      this.ws.send(JSON.stringify({ id, method, params })); });
  }
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log("[1/4] 建置靜態站…");
  const venvPy = path.join(BASE, "venv", "bin", "python");
  const py = fs.existsSync(venvPy) ? venvPy : "python3";
  const b = spawnSync(py, [path.join(BASE, "build_site.py")], { cwd: BASE, encoding: "utf8" });
  if (b.status !== 0) { console.error("build_site.py 失敗：", b.stderr); return 2; }
  console.log("      ", b.stdout.trim());

  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(req.url.split("?")[0]);
    const file = path.join(SITE, rel === "/" ? "/index.html" : rel);
    if (!file.startsWith(SITE) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404).end("nope"); return;
    }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] ?? "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(r => server.listen(HTTP_PORT, "127.0.0.1", r));
  console.log(`[2/4] 靜態站起在 127.0.0.1:${HTTP_PORT}`);

  const profile = "/tmp/nioh3-site-test-profile";
  fs.rmSync(profile, { recursive: true, force: true });
  const chrome = spawn("google-chrome", [
    "--headless", "--disable-gpu", "--no-sandbox", "--window-size=1440,900",
    `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
    "--hide-scrollbars", "about:blank",
  ], { stdio: "ignore" });

  let target = null;
  for (let i = 0; i < 60; i++) {
    await sleep(500);
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      target = list.find(t => t.type === "page");
      if (target?.webSocketDebuggerUrl) break;
    } catch { /* chrome 還沒起來 */ }
  }
  if (!target) { console.error("連不上 Chrome CDP"); chrome.kill(); server.close(); return 2; }
  console.log("[3/4] Chrome 已連上，跑契約…");

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const cdp = new CDP(ws);

  await cdp.send("Page.enable");
  await cdp.send("Page.navigate", { url: `http://127.0.0.1:${HTTP_PORT}/index.html` });
  let ready = false;
  for (let i = 0; i < 80; i++) {
    await sleep(500);
    const rs = await cdp.send("Runtime.evaluate", {
      expression: "document.readyState + '|' + location.pathname", returnByValue: true });
    const v = rs.result?.result?.value ?? "";
    if (v.startsWith("complete") && v.includes("/index.html")) { ready = true; break; }
  }
  if (!ready) { console.error("頁面沒有載入完成"); ws.close(); chrome.kill(); server.close(); return 2; }

  const r = await cdp.send("Runtime.evaluate", {
    expression: CONTRACT, awaitPromise: true, returnByValue: true,
  });

  ws.close(); chrome.kill(); server.close();

  if (r.error) { console.error("CDP 回錯誤：", JSON.stringify(r.error, null, 2)); return 2; }
  if (!r.result) { console.error("CDP 回應非預期：", JSON.stringify(r).slice(0, 600)); return 2; }
  if (r.result?.exceptionDetails) {
    console.error("契約腳本自己爆了：", JSON.stringify(r.result.exceptionDetails, null, 2));
    return 2;
  }
  const results = JSON.parse(r.result.result.value);
  console.log("[4/4] 契約結果：\n");
  let passed = 0;
  for (const x of results) {
    console.log(`  [${x.ok ? "PASS" : "FAIL"}] ${x.name}`);
    if (!x.ok) console.log(`         → ${x.detail}`);
    passed += x.ok ? 1 : 0;
  }
  console.log(`\n  ${passed}/${results.length} 通過`);
  return passed === results.length ? 0 : 1;
}

main().then(c => process.exit(c)).catch(e => { console.error(e); process.exit(2); });
