import { api, ApiError } from "./api/client.js";
import { dateText, duration, hours, money, monthOf, today } from "./utils/format.js";
import "./styles/main.css";

const app = document.querySelector("#app");
const timerStorageKey = "flowfolio-practice-timer";
const navItems = [
  ["dashboard", "總覽", "⌂"],
  ["works", "工作紀錄", "▣"],
  ["quotes", "報價", "◇"],
  ["portfolio", "作品集", "▧"],
  ["practice", "練習", "♫"],
  ["todos", "待辦", "✓"],
  ["analytics", "分析", "◒"],
  ["settings", "設定", "⚙"],
];

const state = {
  route: location.hash.replace(/^#\/?/, "") || "dashboard",
  month: monthOf(),
  date: today(),
  workEditing: null,
  practiceEditing: null,
  portfolioEditing: null,
  timer: loadTimer(),
  timerInterval: null,
  quoteDirty: false,
};

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(props).forEach(([key, value]) => {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "htmlFor") node.htmlFor = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  });
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child === null || child === undefined) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function button(label, className = "secondary", onClick, type = "button") {
  const variants = className.replace(/^button\s+/, "");
  return el("button", { className: `c-button ${variants}`, type, onClick, text: label });
}

function field(label, type, name, value = "", options = {}) {
  const wrapper = el("label", { className: "c-field" });
  wrapper.append(el("span", { className: "c-field-label", text: label }));
  const input = el(type === "textarea" ? "textarea" : "input", {
    id: options.id || name,
    name,
    type: type === "textarea" ? undefined : type,
    value: type === "textarea" ? undefined : value,
    placeholder: options.placeholder,
    min: options.min,
    max: options.max,
    step: options.step,
    required: options.required,
    className: "c-input",
  });
  if (type === "textarea") input.textContent = value;
  if (options.rows) input.rows = options.rows;
  wrapper.append(input);
  return wrapper;
}

function selectField(label, name, options, value) {
  const wrapper = el("label", { className: "c-field" });
  wrapper.append(el("span", { className: "c-field-label", text: label }));
  const select = el("select", { className: "c-input", name });
  options.forEach(([optionValue, optionLabel]) => {
    const option = el("option", { value: optionValue, text: optionLabel });
    if (String(optionValue) === String(value)) option.selected = true;
    select.append(option);
  });
  wrapper.append(select);
  return wrapper;
}

function setValue(container, selector, value) {
  const target = container.querySelector(selector);
  if (target) target.value = value ?? "";
}

function getValue(container, selector) {
  return container.querySelector(selector)?.value?.trim() || "";
}

function formatError(error) {
  if (error instanceof ApiError) return error.message;
  return "目前無法完成操作，請確認後端服務仍在執行。";
}

function toast(message, type = "success") {
  const area = document.querySelector("#toast-area") || document.body.appendChild(el("div", { id: "toast-area" }));
  const item = el("div", { className: `toast ${type}`, text: message });
  area.append(item);
  window.setTimeout(() => item.remove(), 3600);
}

function setLoading(container, message = "載入中…") {
  container.replaceChildren(el("div", { className: "loading", text: message }));
}

function emptyState(message, action) {
  const box = el("div", { className: "empty-state" });
  box.append(el("div", { className: "empty-icon", text: "○" }), el("h3", { text: message }));
  if (action) box.append(action);
  return box;
}

function pageFrame(eyebrow, title, description = "") {
  const frame = el("div", { className: "page-frame" });
  const header = el("header", { className: "page-header" });
  const copy = el("div", {});
  copy.append(el("div", { className: "c-eyebrow", text: eyebrow }), el("h1", { text: title }));
  if (description) copy.append(el("p", { className: "page-description", text: description }));
  header.append(copy);
  frame.append(header);
  return frame;
}

function card(title, subtitle = "") {
  const node = el("section", { className: "c-card" });
  if (title) {
    const header = el("div", { className: "c-card-header" });
    const copy = el("div", {});
    copy.append(el("h2", { text: title }));
    if (subtitle) copy.append(el("p", { className: "muted", text: subtitle }));
    header.append(copy);
    node.append(header);
  }
  return node;
}

