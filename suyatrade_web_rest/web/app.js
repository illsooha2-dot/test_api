// ===== tiny helpers =====
const $ = (id) => document.getElementById(id);
const fmtMoney = (n) => (Number(n || 0)).toLocaleString() + " 원";
const fmtPercent = (n) => (Number(n || 0)).toFixed(2) + " %";

async function jsonFetch(url, opts = {}) {
  const r = await fetch(url, {
    headers: { "Accept": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const ct = r.headers.get("content-type") || "";
  const isJson = ct.includes("application/json");
  const body = isJson ? await r.json() : await r.text();
  if (!r.ok) {
    throw { status: r.status, body };
  }
  return body;
}

// ===== toast (화면 우상단 작은 알림) =====
function toast(msg, ok = true) {
  let host = $("__toast_host");
  if (!host) {
    host = document.createElement("div");
    host.id = "__toast_host";
    host.style.position = "fixed";
    host.style.top = "12px";
    host.style.right = "12px";
    host.style.zIndex = "9999";
    document.body.appendChild(host);
  }
  const el = document.createElement("div");
  el.textContent = msg;
  el.style.marginTop = "6px";
  el.style.padding = "10px 12px";
  el.style.borderRadius = "10px";
  el.style.fontSize = "13px";
  el.style.color = ok ? "#041022" : "#fff";
  el.style.background = ok ? "#6ea2ff" : "#c84a4a";
  el.style.boxShadow = "0 8px 24px rgba(0,0,0,.35)";
  host.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}

// ===== 서버 핑/토큰 =====
async function ping() {
  try {
    const j = await jsonFetch("/api/health");
    $("health").textContent = "OK: " + (j?.status || "healthy");
    toast("서버 연결 성공", true);
  } catch (e) {
    $("health").textContent = "ERROR";
    toast("서버 연결 실패", false);
  }
}

async function issueToken() {
  try {
    const j = await jsonFetch("/api/token/debug");
    $("health").textContent = "OK: " + (j?.ok ? "token_ok" : "token_fail");
    toast(j?.ok ? "토큰 OK" : "토큰 실패", !!j?.ok);
  } catch (e) {
    toast("토큰 요청 오류", false);
  }
}

// ===== 계좌 요약 =====
let _busyBalance = false;

async function refreshAccountSummary() {
  if (_busyBalance) return;
  _busyBalance = true;
  const btn = $("btnBalance");
  const labelOrig = btn ? btn.textContent : "";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "조회 중…";
  }
  try {
    const j = await jsonFetch("/api/account/summary");
    $("labDeposit").textContent  = fmtMoney(j.deposit);
    $("labAvail").textContent    = fmtMoney(j.orderable);
    $("labToday").textContent    = fmtMoney(j.today_realized);
    $("labPurchase").textContent = fmtMoney(j.total_purchase);
    $("labEval").textContent     = fmtMoney(j.total_eval);
    $("labPL").textContent       = fmtMoney(j.total_pl);
    $("labReturn").textContent   = fmtPercent(j.total_return);

    if (j.ok === false) {
      toast("일부 항목 수집 실패(로그 확인)", false);
      console.warn("account summary partial errors:", j.errors);
    } else {
      toast("계좌 잔고 갱신 완료", true);
    }
  } catch (e) {
    console.error("refreshAccountSummary error:", e);
    toast("계좌 잔고 조회 실패", false);
  } finally {
    _busyBalance = false;
    if (btn) {
      btn.disabled = false;
      btn.textContent = labelOrig || "계좌 잔고 확인";
    }
  }
}

// ===== 탭 전환 =====
function bindTabs() {
  const tabs = document.querySelectorAll(".tabs .tab");
  const bodies = document.querySelectorAll(".tabbody");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      bodies.forEach(b => b.classList.add("hidden"));
      const body = $("tab-" + target);
      if (body) body.classList.remove("hidden");
    });
  });
}

