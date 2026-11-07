import { api, ApiError } from "./api/client.js";
import { dateText, duration, hours, money, monthOf, today } from "./utils/format.js";
import "./styles/main.css";

const app = document.querySelector("#app");
const navItems = [
  ["dashboard", "總覽", "⌂"],
  ["works", "工作紀錄", "▣"],
  ["portfolio", "作品集", "▧"],
  ["practice", "目標", "◎"],
  ["todos", "待辦", "✓"],
  ["analytics", "分析", "◒"],
  ["settings", "設定", "⚙"],
];

const state = {
  route: location.hash.replace(/^#\/?/, "") || "dashboard",
  month: monthOf(),
  date: today(),
  workEditing: null,
  goalEditing: null,
  portfolioEditing: null,
};

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(props).forEach(([key, value]) => {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "htmlFor") node.htmlFor = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2).toLowerCase(), value);
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
  if (active !== state.route) history.replaceState(null, "", "#/dashboard");
  state.route = active;
  const dashboardHeaderBrandMarkup = active === "dashboard"
    ? '<div class="main-brand-photo"><img src="/assets/flowfolio-wordmark-cropped.jpg" alt="Flowfolio 右上角品牌字樣" /></div>'
    : "";
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand"><div><strong>Flowfolio</strong><small>工作與目標節奏</small></div></div>
        <nav class="sidebar-nav" aria-label="主要導覽"></nav>
        <div class="sidebar-footer"><span class="status-dot"></span><span>私人本機模式</span></div>
      </aside>
      <main class="main-content">${dashboardHeaderBrandMarkup}<div id="page"></div></main>
      <button class="mobile-menu-toggle" type="button" aria-label="開啟手機導覽" aria-expanded="false"><span></span><span></span><span></span></button>
      <nav class="mobile-nav" aria-label="手機導覽"></nav>
    </div>
    <div id="toast-area" aria-live="polite"></div>
  `;
  const sidebarNav = app.querySelector(".sidebar-nav");
  const mobileNav = app.querySelector(".mobile-nav");
  const mobileMenuToggle = app.querySelector(".mobile-menu-toggle");
  const appShell = app.querySelector(".app-shell");
  mobileMenuToggle.addEventListener("click", () => {
    const isOpen = appShell.classList.toggle("mobile-menu-open");
    mobileMenuToggle.setAttribute("aria-expanded", String(isOpen));
    mobileMenuToggle.setAttribute("aria-label", isOpen ? "關閉手機導覽" : "開啟手機導覽");
  });
  navItems.forEach(([key, label, icon]) => {
    const link = el("a", { className: `nav-link ${active === key ? "active" : ""}`, href: `#/${key}`, "aria-label": label, title: label });
    link.append(el("span", { className: "nav-icon", text: icon }), el("span", { text: label }));
    sidebarNav.append(link);
    const mobileLink = el("a", { className: active === key ? "active" : "", href: `#/${key}`, "aria-label": label });
    mobileLink.addEventListener("click", () => {
      appShell.classList.remove("mobile-menu-open");
      mobileMenuToggle.setAttribute("aria-expanded", "false");
      mobileMenuToggle.setAttribute("aria-label", "開啟手機導覽");
    });
    mobileLink.append(el("span", { text: icon }), el("small", { text: label }));
    mobileNav.append(mobileLink);
  });
  renderPage(app.querySelector("#page"));
}

function renderPage(outlet) {
  const pages = { dashboard: renderDashboard, works: renderWorks, portfolio: renderPortfolio, practice: renderGoals, todos: renderTodos, analytics: renderAnalytics, settings: renderSettings };
  (pages[state.route] || renderDashboard)(outlet);
}

function statCard(label, value, detail, accent) {
  const node = el("article", { className: `stat-card accent-${accent}` });
  node.append(el("span", { className: "stat-label", text: label }), el("strong", { className: "stat-value", text: value }), el("span", { className: "stat-detail", text: detail }));
  return node;
}