function renderShell() {
  const active = navItems.some(([key]) => key === state.route) ? state.route : "dashboard";
  state.route = active;
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand"><span class="brand-mark">F</span><div><strong>Flowfolio</strong><small>工作與練習節奏</small></div></div>
        <nav class="sidebar-nav" aria-label="主要導覽"></nav>
        <div class="sidebar-footer"><span class="status-dot"></span><span>私人本機模式</span></div>
      </aside>
      <main class="main-content"><div id="page"></div></main>
      <nav class="mobile-nav" aria-label="手機導覽"></nav>
    </div>
    <div id="toast-area" aria-live="polite"></div>
  `;
  const sidebarNav = app.querySelector(".sidebar-nav");
  const mobileNav = app.querySelector(".mobile-nav");
  navItems.forEach(([key, label, icon]) => {
    const link = el("a", { className: `nav-link ${active === key ? "active" : ""}`, href: `#/${key}` });
    link.append(el("span", { className: "nav-icon", text: icon }), el("span", { text: label }));
    sidebarNav.append(link);
    const mobileLink = el("a", { className: active === key ? "active" : "", href: `#/${key}`, "aria-label": label });
    mobileLink.append(el("span", { text: icon }), el("small", { text: label }));
    mobileNav.append(mobileLink);
  });
  renderPage(app.querySelector("#page"));
}

function renderPage(outlet) {
  const pages = { dashboard: renderDashboard, works: renderWorks, quotes: renderQuotes, portfolio: renderPortfolio, practice: renderPractice, todos: renderTodos, analytics: renderAnalytics, settings: renderSettings };
  (pages[state.route] || renderDashboard)(outlet);
}

function statCard(label, value, detail, accent) {
  const node = el("article", { className: `stat-card accent-${accent}` });
  node.append(el("span", { className: "stat-label", text: label }), el("strong", { className: "stat-value", text: value }), el("span", { className: "stat-detail", text: detail }));
  return node;
}

async function renderDashboard(outlet) {
  const frame = pageFrame("今天的工作台", "把工作、練習與生活放在同一個節奏裡", "收入與工作時數分開計算，練習時間也維持自己的單位。");
  const controls = el("div", { className: "toolbar dashboard-toolbar" });
  controls.append(field("統計月份", "month", "month", state.month), field("查看日期", "date", "date", state.date));
  controls.append(button("重新整理", "button secondary", () => load()));
  frame.querySelector(".page-header").append(controls);
  const stats = el("div", { className: "stats-grid" });
  const body = el("div", { className: "dashboard-grid" });
  const dailyCard = card("指定日期的安排", "待辦、工作與練習各自保留來源。");
  const recentCard = card("最近活動", "依建立時間顯示最近 8 筆紀錄。");
  const dailyList = el("div", { className: "stack-list" });
  const recentList = el("div", { className: "stack-list" });
  dailyCard.append(dailyList);
  recentCard.append(recentList);
  body.append(dailyCard, recentCard);
  frame.append(stats, body);
  outlet.replaceChildren(frame);

  const monthInput = controls.querySelector('[name="month"]');
  const dateInput = controls.querySelector('[name="date"]');
  async function load() {
    state.month = monthInput.value || monthOf();
    state.date = dateInput.value || today();
    setLoading(stats, "讀取統計…");
    try {
      const data = await api(`/api/v1/dashboard?month=${encodeURIComponent(state.month)}&selected_date=${state.date}`);
      stats.replaceChildren(
        statCard("本月收入", money(data.income), "工作紀錄收入合計", "teal"),
        statCard("本月工作時數", hours(data.work_minutes), "不含練琴時間", "blue"),
        statCard("本月練習時間", duration(data.practice_seconds), "獨立以秒儲存", "violet"),
        statCard("當日完成率", `${data.completion_rate}%`, `${data.date} 的已完成項目`, "amber"),
      );
      dailyList.replaceChildren();
      if (!data.daily.length) dailyList.append(emptyState("這一天還沒有安排", button("新增待辦", "button primary small", () => (location.hash = "#/todos"))));
      data.daily.forEach((item) => {
        const title = item.kind === "todo" ? item.title : item.kind === "work" ? item.name : item.piece;
        const detail = item.kind === "todo" ? `${item.time || "未排時間"}${item.location ? ` · ${item.location}` : ""}` : item.kind === "work" ? `${item.type} · ${money(item.income)}` : duration(item.duration_seconds);
        const row = el("div", { className: `list-row ${item.completed ? "is-done" : ""}` });
        row.append(el("span", { className: `kind-dot ${item.kind}`, text: item.kind === "todo" ? "待" : item.kind === "work" ? "工" : "練" }), el("div", { className: "row-main" }, [el("strong", { text: title }), el("small", { text: detail })]));
        if (item.kind === "todo") row.append(button(item.completed ? "已完成" : "完成", "button ghost small", async () => { await api(`/api/v1/todos/${item.id}`, { method: "PATCH", body: { completed: !item.completed } }); load(); }));
        dailyList.append(row);
      });
      recentList.replaceChildren();
      if (!data.recent.length) recentList.append(emptyState("還沒有活動紀錄"));
      data.recent.forEach((item) => {
        const row = el("div", { className: "list-row" });
        row.append(el("span", { className: `kind-dot ${item.kind}`, text: item.kind === "work" ? "工" : "練" }), el("div", { className: "row-main" }, [el("strong", { text: item.title }), el("small", { text: `${item.kind === "work" ? "工作" : "練習"} · ${dateText(item.date)}` })]));
        recentList.append(row);
      });
    } catch (error) {
      stats.replaceChildren(emptyState(formatError(error), button("再試一次", "button secondary", load)));
      dailyList.replaceChildren();
      recentList.replaceChildren();
    }
  }
  monthInput.addEventListener("change", load);
  dateInput.addEventListener("change", load);
  load();
}

