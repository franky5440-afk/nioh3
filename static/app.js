const CAT_LABELS = {
  boss: "Boss 攻略", build: "配裝 Build", weapon: "武器流派", beginner: "新手入門",
  walkthrough: "流程任務", collect: "收集要素", trophy: "白金成就", news: "情報更新", general: "綜合",
};

const state = { data: null, guidesLang: "zh", hotLang: "zh", newLang: "zh", guideCategory: "all", activeTab: "guides" };
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  // textContent→innerHTML 只轉義 & < >，不含引號；值會被插進 src/href 屬性，故補上
  return d.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function fmtViews(n) {
  if (typeof n !== "number") return "";
  if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, "") + " 萬觀看";
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "K 觀看";
  return n + " 觀看";
}

const EXT_ICON = '<svg class="ext-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6"/><path d="M10 14L21 3"/></svg>';

function guideCard(g) {
  return `<article class="guide-card">
    <h4><a href="${esc(g.url)}" target="_blank" rel="noopener noreferrer">${esc(g.title)}</a></h4>
    <p class="snippet">${esc(g.snippet)}</p>
    <div class="card-foot">
      <span class="tag gold">${CAT_LABELS[g.category] || esc(g.category)}</span>
      <span>${esc(g.source)}</span><span>${esc(g.found_date)}</span>${EXT_ICON}
    </div>
  </article>`;
}

function videoCard(v, rank) {
  const vid = esc(v.video_id);
  return `<article class="video-card">
    <a class="thumb-link" href="${esc(v.url)}" target="_blank" rel="noopener noreferrer">
      <img class="thumb" src="https://i.ytimg.com/vi/${vid}/mqdefault.jpg" alt="" loading="lazy" referrerpolicy="no-referrer">
      <span class="play-badge"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.14v14l11-7-11-7z"/></svg></span>
      ${rank != null ? `<span class="rank-badge">${rank}</span>` : ""}
    </a>
    <div class="video-info">
      <h4><a href="${esc(v.url)}" target="_blank" rel="noopener noreferrer">${esc(v.title)}</a></h4>
      <div class="video-meta">
        <span class="lang-flag">${v.lang === "zh" ? "中文" : "EN"}</span>
        <span>${esc(v.channel)}</span>
        ${v.views != null ? `<span>👁 ${fmtViews(v.views)}</span>` : ""}
        ${v.date ? `<span>📅 ${esc(v.date)}</span>` : ""}
      </div>
    </div>
  </article>`;
}

document.addEventListener("error", (e) => {
  const img = e.target;
  if (img.tagName === "IMG" && img.classList.contains("thumb")) img.style.visibility = "hidden";
}, true);

/* ---------- renders ---------- */
function renderGuides() {
  const list = state.data[`guides_${state.guidesLang}`] || [];
  const counts = {};
  for (const g of list) counts[g.category] = (counts[g.category] || 0) + 1;
  const cats = ["all", ...Object.keys(CAT_LABELS)];

  $("#guideChips").innerHTML = cats
    .filter((c) => c === "all" || counts[c])
    .map((c) => `<button class="chip ${state.guideCategory === c ? "active" : ""}" data-cat="${c}">${c === "all" ? "全部" : CAT_LABELS[c]} (${c === "all" ? list.length : counts[c]})</button>`)
    .join("");

  const groups = {};
  for (const g of list) {
    if (state.guideCategory !== "all" && g.category !== state.guideCategory) continue;
    (groups[g.category] = groups[g.category] || []).push(g);
  }
  const order = Object.keys(CAT_LABELS).filter((c) => groups[c]);
  $("#guideSections").innerHTML = order.length === 0
    ? '<p class="empty-msg">此分類尚無攻略，等待下次每日掃描。</p>'
    : order.map((cat) => `
      <div class="guide-section">
        <h3>${CAT_LABELS[cat]} <span class="count">${groups[cat].length} 篇</span></h3>
        <div class="card-grid">${groups[cat].map(guideCard).join("")}</div>
      </div>`).join("");
}

function renderVideos() {
  const hot = state.data[`videos_hot_${state.hotLang}`] || [];
  const fresh = state.data[`videos_new_${state.newLang}`] || [];
  $("#hotGrid").innerHTML = hot.length ? hot.map((v, i) => videoCard(v, i + 1)).join("") : '<p class="empty-msg">尚無資料。</p>';
  $("#newGrid").innerHTML = fresh.length ? fresh.map((v) => videoCard(v)).join("") : '<p class="empty-msg">尚無資料。</p>';
}

function renderBahamut() {
  const items = state.data.bahamut || [];
  $("#bahaList").innerHTML = items.length ? items.map((b, i) => `
    <div class="thread-item">
      <span class="thread-num">${i + 1}</span>
      <div class="thread-body">
        <h4><a href="${esc(b.url)}" target="_blank" rel="noopener noreferrer">${esc(b.title)}</a></h4>
        <div class="thread-sub"><span>👤 ${esc(b.author) || "匿名"}</span><span>🕒 ${esc(b.time)}</span></div>
      </div>
      ${b.replies ? `<span class="reply-badge">回應 ${esc(b.replies)}</span>` : ""}
    </div>`).join("") : '<p class="empty-msg">尚無資料。</p>';
}