async function renderDashboard(outlet) {
  const frame = pageFrame("今天的工作台", "目標與生活\n放在同一個節奏裡~", "收入、工作時數與目標狀態各自保留來源。");
  frame.querySelector("h1").classList.add("dashboard-title");
  const controls = el("div", { className: "toolbar dashboard-toolbar" });
  controls.append(field("統計月份", "month", "month", state.month), field("查看日期", "date", "date", state.date));
  controls.append(button("重新整理", "button secondary", () => load()));
  frame.querySelector(".page-header").append(controls);
  const stats = el("div", { className: "stats-grid" });
  const body = el("div", { className: "dashboard-grid" });
  const dailyCard = card("指定日期的安排", "待辦、工作與目標依指定日期顯示。");
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
        statCard("本月工作時數", hours(data.work_minutes), "工作紀錄時間合計", "blue"),
        statCard("進行中目標", data.active_goals ?? 0, "尚未達成的目標", "violet"),
        statCard("當日完成率", `${data.completion_rate}%`, `${data.date} 的已完成項目`, "amber"),
      );
      dailyList.replaceChildren();
      if (!data.daily.length) {
        dailyList.append(emptyState("這一天還沒有安排"));
      }
      data.daily.forEach((item) => {
        const title = item.kind === "todo" ? item.title : item.kind === "work" ? item.name : item.kind === "goal" ? item.title : item.piece;
        const detail = item.kind === "todo" ? `${item.time || "未排時間"}${item.location ? ` · ${item.location}` : ""}` : item.kind === "work" ? `${item.type} · ${money(item.income)}` : item.kind === "goal" ? (item.status === "completed" ? "已達成" : "進行中") : duration(item.duration_seconds);
        const row = el("div", { className: `list-row ${item.completed || item.status === "completed" ? "is-done" : ""}` });
        row.append(el("span", { className: `kind-dot ${item.kind}`, text: item.kind === "todo" ? "待" : item.kind === "work" ? "工" : item.kind === "goal" ? "目" : "練" }), el("div", { className: "row-main" }, [el("strong", { text: title }), el("small", { text: detail })]));
        if (item.kind === "todo") row.append(button(item.completed ? "已完成" : "完成", "button ghost small", async () => { await api(`/api/v1/todos/${item.id}`, { method: "PATCH", body: { completed: !item.completed } }); load(); }));
        if (item.kind === "goal") row.append(button("查看目標", "button ghost small", () => (location.hash = "#/practice")));
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
  form.append(field("日期", "date", "date", editing?.date || today(), { required: true }), field("工作名稱", "text", "name", editing?.name || "", { required: true, placeholder: "例如：品牌視覺整理" }), field("工作性質", "text", "type", editing?.type || "一般", { required: true, placeholder: "例如：顧問、教學、維護" }), field("收入（TWD）", "number", "income", editing?.income || "0", { min: 0, step: 1 }), field("工作時數", "number", "hours", editing?.hours || "0", { min: 0, step: 0.25 }), field("備註", "textarea", "notes", editing?.notes || "", { rows: 3 }));
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
  form.append(field("日期", "date", "date", editing?.date || state.date, { required: true }), field("時間", "time", "time", editing?.time || ""), field("標題", "text", "title", editing?.title || "", { required: true, placeholder: "例如：整理專案資料" }), field("地點", "text", "location", editing?.location || ""));
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

function goalForm(editing = null) {
  const form = el("form", { className: "form-grid", id: "goal-form" });
  const fields = [
    field("目標名稱", "text", "title", editing?.title || "", { required: true, placeholder: "例如：完成一本書" }),
    field("目標類別", "text", "category", editing?.category || "學習", { required: true, placeholder: "例如：學習、工作、健康" }),
    field("目標日期", "date", "due_date", editing?.due_date || ""),
    field("目標說明", "textarea", "description", editing?.description || "", { rows: 4 }),
  ];
  form.append(...fields);
  const actions = el("div", { className: "form-actions" });
  actions.append(button(editing ? "儲存目標" : "建立目標", "button primary", undefined, "submit"));
  if (editing) actions.append(button("取消編輯", "button secondary", () => { state.goalEditing = null; renderShell(); }));
  form.append(actions);
  return form;
}

function renderGoalCard(item, onChanged) {
  const node = el("article", { className: `goal-card ${item.status === "completed" ? "is-completed" : ""}` });
  const header = el("div", { className: "goal-card-header" });
  const copy = el("div", {});
  copy.append(el("span", { className: "goal-category", text: item.category }), el("h3", { text: item.title }));
  header.append(copy, el("span", { className: "goal-status", text: item.status === "completed" ? "已達成" : "進行中" }));
  node.append(header);
  if (item.description) node.append(el("p", { className: "goal-description", text: item.description }));
  const meta = el("div", { className: "goal-meta" });
  meta.append(el("span", { text: item.due_date ? `期限 ${dateText(item.due_date)}` : "未設定期限" }));
  node.append(meta);
  const progress = el("div", { className: "goal-progress-track", role: "progressbar", "aria-label": `${item.title} 進度`, "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(item.progress_percent) });
  progress.append(el("div", { className: "goal-progress-bar", style: `width:${item.progress_percent}%` }));
  node.append(progress, el("div", { className: "goal-progress-values" }, [el("span", { text: item.status === "completed" ? `完成於 ${dateText(item.completed_at?.slice(0, 10))}` : "尚未達成" })]));
  const updateStatus = async (completed) => {
    try {
      await api(`/api/v1/goals/${item.id}/progress`, { method: "POST", body: { current_value: completed ? item.target_value : "0", record_date: today(), note: completed ? "標記為已達成" : "恢復進行中" } });
      toast(completed ? "目標已達成" : "目標已恢復進行中");
      await onChanged();
    } catch (error) { toast(formatError(error), "error"); }
  };
  const actions = el("div", { className: "actions goal-actions" });
  actions.append(button(item.status === "completed" ? "恢復進行中" : "標記已達成", "button secondary small", () => updateStatus(item.status !== "completed")), button("編輯", "button ghost small", () => { state.goalEditing = item; renderShell(); }), button("刪除", "button danger small", async () => { if (!confirm("確定要刪除這個目標與進度紀錄嗎？")) return; try { await api(`/api/v1/goals/${item.id}`, { method: "DELETE" }); toast("目標已刪除"); await onChanged(); } catch (error) { toast(formatError(error), "error"); } }));
  node.append(actions);
  return node;
}

async function renderGoals(outlet) {
  const frame = pageFrame("Goals", "目標紀錄與回報", "不限鋼琴，建立學習、工作、健康與生活中的各種目標。");
  const layout = el("div", { className: "goal-layout" });
  const editor = card(state.goalEditing ? "編輯目標" : "建立新目標", "設定名稱、類別與日期，完成後可標記為已達成。");
  editor.append(goalForm(state.goalEditing));
  const activeCard = card("進行中目標", "還在持續累積的目標。");
  const activeList = el("div", { className: "goal-list" });
  activeCard.append(activeList);
  const achievedCard = card("已達成", "完成的目標會保留達成日期。");
  achievedCard.classList.add("goal-achieved");
  const achievedList = el("div", { className: "goal-list" });
  achievedCard.append(achievedList);
  layout.append(editor, activeCard, achievedCard);
  frame.append(layout);
  outlet.replaceChildren(frame);

  const form = frame.querySelector("#goal-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = { title: getValue(form, '[name="title"]'), category: getValue(form, '[name="category"]'), due_date: getValue(form, '[name="due_date"]') || null, description: getValue(form, '[name="description"]') };
    try { await api(state.goalEditing ? `/api/v1/goals/${state.goalEditing.id}` : "/api/v1/goals", { method: state.goalEditing ? "PATCH" : "POST", body }); toast(state.goalEditing ? "目標已更新" : "目標已建立"); state.goalEditing = null; renderShell(); } catch (error) { toast(formatError(error), "error"); }
  });

  async function load() {
    try {
      const items = await api("/api/v1/goals");
      activeList.replaceChildren(); achievedList.replaceChildren();
      const activeItems = items.filter((item) => item.status === "active");
      const achievedItems = items.filter((item) => item.status === "completed");
      if (!activeItems.length) activeList.append(emptyState("目前沒有進行中的目標"));
      if (!achievedItems.length) achievedList.append(emptyState("還沒有已達成的目標"));
      activeItems.forEach((item) => activeList.append(renderGoalCard(item, load)));
      achievedItems.forEach((item) => achievedList.append(renderGoalCard(item, load)));
    } catch (error) {
      activeList.replaceChildren(emptyState(formatError(error)));
      achievedList.replaceChildren();
    }
  }
  await load();
}

async function renderPortfolio(outlet) {
  const frame = pageFrame("日常紀錄", "作品集", "作品只存於本機資料目錄；圖片透過 media ID 取用，不暴露磁碟路徑。");
  const layout = el("div", { className: "two-column portfolio-layout" }); const formCard = card(state.portfolioEditing ? "編輯作品資訊" : "新增作品"); const form = el("form", { className: "form-grid", id: "portfolio-form" }); const editing = state.portfolioEditing;
  form.append(field("日期", "date", "date", editing?.date || today(), { required: true }), field("作品名稱", "text", "project", editing?.project || "", { required: true }), field("分類", "text", "category", editing?.category || "未分類"), field("內容摘要", "textarea", "content", editing?.content || "", { rows: 5 }));
  const fileField = field("圖片（可多選）", "file", "files", "", {}); fileField.querySelector("input").multiple = true; fileField.querySelector("input").accept = "image/jpeg,image/png,image/webp"; form.append(fileField); const actions = el("div", { className: "form-actions" }); actions.append(button(editing ? "儲存作品資訊" : "新增作品", "button primary", undefined, "submit")); if (editing) actions.append(button("取消編輯", "button secondary", () => { state.portfolioEditing = null; renderShell(); })); form.append(actions); formCard.append(form);
  const listCard = card("作品牆", "支援搜尋、縮圖與圖片預覽。"); const search = field("搜尋", "search", "search", "", { placeholder: "搜尋名稱、分類或內容" }); listCard.querySelector(".c-card-header").append(search); const grid = el("div", { className: "portfolio-grid" }); listCard.append(grid); layout.append(formCard, listCard); frame.append(layout); outlet.replaceChildren(frame);
  form.addEventListener("submit", async (event) => { event.preventDefault(); const body = { date: getValue(form, '[name="date"]'), project: getValue(form, '[name="project"]'), category: getValue(form, '[name="category"]') || "未分類", content: getValue(form, '[name="content"]') }; try { const saved = await api(editing ? `/api/v1/portfolio/${editing.id}` : "/api/v1/portfolio", { method: editing ? "PATCH" : "POST", body }); const files = form.querySelector('[name="files"]').files; if (!editing && files.length) { const data = new FormData(); [...files].forEach((file) => data.append("files", file)); await api(`/api/v1/portfolio/${saved.id}/media`, { method: "POST", body: data }); } toast("作品已儲存"); state.portfolioEditing = null; renderShell(); } catch (error) { toast(formatError(error), "error"); } });
  async function load() { try { const items = await api(`/api/v1/portfolio?search=${encodeURIComponent(getValue(frame, '[name="search"]'))}`); renderPortfolioGrid(grid, items); } catch (error) { grid.replaceChildren(emptyState(formatError(error))); } }
  search.querySelector("input").addEventListener("input", () => { window.clearTimeout(search._timer); search._timer = window.setTimeout(load, 250); }); await load();
}

function renderPortfolioGrid(grid, items) {
  grid.replaceChildren(); if (!items.length) { grid.append(emptyState("還沒有作品")); return; }
  items.forEach((item) => { const cardNode = el("article", { className: "portfolio-card" }); const visual = el("div", { className: "portfolio-visual" }); if (item.media?.length) { const image = el("img", { src: item.media[0].url, alt: item.project }); image.addEventListener("click", () => openImageViewer(item.media, 0)); visual.append(image); if (item.media.length > 1) visual.append(el("span", { className: "media-count", text: `+${item.media.length - 1}` })); } else visual.append(el("span", { className: "visual-placeholder", text: "作品" })); const body = el("div", { className: "portfolio-body" }); body.append(el("div", { className: "c-eyebrow", text: item.category }), el("h3", { text: item.project }), el("p", { text: item.content || "尚未填寫內容" }), el("small", { className: "muted", text: dateText(item.date) })); const actions = el("div", { className: "actions" }); actions.append(button("編輯", "ghost small", () => { state.portfolioEditing = item; renderShell(); }), button("刪除", "danger small", async () => { if (!confirm("確定要刪除這件作品與其圖片嗎？")) return; await api(`/api/v1/portfolio/${item.id}`, { method: "DELETE" }); toast("作品已刪除"); renderShell(); })); body.append(actions); cardNode.append(visual, body); grid.append(cardNode); });
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

window.addEventListener("hashchange", () => { state.route = location.hash.replace(/^#\/?/, "") || "dashboard"; renderShell(); });
renderShell();