function workForm(editing = null) {
  const form = el("form", { className: "form-grid", id: "work-form" });
  form.append(field("日期", "date", "date", editing?.date || today(), { required: true }), field("工作名稱", "text", "name", editing?.name || "", { required: true, placeholder: "例如：品牌視覺整理" }), selectField("工作類型", "type", [["一般", "一般"], ["攝影", "攝影"], ["設計", "設計"], ["活動", "活動"], ["音樂", "音樂"]], editing?.type || "一般"), field("收入（TWD）", "number", "income", editing?.income || "0", { min: 0, step: 1 }), field("工作時數", "number", "hours", editing?.hours || "0", { min: 0, step: 0.25 }), field("備註", "textarea", "notes", editing?.notes || "", { rows: 3 }));
  const actions = el("div", { className: "form-actions" });
  actions.append(button(editing ? "儲存修改" : "新增工作", "button primary", undefined, "submit"));
  if (editing) actions.append(button("取消編輯", "button secondary", () => { state.workEditing = null; renderShell(); }));
  form.append(actions);
  return form;
}

async function renderWorks(outlet) {
  const frame = pageFrame("Works", "工作紀錄", "用穩定 ID 管理每一筆工作，收入與工作時數分開統計。");
  const layout = el("div", { className: "two-column" });
  const formCard = card(state.workEditing ? "編輯工作" : "新增工作");
  formCard.append(workForm(state.workEditing));
  const listCard = card("工作清單", "可搜尋名稱、類型與備註。");
  const search = field("搜尋", "search", "search", "", { placeholder: "輸入關鍵字" });
  listCard.querySelector(".c-card-header").append(search);
  const list = el("div", { className: "table-wrap" });
  listCard.append(list);
  layout.append(formCard, listCard);
  frame.append(layout);
  outlet.replaceChildren(frame);
  const form = frame.querySelector("#work-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = { date: getValue(form, '[name="date"]'), name: getValue(form, '[name="name"]'), type: getValue(form, '[name="type"]'), income: getValue(form, '[name="income"]') || "0", hours: getValue(form, '[name="hours"]') || "0", notes: getValue(form, '[name="notes"]') };
    try {
      await api(state.workEditing ? `/api/v1/works/${state.workEditing.id}` : "/api/v1/works", { method: state.workEditing ? "PATCH" : "POST", body });
      toast(state.workEditing ? "工作紀錄已更新" : "工作紀錄已新增");
      state.workEditing = null;
      renderShell();
    } catch (error) { toast(formatError(error), "error"); }
  });
  async function load() {
    try {
      const items = await api(`/api/v1/works?search=${encodeURIComponent(getValue(frame, '[name="search"]'))}`);
      renderWorkTable(list, items);
    } catch (error) { list.replaceChildren(emptyState(formatError(error), button("再試一次", "button secondary", load))); }
  }
  search.querySelector("input").addEventListener("input", () => { window.clearTimeout(search._timer); search._timer = window.setTimeout(load, 250); });
  await load();
}

function renderWorkTable(container, items) {
  if (!items.length) { container.replaceChildren(emptyState("還沒有工作紀錄")); return; }
  const table = el("table", {});
  const head = el("thead", {}); head.append(el("tr", {}, ["日期", "工作", "類型", "收入", "時數", "操作"].map((text) => el("th", { text })))); table.append(head);
  const body = el("tbody", {});
  items.forEach((item) => {
    const row = el("tr", {});
    row.append(el("td", { text: dateText(item.date) }), el("td", {}, [el("strong", { text: item.name }), el("small", { className: "table-note", text: item.notes || "" })]), el("td", { text: item.type }), el("td", { className: "numeric", text: money(item.income) }), el("td", { className: "numeric", text: `${Number(item.hours || 0).toFixed(2)} h` }));
    const actions = el("td", { className: "actions" });
    actions.append(button("編輯", "button ghost small", () => { state.workEditing = item; renderShell(); }), button("刪除", "button danger small", async () => { if (!confirm("確定要刪除這筆工作紀錄嗎？")) return; try { await api(`/api/v1/works/${item.id}`, { method: "DELETE" }); toast("工作紀錄已刪除"); renderShell(); } catch (error) { toast(formatError(error), "error"); } }));
    row.append(actions); body.append(row);
  });
  table.append(body); container.replaceChildren(table);
}