function renderMeta() {
  const meta = state.data.meta || {};
  const map = {
    guides: ["guides_zh", "guides_en", "guides_ja"],
    videos_hot: ["videos_hot_zh", "videos_hot_en", "videos_hot_ja"],
    videos_new: ["videos_new_zh", "videos_new_en", "videos_new_ja"],
    bahamut: ["bahamut"],
  };
  $$("[data-meta]").forEach((el) => {
    const times = (map[el.dataset.meta] || []).map((k) => meta[k]).filter(Boolean);
    el.textContent = times.length ? `最後更新：${times[0]}` : "尚未更新";
  });
  if (meta._last_run) $("#lastRun").textContent = `上次完整掃描：${meta._last_run}`;
}

/* ---------- search ---------- */
function localSearch(raw) {
  const q = raw.trim().toLowerCase();
  if (!q) return;
  const words = q.split(/\s+/);
  const m = (item, keys) => {
    const hay = keys.map((k) => String(item[k] || "")).join(" ").toLowerCase();
    return words.every((w) => hay.includes(w));
  };
  const byDate = (a, b) => String(b.found_date || "").localeCompare(String(a.found_date || ""));
  const guides = [...(state.data.guides_zh || []), ...(state.data.guides_en || []), ...(state.data.guides_ja || [])]
    .filter((g) => m(g, ["title", "snippet", "source", "category", "found_date"])).sort(byDate).slice(0, 60);
  const hot = [...(state.data.videos_hot_zh || []), ...(state.data.videos_hot_en || []), ...(state.data.videos_hot_ja || [])]
    .filter((v) => m(v, ["title", "channel", "lang"])).slice(0, 20);
  const fresh = [...(state.data.videos_new_zh || []), ...(state.data.videos_new_en || []), ...(state.data.videos_new_ja || [])]
    .filter((v) => m(v, ["title", "channel", "lang"])).slice(0, 20);
  const baha = (state.data.bahamut || [])
    .filter((b) => m(b, ["title", "snippet", "author", "source"])).slice(0, 20);
  return { guides, hot, new: fresh, bahamut: baha, total: guides.length + hot.length + fresh.length + baha.length };
}

async function doSearch(q) {
  q = q.trim();
  if (!q) return;
  const r = localSearch(q);
  $("#searchTitle").textContent = `「${q}」搜尋結果：共 ${r.total} 筆`;
  let html = "";
  if (r.guides.length) html += `<h3 class="group-title">文字 / 圖文攻略（${r.guides.length}）</h3><div class="card-grid">${r.guides.map(guideCard).join("")}</div>`;
  if (r.hot.length) html += `<h3 class="group-title">熱門影片（${r.hot.length}）</h3><div class="video-grid">${r.hot.map((v) => videoCard(v)).join("")}</div>`;
  if (r.new.length) html += `<h3 class="group-title">最新影片（${r.new.length}）</h3><div class="video-grid">${r.new.map((v) => videoCard(v)).join("")}</div>`;
  if (r.bahamut.length) html += `<h3 class="group-title">巴哈討論（${r.bahamut.length}）</h3><div class="thread-list">${r.bahamut.map((b) => `
    <div class="thread-item"><div class="thread-body">
      <h4><a href="${esc(b.url)}" target="_blank" rel="noopener noreferrer">${esc(b.title)}</a></h4>
      <div class="thread-sub"><span>👤 ${esc(b.author) || "匿名"}</span><span>🕒 ${esc(b.time)}</span></div>
    </div></div>`).join("")}</div>`;
  $("#searchResults").innerHTML = html || `<p class="no-result">找不到符合「${esc(q)}」的內容。</p>`;
  switchView("search");
}

function switchView(name) {
  if (name !== "search") state.activeTab = name;
  $$(".view").forEach((el) => el.classList.add("hidden"));
  $(`#view-${name}`).classList.remove("hidden");
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  window.scrollTo({ top: 0 });
}

/* ---------- init ---------- */
document.addEventListener("DOMContentLoaded", async () => {
  state.data = await (await fetch("data/site.json")).json();
  renderGuides(); renderVideos(); renderBahamut(); renderMeta();

  $$(".tab").forEach((t) => t.addEventListener("click", () => switchView(t.dataset.tab)));

  document.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) { state.guideCategory = chip.dataset.cat; renderGuides(); return; }
    const pill = e.target.closest(".pill");
    if (pill) {
      pill.closest(".pill-group").querySelectorAll(".pill").forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state[`${pill.closest(".pill-group").dataset.langFor}Lang`] = pill.dataset.lang;
      renderGuides(); renderVideos();
    }
  });

  $("#searchForm").addEventListener("submit", (e) => { e.preventDefault(); doSearch($("#searchInput").value); });
  $("#clearSearch").addEventListener("click", () => { $("#searchInput").value = ""; switchView(state.activeTab); });
});