// ===== 일반/텔레그램 설정 load & save =====
async function loadGeneral() {
  try {
    const j = await jsonFetch("/api/settings/general");
    $("autoEnabled").checked = !!j.autotrade_enabled;
    $("orderAmount").value   = j.order_amount ?? 100000;
    $("maxItems").value      = j.max_items ?? 10;

    $("sellEnabled").checked = !!j.sell_strategy_enabled;
    const sell = (j.sell_strategy || "fixed_stop");
    const radio = document.querySelector(`input[name="sell"][value="${sell}"]`);
    if (radio) radio.checked = true;

    $("targetProfit").value  = j.target_profit ?? 5.0;
    $("stopLoss").value      = j.stop_loss ?? -3.0;
    $("trailStart").value    = j.trailing_start ?? 3.0;
    $("trailFall").value     = j.trailing_fall ?? -1.0;
    $("trailBase").value     = j.trailing_base_stoploss ?? -3.0;
    $("maUnit").value        = j.ma_time_unit || "일봉";
    $("maInterval").value    = j.ma_time_interval ?? 5;
    $("maShort").value       = j.ma_short ?? 5;
    $("maLong").value        = j.ma_long ?? 20;
  } catch (e) {
    console.warn("loadGeneral failed:", e);
  }
}

async function saveGeneral() {
  try {
    const body = {
      autotrade_enabled: $("autoEnabled").checked,
      order_amount: Number($("orderAmount").value || 0),
      max_items: Number($("maxItems").value || 0),
      sell_strategy_enabled: $("sellEnabled").checked,
      sell_strategy: (document.querySelector('input[name="sell"]:checked')?.value || "fixed_stop"),
      target_profit: Number($("targetProfit").value || 0),
      stop_loss: Number($("stopLoss").value || 0),
      trailing_start: Number($("trailStart").value || 0),
      trailing_fall: Number($("trailFall").value || 0),
      trailing_base_stoploss: Number($("trailBase").value || 0),
      ma_time_unit: $("maUnit").value,
      ma_time_interval: Number($("maInterval").value || 0),
      ma_short: Number($("maShort").value || 0),
      ma_long: Number($("maLong").value || 0),
    };
    await jsonFetch("/api/settings/general", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    toast("전략 저장 완료", true);
  } catch (e) {
    toast("전략 저장 실패", false);
  }
}

async function loadTelegram() {
  try {
    const j = await jsonFetch("/api/settings/telegram");
    $("tgEnabled").checked = !!j.enabled;
    $("tgToken").value = j.token || "";
    $("tgChat").value = j.chat_id || "";
  } catch {
    // 없으면(404) 무시
  }
}

async function saveTelegram() {
  try {
    const body = {
      enabled: $("tgEnabled").checked,
      token: $("tgToken").value || "",
      chat_id: $("tgChat").value || "",
    };
    await jsonFetch("/api/settings/telegram", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    toast("텔레그램 저장 완료", true);
  } catch (e) {
    toast("텔레그램 저장 실패", false);
  }
}

// ===== 수동 주문 =====
async function manualOrder(side) {
  const code = $(side === "buy" ? "manBuyCode" : "manSellCode").value.trim();
  const qty  = Number($(side === "buy" ? "manBuyQty" : "manSellQty").value || 0);
  const mkt  = $(side === "buy" ? "manBuyMarket" : "manSellMarket").value === "true";
  const price= Number($(side === "buy" ? "manBuyPrice" : "manSellPrice").value || 0);
  if (!code || qty <= 0) {
    toast("코드/수량을 확인하세요", false);
    return;
  }
  try {
    const url = side === "buy" ? "/api/orders/stock/buy" : "/api/orders/stock/sell";
    const body = { code, qty, market: mkt, price };
    const j = await jsonFetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    toast(`${side === "buy" ? "매수" : "매도"} 요청 완료`, true);
    console.log("manualOrder resp:", j);
  } catch (e) {
    toast(`${side === "buy" ? "매수" : "매도"} 요청 실패`, false);
  }
}

// ===== init =====
window.addEventListener("DOMContentLoaded", () => {
  // 상단 버튼
  $("btnHealth")?.addEventListener("click", ping);
  $("btnToken")?.addEventListener("click", issueToken);

  // 탭/폼
  bindTabs();
  $("btnSaveGeneral")?.addEventListener("click", saveGeneral);
  $("btnSaveTg")?.addEventListener("click", saveTelegram);

  // 계좌 잔고
  $("btnBalance")?.addEventListener("click", refreshAccountSummary);

  // 수동 주문
  $("manBuyBtn")?.addEventListener("click", () => manualOrder("buy"));
  $("manSellBtn")?.addEventListener("click", () => manualOrder("sell"));

  // 최초 상태 로드
  ping();
  loadGeneral();
  loadTelegram();
});

// (선택) 디버그를 위해 전역에 노출
window.__forceAccountRefresh = refreshAccountSummary;