function todoForm(editing = null) {
  const form = el("form", { className: "form-grid", id: "todo-form" });
  form.append(field("日期", "date", "date", editing?.date || state.date, { required: true }), field("時間", "time", "time", editing?.time || ""), field("標題", "text", "title", editing?.title || "", { required: true, placeholder: "例如：寄出報價單" }), field("地點", "text", "location", editing?.location || ""));
  const actions = el("div", { className: "form-actions" }); actions.append(button(editing ? "儲存修改" : "新增待辦", "button primary", undefined, "submit")); if (editing) actions.append(button("取消編輯", "button secondary", () => { state.todoEditing = null; renderShell(); })); form.append(actions); return form;
}

async function renderTodos(outlet) {
  const frame = pageFrame("Todos", "待辦事項", "把日期、時間與地點保留在同一筆資料裡，完成狀態可直接回寫。");
  const layout = el("div", { className: "two-column" });
  const formCard = card(state.todoEditing ? "編輯待辦" : "新增待辦"); formCard.append(todoForm(state.todoEditing));
  const listCard = card("待辦清單", "按日期與時間排序。"); const list = el("div", { className: "stack-list" }); listCard.append(list); layout.append(formCard, listCard); frame.append(layout); outlet.replaceChildren(frame);
  const form = frame.querySelector("#todo-form");
  form.addEventListener("submit", async (event) => { event.preventDefault(); const body = { date: getValue(form, '[name="date"]'), time: getValue(form, '[name="time"]') || null, title: getValue(form, '[name="title"]'), location: getValue(form, '[name="location"]') }; try { await api(state.todoEditing ? `/api/v1/todos/${state.todoEditing.id}` : "/api/v1/todos", { method: state.todoEditing ? "PATCH" : "POST", body }); toast("待辦已儲存"); state.todoEditing = null; renderShell(); } catch (error) { toast(formatError(error), "error"); } });
  try { const items = await api("/api/v1/todos"); list.replaceChildren(); if (!items.length) list.append(emptyState("目前沒有待辦")); items.forEach((item) => { const row = el("div", { className: `list-row ${item.completed ? "is-done" : ""}` }); const check = el("input", { type: "checkbox" }); check.checked = item.completed; check.addEventListener("change", async () => { await api(`/api/v1/todos/${item.id}`, { method: "PATCH", body: { completed: check.checked } }); renderShell(); }); row.append(check, el("div", { className: "row-main" }, [el("strong", { text: item.title }), el("small", { text: `${dateText(item.date)}${item.time ? ` · ${item.time}` : ""}${item.location ? ` · ${item.location}` : ""}` })]), button("編輯", "button ghost small", () => { state.todoEditing = item; renderShell(); }), button("刪除", "button danger small", async () => { if (!confirm("確定要刪除這個待辦嗎？")) return; await api(`/api/v1/todos/${item.id}`, { method: "DELETE" }); toast("待辦已刪除"); renderShell(); })); list.append(row); }); } catch (error) { list.replaceChildren(emptyState(formatError(error))); }
}

function loadTimer() {
  try {
    const saved = JSON.parse(localStorage.getItem(timerStorageKey) || "null");
    if (!saved) return { running: false, accumulated: 0, startedAt: null, piece: "", notes: "" };
    if (saved.running && saved.startedAt) saved.accumulated += Math.max(0, (Date.now() - saved.startedAt) / 1000);
    saved.startedAt = saved.running ? Date.now() : null;
    return saved;
  } catch { return { running: false, accumulated: 0, startedAt: null, piece: "", notes: "" }; }
}

function timerSeconds() { return state.timer.running ? state.timer.accumulated + Math.max(0, (Date.now() - state.timer.startedAt) / 1000) : state.timer.accumulated; }
function saveTimerSnapshot() { localStorage.setItem(timerStorageKey, JSON.stringify({ ...state.timer, accumulated: timerSeconds(), startedAt: state.timer.running ? Date.now() : null })); }
function resetTimer() { state.timer = { running: false, accumulated: 0, startedAt: null, piece: "", notes: "" }; localStorage.removeItem(timerStorageKey); }

