export function money(value) {
  const amount = Number(value || 0);
  return `NT$ ${new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 0 }).format(amount)}`;
}

export function hours(minutes) {
  return `${(Number(minutes || 0) / 60).toFixed(1)} 小時`;
}

export function duration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds || 0)));
  const h = String(Math.floor(total / 3600)).padStart(2, "0");
  const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

export function today() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export function monthOf(dateString = today()) {
  return dateString.slice(0, 7);
}

export function dateText(value) {
  if (!value) return "未設定";
  return new Intl.DateTimeFormat("zh-TW", { year: "numeric", month: "short", day: "numeric" }).format(
    new Date(`${value}T00:00:00`),
  );
}