async function renderPractice(outlet) {
  const frame = pageFrame("Practice", "練習計時器", "計時狀態會留在瀏覽器快照中；儲存後才會寫入 SQLite 練習紀錄。");
  const layout = el("div", { className: "two-column practice-layout" });
  const timerCard = card("今天練什麼？", "重新整理或手機切到背景後，仍會依時間戳恢復。");
  const form = el("form", { className: "practice-form", id: "practice-form" });
  form.append(field("曲目", "text", "piece", state.practiceEditing?.piece || state.timer.piece || "", { required: true, placeholder: "例如：Chopin Nocturne Op.9 No.2" }), field("練習心得", "textarea", "notes", state.practiceEditing?.notes || state.timer.notes || "", { rows: 4 }));
  const display = el("div", { className: "timer-display", text: duration(state.practiceEditing ? state.practiceEditing.duration_seconds : timerSeconds()) });
  const status = el("div", { className: "timer-status", text: state.timer.running ? "計時中" : state.practiceEditing ? "編輯歷史紀錄" : "待機中" });
  const timerActions = el("div", { className: "form-actions center" });
  const toggle = button(state.timer.running ? "暫停" : "開始練習", `button ${state.timer.running ? "warning" : "primary"}`, () => { const piece = getValue(form, '[name="piece"]'); if (!piece) { toast("請先輸入曲目", "error"); return; } state.timer.piece = piece; state.timer.notes = getValue(form, '[name="notes"]'); if (state.timer.running) { state.timer.accumulated = timerSeconds(); state.timer.running = false; state.timer.startedAt = null; } else { state.timer.running = true; state.timer.startedAt = Date.now(); } saveTimerSnapshot(); renderShell(); });
  timerActions.append(toggle);
  if (state.practiceEditing) timerActions.append(button("儲存修改", "button secondary", async () => { try { await api(`/api/v1/practice/${state.practiceEditing.id}`, { method: "PATCH", body: { piece: getValue(form, '[name="piece"]'), notes: getValue(form, '[name="notes"]') } }); toast("練習紀錄已更新"); state.practiceEditing = null; renderShell(); } catch (error) { toast(formatError(error), "error"); } }));
  else timerActions.append(button("結束並儲存", "button secondary", async () => { const piece = getValue(form, '[name="piece"]'); if (!piece) { toast("請先輸入曲目", "error"); return; } const seconds = Math.round(timerSeconds()); try { await api("/api/v1/practice", { method: "POST", body: { date: today(), piece, notes: getValue(form, '[name="notes"]'), duration_seconds: seconds } }); toast(`已儲存 ${duration(seconds)} 的練習`); resetTimer(); renderShell(); } catch (error) { toast(formatError(error), "error"); } }));
  if (state.timer.accumulated > 0 && !state.practiceEditing) timerActions.append(button("清除計時", "button ghost small", () => { if (confirm("清除尚未儲存的計時？")) { resetTimer(); renderShell(); } }));
  form.append(status, display, timerActions); timerCard.append(form);
  const historyCard = card("練習歷史", "時間以整數秒儲存，畫面再轉為時分秒。"); const history = el("div", { className: "stack-list" }); historyCard.append(history); layout.append(timerCard, historyCard); frame.append(layout); outlet.replaceChildren(frame);
  if (state.timer.running) { window.clearInterval(state.timerInterval); state.timerInterval = window.setInterval(() => { display.textContent = duration(timerSeconds()); saveTimerSnapshot(); }, 500); }
  else window.clearInterval(state.timerInterval);
  try { const items = await api("/api/v1/practice"); if (!items.length) history.append(emptyState("還沒有練習紀錄")); items.forEach((item) => { const row = el("div", { className: "list-row" }); row.append(el("span", { className: "kind-dot practice", text: "練" }), el("div", { className: "row-main" }, [el("strong", { text: item.piece }), el("small", { text: `${dateText(item.date)} · ${duration(item.duration_seconds)}${item.notes ? ` · ${item.notes}` : ""}` })]), button("編輯", "button ghost small", () => { state.practiceEditing = item; renderShell(); }), button("刪除", "button danger small", async () => { if (!confirm("確定要刪除這筆練習紀錄嗎？")) return; await api(`/api/v1/practice/${item.id}`, { method: "DELETE" }); toast("練習紀錄已刪除"); renderShell(); })); history.append(row); }); } catch (error) { history.append(emptyState(formatError(error))); }
}

function quoteItemRow(item = {}) {
  const row = el("div", { className: "quote-item-row" });
  row.append(field("項目", "text", "description", item.description || "", { required: true, placeholder: "服務項目" }), field("數量", "number", "quantity", item.quantity || "1", { min: 0.001, step: 0.001 }), field("單價", "number", "unit_price", item.unit_price || "0", { min: 0, step: 1 }), button("移除", "button danger small", () => { row.remove(); updateQuotePreview(); }));
  row.querySelectorAll("input").forEach((input) => input.addEventListener("input", updateQuotePreview));
  return row;
}

function quotePayload(form) {
  return { quote_number: getValue(form, '[name="quote_number"]'), client_name: getValue(form, '[name="client_name"]'), quote_date: getValue(form, '[name="quote_date"]'), tax_rate_percent: getValue(form, '[name="tax_rate_percent"]') || "0", deposit_percent: Number(getValue(form, '[name="deposit_percent"]') || 0), notes: getValue(form, '[name="notes"]'), items: [...form.querySelectorAll(".quote-item-row")].map((row) => ({ description: getValue(row, '[name="description"]'), quantity: getValue(row, '[name="quantity"]') || "1", unit_price: getValue(row, '[name="unit_price"]') || "0" })) };
}

function updateQuotePreview() {
  const form = document.querySelector("#quote-form"); const target = document.querySelector("#quote-preview"); if (!form || !target) return;
  const items = quotePayload(form).items; const subtotal = items.reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0); const tax = subtotal * Number(getValue(form, '[name="tax_rate_percent"]') || 0) / 100; const total = Math.round(subtotal + tax); const deposit = Math.round(total * Number(getValue(form, '[name="deposit_percent"]') || 0) / 100); target.replaceChildren(el("div", { className: "summary-line", text: `小計 ${money(subtotal)}` }), el("div", { className: "summary-line", text: `稅額 ${money(tax)}` }), el("div", { className: "summary-total", text: `總額 ${money(total)}` }), el("div", { className: "summary-line", text: `訂金 ${money(deposit)} · 尾款 ${money(total - deposit)}` }));
}

async function renderQuotes(outlet) {
  const frame = pageFrame("Quotes", "報價工作台", "後端以整數 TWD 與 Decimal 規則計價；前端預覽只服務操作感受。");
  const layout = el("div", { className: "two-column quote-layout" });
  const editor = card(state.quoteEditing ? "編輯報價" : "建立報價草稿");
  const form = el("form", { className: "form-grid", id: "quote-form" });
  const editing = state.quoteEditing;
  form.append(field("報價編號", "text", "quote_number", editing?.quote_number || `Q-${new Date().toISOString().slice(0, 10).replaceAll("-", "")}`, { required: true }), field("客戶名稱", "text", "client_name", editing?.client_name || "", { required: true }), field("報價日期", "date", "quote_date", editing?.quote_date || today(), { required: true }), field("稅率（%）", "number", "tax_rate_percent", editing?.tax_rate_percent || "0", { min: 0, max: 100, step: 0.1 }), field("訂金比例（%）", "number", "deposit_percent", editing?.deposit_percent ?? "30", { min: 0, max: 100, step: 1 }), field("備註", "textarea", "notes", editing?.notes || "", { rows: 3 }));
  const itemHeader = el("div", { className: "section-inline" }); itemHeader.append(el("h3", { text: "服務項目" }), button("新增項目", "button secondary small", () => { items.append(quoteItemRow()); updateQuotePreview(); }));
  const items = el("div", { className: "quote-items", id: "quote-items" }); (editing?.items || [{ description: "", quantity: "1", unit_price: "0" }]).forEach((item) => items.append(quoteItemRow(item))); const preview = el("div", { className: "quote-preview", id: "quote-preview" });
  form.append(itemHeader, items, preview); const actions = el("div", { className: "form-actions" }); actions.append(button(editing ? "儲存報價" : "儲存草稿", "button primary", undefined, "submit")); if (editing) actions.append(button("取消編輯", "button secondary", () => { state.quoteEditing = null; state.quoteDirty = false; renderShell(); })); form.append(actions); editor.append(form);
  const listCard = card("報價歷史", "編號唯一，匯出從後端最新資料產生。"); const list = el("div", { className: "stack-list" }); listCard.append(list); layout.append(editor, listCard); frame.append(layout); outlet.replaceChildren(frame);
  form.addEventListener("input", () => { state.quoteDirty = true; updateQuotePreview(); }); form.addEventListener("submit", async (event) => { event.preventDefault(); try { await api(state.quoteEditing ? `/api/v1/quotes/${state.quoteEditing.id}` : "/api/v1/quotes", { method: state.quoteEditing ? "PATCH" : "POST", body: quotePayload(form) }); toast("報價已儲存"); state.quoteEditing = null; state.quoteDirty = false; renderShell(); } catch (error) { toast(formatError(error), "error"); } }); updateQuotePreview();
  try { const itemsData = await api("/api/v1/quotes"); if (!itemsData.length) list.append(emptyState("還沒有報價草稿")); itemsData.forEach((item) => { const row = el("div", { className: "list-row quote-list-row" }); row.append(el("div", { className: "row-main" }, [el("strong", { text: item.quote_number }), el("small", { text: `${item.client_name} · ${dateText(item.quote_date)} · ${money(item.totals.total)}` })])); const actions = el("div", { className: "actions" }); actions.append(button("編輯", "button ghost small", () => { state.quoteEditing = item; renderShell(); }), button("複製", "button ghost small", async () => { await api(`/api/v1/quotes/${item.id}/duplicate`, { method: "POST" }); toast("報價已複製"); renderShell(); }), el("a", { className: "c-button ghost small", href: `/api/v1/quotes/${item.id}/export.pdf`, text: "PDF" }), el("a", { className: "c-button ghost small", href: `/api/v1/quotes/${item.id}/export.csv`, text: "CSV" }), button("刪除", "button danger small", async () => { if (!confirm("確定要刪除這份報價嗎？")) return; await api(`/api/v1/quotes/${item.id}`, { method: "DELETE" }); toast("報價已刪除"); renderShell(); })); row.append(actions); list.append(row); }); } catch (error) { list.append(emptyState(formatError(error))); }
}

async function renderPortfolio(outlet) {
  const frame = pageFrame("Portfolio", "私人作品集", "作品只存於本機資料目錄；圖片透過 media ID 取用，不暴露磁碟路徑。");
  const layout = el("div", { className: "two-column portfolio-layout" }); const formCard = card(state.portfolioEditing ? "編輯作品資訊" : "新增作品"); const form = el("form", { className: "form-grid", id: "portfolio-form" }); const editing = state.portfolioEditing;
  form.append(field("日期", "date", "date", editing?.date || today(), { required: true }), field("時間", "time", "time", editing?.time || ""), field("作品名稱", "text", "project", editing?.project || "", { required: true }), field("分類", "text", "category", editing?.category || "未分類"), field("內容摘要", "textarea", "content", editing?.content || "", { rows: 5 }));
  const fileField = field("圖片（可多選）", "file", "files", "", {}); fileField.querySelector("input").multiple = true; fileField.querySelector("input").accept = "image/jpeg,image/png,image/webp"; form.append(fileField); const actions = el("div", { className: "form-actions" }); actions.append(button(editing ? "儲存作品資訊" : "新增作品", "button primary", undefined, "submit")); if (editing) actions.append(button("取消編輯", "button secondary", () => { state.portfolioEditing = null; renderShell(); })); form.append(actions); formCard.append(form);
  const listCard = card("作品牆", "支援搜尋、縮圖與圖片預覽。"); const search = field("搜尋", "search", "search", "", { placeholder: "搜尋名稱、分類或內容" }); listCard.querySelector(".c-card-header").append(search); const grid = el("div", { className: "portfolio-grid" }); listCard.append(grid); layout.append(formCard, listCard); frame.append(layout); outlet.replaceChildren(frame);
  form.addEventListener("submit", async (event) => { event.preventDefault(); const body = { date: getValue(form, '[name="date"]'), time: getValue(form, '[name="time"]') || null, project: getValue(form, '[name="project"]'), category: getValue(form, '[name="category"]') || "未分類", content: getValue(form, '[name="content"]') }; try { const saved = await api(editing ? `/api/v1/portfolio/${editing.id}` : "/api/v1/portfolio", { method: editing ? "PATCH" : "POST", body }); const files = form.querySelector('[name="files"]').files; if (!editing && files.length) { const data = new FormData(); [...files].forEach((file) => data.append("files", file)); await api(`/api/v1/portfolio/${saved.id}/media`, { method: "POST", body: data }); } toast("作品已儲存"); state.portfolioEditing = null; renderShell(); } catch (error) { toast(formatError(error), "error"); } });
  async function load() { try { const items = await api(`/api/v1/portfolio?search=${encodeURIComponent(getValue(frame, '[name="search"]'))}`); renderPortfolioGrid(grid, items); } catch (error) { grid.replaceChildren(emptyState(formatError(error))); } }
  search.querySelector("input").addEventListener("input", () => { window.clearTimeout(search._timer); search._timer = window.setTimeout(load, 250); }); await load();
}

function renderPortfolioGrid(grid, items) {
  grid.replaceChildren(); if (!items.length) { grid.append(emptyState("還沒有作品")); return; }
  items.forEach((item) => { const cardNode = el("article", { className: "portfolio-card" }); const visual = el("div", { className: "portfolio-visual" }); if (item.media?.length) { const image = el("img", { src: item.media[0].url, alt: item.project }); image.addEventListener("click", () => openImageViewer(item.media, 0)); visual.append(image); if (item.media.length > 1) visual.append(el("span", { className: "media-count", text: `+${item.media.length - 1}` })); } else visual.append(el("span", { className: "visual-placeholder", text: "作品" })); const body = el("div", { className: "portfolio-body" }); body.append(el("div", { className: "c-eyebrow", text: item.category }), el("h3", { text: item.project }), el("p", { text: item.content || "尚未填寫內容" }), el("small", { className: "muted", text: `${dateText(item.date)}${item.time ? ` · ${item.time}` : ""}` })); const actions = el("div", { className: "actions" }); actions.append(button("編輯", "ghost small", () => { state.portfolioEditing = item; renderShell(); }), button("刪除", "danger small", async () => { if (!confirm("確定要刪除這件作品與其圖片嗎？")) return; await api(`/api/v1/portfolio/${item.id}`, { method: "DELETE" }); toast("作品已刪除"); renderShell(); })); body.append(actions); cardNode.append(visual, body); grid.append(cardNode); });
}

function openImageViewer(media, index) {
  const dialog = el("dialog", { className: "image-dialog" }); const image = el("img", { src: media[index].url, alt: media[index].original_name }); const close = button("關閉", "button secondary", () => dialog.close()); dialog.append(image, el("div", { className: "dialog-actions" }, [close])); document.body.append(dialog); dialog.showModal(); dialog.addEventListener("close", () => dialog.remove(), { once: true });
}

async function renderAnalytics(outlet) {
  const frame = pageFrame("Analytics", "數據分析", "只呈現有來源可追溯的月度收入、工作時數與練習時間。"); const chartCard = card("近六個月", "工作與練習維持不同的單位。"); const chart = el("div", { className: "bar-chart" }); chartCard.append(chart); frame.append(chartCard); outlet.replaceChildren(frame);
  try { const rows = await api("/api/v1/analytics/summary?months=6"); const max = Math.max(1, ...rows.map((row) => Math.max(Number(row.income), row.work_minutes, row.practice_seconds / 60))); rows.forEach((row) => { const group = el("div", { className: "bar-group" }); group.append(el("span", { className: "bar-label", text: row.month.slice(5) })); const income = el("div", { className: "bar income", style: `height:${Math.max(4, Number(row.income) / max * 180)}px` }); income.title = `收入 ${money(row.income)}`; const work = el("div", { className: "bar work", style: `height:${Math.max(4, row.work_minutes / max * 180)}px` }); work.title = `工作 ${hours(row.work_minutes)}`; const practice = el("div", { className: "bar practice", style: `height:${Math.max(4, row.practice_seconds / 60 / max * 180)}px` }); practice.title = `練習 ${duration(row.practice_seconds)}`; group.append(el("div", { className: "bar-stack" }, [income, work, practice])); chart.append(group); }); chart.append(el("div", { className: "chart-legend" }, [el("span", { text: "收入" }), el("span", { text: "工作時數" }), el("span", { text: "練習時間" })])); } catch (error) { chart.replaceChildren(emptyState(formatError(error))); }
}

async function renderSettings(outlet) {
  const frame = pageFrame("Settings", "設定與資料維護", "資料庫、媒體與備份都由本機服務管理；還原不提供一鍵覆蓋，避免誤操作。"); const grid = el("div", { className: "settings-grid" }); const health = card("服務狀態", "只顯示非敏感資訊。"); const actions = card("資料操作", "匯出 JSON 可作為人工檢查或搬遷輸入；備份會使用 SQLite Online Backup API。"); const docs = card("Windows 操作", "正式服務只監聽 127.0.0.1，遠端存取請依文件確認 Tailscale Serve。");
  const healthText = el("div", { className: "health-panel", text: "檢查中…" }); health.append(healthText); actions.append(el("div", { className: "button-stack" }, [el("a", { className: "c-button primary", href: "/api/v1/maintenance/export", text: "下載資料匯出" }), button("建立備份", "secondary", async () => { try { const result = await api("/api/v1/maintenance/backup", { method: "POST" }); toast(`備份完成：${result.archive_name}`); } catch (error) { toast(formatError(error), "error"); } })])); docs.append(el("p", { className: "muted", text: "可執行 scripts/windows/build-web.ps1 建置前端，再用 scripts/windows/start-prod.ps1 啟動。Tailscale Serve 與工作排程器需由你確認後操作。" })); grid.append(health, actions, docs); frame.append(grid); outlet.replaceChildren(frame);
  try { const result = await api("/health"); healthText.replaceChildren(el("span", { className: "health-ok", text: "● " }), el("strong", { text: "服務正常" }), el("p", { text: `${result.service} · 版本 ${result.version}` })); } catch (error) { healthText.textContent = formatError(error); healthText.classList.add("error-text"); }
}

window.addEventListener("hashchange", () => { state.route = location.hash.replace(/^#\/?/, "") || "dashboard"; if (state.quoteDirty && !confirm("報價表單尚未儲存，確定要離開嗎？")) return; state.quoteDirty = false; renderShell(); });
window.addEventListener("beforeunload", (event) => { if (state.quoteDirty) { event.preventDefault(); event.returnValue = ""; } });
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden" && state.timer.running) saveTimerSnapshot(); });
renderShell();

