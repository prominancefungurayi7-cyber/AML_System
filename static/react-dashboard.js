(function () {
  const adminRoot = document.getElementById("admin-react-root");
  const complianceRoot = document.getElementById("compliance-react-root");
  const customerRoot = document.getElementById("customer-react-root");

  if (!adminRoot && !complianceRoot && !customerRoot) return;

  if (!window.React || !window.ReactDOM) {
    const root = adminRoot || complianceRoot || customerRoot;
    root.innerHTML = '<section class="card"><h3>Dashboard unavailable</h3><p class="muted-line">React could not be loaded. Check your network connection and reload this page.</p></section>';
    return;
  }

  const { createElement: h, useEffect, useMemo, useState, useRef } = window.React;
  const suspiciousLevels = ["suspicious", "super_suspicious", "high_risk", "critical"];

  function Icon({ name }) {
    const icons = {
      home: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("polyline", { points: "9 22 9 12 15 12 15 22", fill: "none", stroke: "currentColor", strokeWidth: 2 })
      ),
      users: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("circle", { cx: "9", cy: "7", r: "4", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("path", { d: "M23 21v-2a4 4 0 0 0-3-3.87", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("path", { d: "M16 3.13a4 4 0 0 1 0 7.75", fill: "none", stroke: "currentColor", strokeWidth: 2 })
      ),
      list: h("svg", { viewBox: "0 0 24 24" },
        h("line", { x1: "8", y1: "6", x2: "21", y2: "6", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "8", y1: "12", x2: "21", y2: "12", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "8", y1: "18", x2: "21", y2: "18", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "3", y1: "6", x2: "3.01", y2: "6", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "3", y1: "12", x2: "3.01", y2: "12", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "3", y1: "18", x2: "3.01", y2: "18", stroke: "currentColor", strokeWidth: 2 })
      ),
      shield: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z", fill: "none", stroke: "currentColor", strokeWidth: 2 })
      ),
      activity: h("svg", { viewBox: "0 0 24 24" },
        h("polyline", { points: "22 12 18 12 15 21 9 3 6 12 2 12", fill: "none", stroke: "currentColor", strokeWidth: 2 })
      ),
      settings: h("svg", { viewBox: "0 0 24 24" },
        h("circle", { cx: "12", cy: "12", r: "3", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("path", { d: "M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z", fill: "none", stroke: "currentColor", strokeWidth: 2 })
      ),
      file: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("polyline", { points: "14 2 14 8 20 8", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "16", y1: "13", x2: "8", y2: "13", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "16", y1: "17", x2: "8", y2: "17", stroke: "currentColor", strokeWidth: 2 }),
        h("polyline", { points: "10 9 9 9 8 9", stroke: "currentColor", strokeWidth: 2 })
      ),
      logout: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("polyline", { points: "16 17 21 12 16 7", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "21", y1: "12", x2: "9", y2: "12", stroke: "currentColor", strokeWidth: 2 })
      ),
      alert: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "12", y1: "9", x2: "12", y2: "13", stroke: "currentColor", strokeWidth: 2 }),
        h("line", { x1: "12", y1: "17", x2: "12.01", y2: "17", stroke: "currentColor", strokeWidth: 2 })
      ),
      message: h("svg", { viewBox: "0 0 24 24" },
        h("path", { d: "M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z", fill: "none", stroke: "currentColor", strokeWidth: 2 }),
        h("path", { d: "M8 9h8M8 13h5", fill: "none", stroke: "currentColor", strokeWidth: 2 })
      )
    };
    return icons[name] || null;
  }

  function readJson(id) {
    const node = document.getElementById(id);
    if (!node) return {};
    try {
      return JSON.parse(node.textContent || "{}");
    } catch (_error) {
      return {};
    }
  }

  function money(value) {
    return Number(value || 0).toLocaleString("en-US", { style: "currency", currency: "USD" });
  }

  function score(value) {
    return Number(value || 0).toFixed(0);
  }

  function scoringWeights(model) {
    const policy = model?.risk_scoring;
    if (!policy || !Number.isFinite(policy.ai_weight) || !Number.isFinite(policy.rule_weight)) return null;
    return `V4 ${Math.round(policy.ai_weight * 100)}% \u00b7 Rules ${Math.round(policy.rule_weight * 100)}%`;
  }

  function operationalScoreHelp(model) {
    const weights = scoringWeights(model);
    return weights
      ? `Current policy for new decisions: ${weights}. V4 contributes its suspicious probability on a 0\u2013100 scale. Independent rule or AI flags may still require review. Earlier recorded scores are retained.`
      : 'Recorded operational score. AI and rule findings are shown separately.';
  }

  function confidence(value) {
    if (value === null || value === undefined || value === "") return "unavailable";
    return `${Math.round(Number(value || 0) * 100)}%`;
  }

  function normalizeLevel(level) {
    return String(level || "normal").toLowerCase().replace(/[^a-z0-9]+/g, "-");
  }

  function labelize(value) {
    return String(value || "normal").replace(/_/g, " ");
  }

  function customerRiskLabel(value) {
    const level = normalizeLevel(value);
    if (["critical", "high-risk", "super-suspicious"].includes(level)) return "Super suspicious";
    if (level === "suspicious") return "Suspicious";
    if (level === "normal" || level === "low") return "Normal";
    return labelize(value || "Pending review");
  }

  function labelizeTransactionType(value) {
    const type = String(value || "").toLowerCase();
    const mobileMoneyLabels = {
      "deposit": "Cash-In",
      "withdraw": "Cash-Out",
      "transfer": "Wallet-to-Wallet Transfer"
    };
    return mobileMoneyLabels[type] || labelize(value);
  }

  function shortTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function riskClass(level) {
    return `status-pill risk-pill risk-${normalizeLevel(level)}`;
  }

  function trim(list, count) {
    return list.slice(0, count);
  }

  function StatGrid({ items }) {
    return h("section", { className: "react-metrics" },
      items.map((item, index) => h("div", { className: "metric-tile", key: item.label },
        h("span", { className: "metric-index", "aria-hidden": "true" }, String(index + 1).padStart(2, "0")),
        h("span", { className: "metric-label" }, item.label),
        h("strong", null, typeof item.value === "number" ? item.value.toLocaleString() : item.value),
        item.caption ? h("small", null, item.caption) : null
      ))
    );
  }

  function EmptyState({ children }) {
    return h("div", { className: "empty-state" },
      h("span", { className: "empty-state-icon", "aria-hidden": "true" }, "i"),
      h("p", null, children)
    );
  }

  function PanelHeading({ title, meta }) {
    return h("div", { className: "panel-heading-row" },
      h("h3", null, title),
      meta || null
    );
  }

  function LiveStatus({ children, tone = "live" }) {
    return h("span", { className: `live-status ${tone}` },
      h("span", { className: "live-dot", "aria-hidden": "true" }),
      children
    );
  }

  function useRealtime(handlers) {
    const latest = useRef(handlers);
    latest.current = handlers;
    const events = Object.keys(handlers).sort().join(',');
    useEffect(() => {
      const socket = window.getAmlSocket();
      if (!socket) return;
      const bound = {};
      events.split(',').forEach((name) => {
        bound[name] = (...args) => latest.current[name]?.(...args);
        socket.on(name, bound[name]);
      });
      if (socket.connected && latest.current.connect) latest.current.connect();
      return () => Object.entries(bound).forEach(([name, fn]) => socket.off(name, fn));
    }, [events]);
  }

  function upsert(items, item, limit) {
    const previous = items.find((row) => String(row.id) === String(item.id));
    return [{ ...previous, ...item }, ...items.filter((row) => String(row.id) !== String(item.id))].slice(0, limit);
  }

  function upsertRecentTransaction(items, item, limit) {
    const previous = items.find((row) => String(row.id) === String(item.id));
    const rows = [{ ...previous, ...item }, ...items.filter((row) => String(row.id) !== String(item.id))];
    rows.sort((left, right) => {
      const leftTime = Date.parse(left.timestamp);
      const rightTime = Date.parse(right.timestamp);
      if (Number.isFinite(leftTime) && Number.isFinite(rightTime) && leftTime !== rightTime) return rightTime - leftTime;
      // Compare decimal IDs without losing precision for large MySQL integers.
      const leftId = String(left.id), rightId = String(right.id);
      if (/^\d+$/.test(leftId) && /^\d+$/.test(rightId)) {
        return rightId.length - leftId.length || (leftId < rightId ? 1 : leftId > rightId ? -1 : 0);
      }
      return 0;
    });
    return rows.slice(0, limit);
  }

  function ownsTransaction(txn, accountNumber) {
    return txn.sender_account === accountNumber || txn.receiver_account === accountNumber;
  }

  function DashboardSidebar({ sidebarItems, activeSection, setActiveSection, role }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [theme, setTheme] = useState(document.documentElement.dataset.theme || "dark");
    const toggleTheme = () => {
      const currentTheme = document.documentElement.dataset.theme || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = newTheme;
      try { localStorage.setItem("epocash-theme", newTheme); } catch (_) { /* Cookie persists the choice. */ }
      document.cookie = `epocash-theme=${encodeURIComponent(newTheme)}; Max-Age=31536000; Path=/; SameSite=Lax`;
      setTheme(newTheme);
    };

    useEffect(() => window.__amlSidebarController.register(setSidebarOpen), []);

    return h(window.React.Fragment, null,
      sidebarOpen && h("div", {
        className: "sidebar-overlay active",
        onClick: () => window.__amlSidebarController.close()
      }),
      h("aside", { id: "page-sidebar", className: `admin-sidebar ${sidebarOpen ? "open" : ""}` },
        h("div", { className: "sidebar-brand" },
          h("span", { className: "sidebar-brand__title" }, "YOUR WORKSPACE"),
          h("span", { className: "sidebar-brand__role" }, role)
        ),
        h("nav", null,
          sidebarItems.map((item) => item.href ?
            h("a", {
              key: item.id,
              href: item.href,
              className: "sidebar-item"
            }, h(Icon, { name: item.icon }), item.label) :
            h("button", {
              key: item.id,
              "aria-current": activeSection === item.id ? "page" : undefined,
              className: activeSection === item.id ? "sidebar-item active" : "sidebar-item",
              onClick: () => {
                setActiveSection(item.id);
                window.__amlSidebarController.close();
              },
              type: "button"
            }, h(Icon, { name: item.icon }), item.label))
        ),
        h("div", { className: "sidebar-footer" },
          h("button", {
            className: "theme-toggle-sidebar",
            onClick: toggleTheme,
            type: "button",
            "aria-label": "Toggle theme"
          },
            h("span", { className: "theme-toggle__track" },
              h("span", { className: "theme-toggle__thumb" })
            ),
            h("span", { className: "theme-toggle__text" }, theme === "dark" ? "Dark" : "Light")
          )
        )
      )
    );
  }

  function CustomerDashboard({ initialData }) {
    const user = initialData.user || {};
    const accountNumber = user.account_number || "";
    const [balance, setBalance] = useState(Number(user.balance || 0));
    const [transactions, setTransactions] = useState(initialData.transactions || []);
    const [alerts, setAlerts] = useState(initialData.alerts || []);
    const [stats, setStats] = useState(initialData.stats || {});
    const [feed, setFeed] = useState([]);
    const [status, setStatus] = useState("Connecting to live updates");
    const [activeSection, setActiveSection] = useState(
      () => new URLSearchParams(window.location.search).has("page") ? "transactions" : "overview");
    // Native form resubmissions preserve this value; a new dashboard draft gets a new one.
    const [transactionRequestId] = useState(() =>
      window.crypto && window.crypto.randomUUID ? window.crypto.randomUUID() : "");
    const [paymentSubmitting, setPaymentSubmitting] = useState(false);
    const [paymentType, setPaymentType] = useState('wallet_to_wallet');
    const cashService = paymentType !== 'wallet_to_wallet';
    const [assistedTransfer, setAssistedTransfer] = useState(false);
    const [transferRecipient, setTransferRecipient] = useState('');
    const [servicedEndpoint, setServicedEndpoint] = useState('sender');
    useEffect(() => {
      let timer, running = false, queued = false, stopped = false;
      const controller = new AbortController();
      const refresh = async () => {
        if (running) { queued = true; return; }
        running = true;
        try {
          const response = await fetch(window.location.href, {
            credentials: 'same-origin', cache: 'no-store', signal: controller.signal
          });
          if (!response.ok) throw new Error('Dashboard refresh unavailable');
          const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
          const node = doc.getElementById('customer-dashboard-data');
          if (!node) throw new Error('Dashboard session unavailable');
          const data = JSON.parse(node.textContent);
          if (stopped) return;
          // Update data in place: preserve the selected section, payment draft,
          // request ID and mounted page instead of reloading on each AI result.
          setTransactions(data.transactions || []);
          setAlerts(data.alerts || []);
          setStats(data.stats || {});
          setBalance(Number(data.user?.balance || 0));
        } catch (error) {
          if (!stopped) setStatus('Live refresh unavailable. Reconnecting...');
        } finally {
          running = false;
          if (queued && !stopped) { queued = false; schedule(); }
        }
      };
      const schedule = () => { clearTimeout(timer); timer = setTimeout(refresh, 400); };
      window.addEventListener('aml:customer-resync', schedule);
      return () => {
        stopped = true; clearTimeout(timer); controller.abort();
        window.removeEventListener('aml:customer-resync', schedule);
      };
    }, []);
    useEffect(() => {
      const restored = () => setPaymentSubmitting(false);
      window.addEventListener("pageshow", restored);
      return () => window.removeEventListener("pageshow", restored);
    }, []);

    const sidebarItems = [
      { id: "overview", label: "Overview", icon: "home" },
      { id: "transactions", label: "Transactions", icon: "list" },
      { id: "alerts", label: "Alerts", icon: "alert" },
      { id: "activity", label: "Activity Feed", icon: "activity" },
      { id: "messages", label: "Messages", href: "/messages", icon: "message" },
      { id: "signout", label: "Sign Out", href: "/logout", icon: "logout" }
    ];


    const addFeed = (text) => setFeed((current) => trim([{ text, timestamp: new Date().toLocaleTimeString() }, ...current], 25));

    useRealtime({
      connect: () => setStatus("Live updates connected"),
      disconnect: () => setStatus("Disconnected. Reconnecting..."),
      connect_error: () => setStatus("Live updates unavailable. Reload to refresh."),
      transaction: (txn) => {
        if (!ownsTransaction(txn, accountNumber)) return;
        setTransactions((current) => upsert(current, txn, 25));
        setStats((current) => ({
          ...current,
          total_tx: Number(current.total_tx || 0) + 1,
          flagged: txn.risk_level && txn.risk_level !== "normal"
            ? Number(current.flagged || 0) + 1
            : Number(current.flagged || 0),
        }));
        addFeed(`Transaction | ${txn.transaction_type || txn.type || ""} | ${money(txn.amount)} | ${txn.risk_level || "normal"}`);
      },
      alert: (alert) => {
        if (alert.account_number !== accountNumber) return;
        setAlerts((current) => upsert(current, alert, 10));
        setStats((current) => ({ ...current, open_alerts: Number(current.open_alerts || 0) + 1 }));
        setStatus("Live alert received | stream active");
        addFeed(`Alert | Tx #${alert.transaction_id || ""} | ${alert.risk_level || ""} | Score ${score(alert.risk_score)} | AI: ${(alert.ai_risk_level === "normal" ? "Normal" : displayAiReason(alert.ai_reason) || "Not recorded")} | Rules: ${alert.rule_reason || "Not recorded"}`);
      },
      alert_update: (alert) => {
        if (alert.account_number !== accountNumber) return;
        setAlerts((current) => {
          if (alert.status !== "open") return current.filter((item) => String(item.id) !== String(alert.id));
          const exists = current.some((item) => String(item.id) === String(alert.id));
          return exists
            ? current.map((item) => String(item.id) === String(alert.id) ? { ...item, ...alert } : item)
            : upsert(current, alert, 10);
        });
        if (alert.status !== "open") {
          setStats((current) => ({ ...current, open_alerts: Math.max(0, Number(current.open_alerts || 0) - 1) }));
        }
        addFeed(`Alert status | #${alert.id || ""} | ${alert.status || ""}`);
      },
      ai_model: (model) => addFeed(`AI model | ${model.trained ? "trained" : "waiting for more labels"} | ${model.training_rows} rows`),
      balance: (event) => {
        if (event.account_number !== accountNumber) return;
        setBalance(Number(event.balance || 0));
      },
      reset: () => {
        setTransactions([]);
        setAlerts([]);
        setFeed([]);
        setStatus("Live reset received | stream active");
        setStats((current) => ({ ...current, total_tx: 0, flagged: 0, open_alerts: 0 }));
      },
    });

    const metricItems = [
      { label: "Wallet balance", value: money(balance), caption: accountNumber },
      { label: "Transactions", value: stats.total_tx ?? transactions.length, caption: "wallet history" },
      { label: "Open alerts", value: stats.open_alerts ?? alerts.filter((alert) => alert.status === "open").length, caption: "live cases" },
    ];

    const renderSection = () => {
      switch (activeSection) {
        case "overview":
          return h(window.React.Fragment, null,
            h(StatGrid, { items: metricItems }),
            h("section", { className: "grid" },
              h("div", { className: "card account-card" },
                h("p", { className: "status-pill" }, "EpoCash Wallet"),
                h("h3", null, accountNumber),
                h("p", { className: "metric" }, money(balance)),
                h("p", { className: "muted-line" }, "Wallet balance updates automatically after every mobile-money transaction.")
              ),
              h("div", { className: "card action-card" },
                h(PanelHeading, { title: "Send or Receive Money" }),
                h("form", { method: "post", action: "/customer/transaction", onSubmit: (event) => {
                  if (paymentSubmitting) { event.preventDefault(); return; }
                  setPaymentSubmitting(true);
                } },
                  h("input", { type: "hidden", name: "client_request_id", value: transactionRequestId }),
                  h("input", { type: "hidden", name: "canonical_version", value: "mobile_money.canonical.v1" }),
                  h("input", { type: "hidden", name: "currency", value: "USD" }),
                  h("label", null, "Type"),
                  h("select", { name: "type", value: paymentType, onChange: e => setPaymentType(e.target.value) },
                    h("option", { value: "cash_in" }, "Cash In"),
                    h("option", { value: "cash_out" }, "Cash Out"),
                    h("option", { value: "wallet_to_wallet" }, "Send Money")
                  ),
                  h("label", null, "Amount"),
                  h("input", { type: "number", min: "0.01", max: "15000.00", step: "0.01", name: "amount", required: true,
                    "aria-describedby": "payment-amount-limit" }),
                  h("p", { id: "payment-amount-limit", className: "form-hint" }, "Current per-transaction limit: $15,000.00."),
                  h("input", { type: "hidden", name: "channel", value: cashService || assistedTransfer ? 'agent' : 'direct_wallet' }),
                  h("input", { type: "hidden", name: "serviced_wallet", value: cashService ? accountNumber :
                    assistedTransfer ? (servicedEndpoint === 'sender' ? accountNumber : transferRecipient) : '' }),
                  h("input", { type: "hidden", name: "agent_flow_direction", value: cashService ? paymentType : 'none' }),
                  cashService ? h(React.Fragment, null,
                    h("input", { type: "hidden", name: "recipient", value: '' }),
                    h("label", null, "Service agent"),
                    h("select", { name: "agent_id", required: true, defaultValue: '' },
                      h("option", { value: '', disabled: true }, "Select an agent"),
                      (initialData.agents || []).map(agent => h("option", { key: agent.id, value: agent.id },
                        `${agent.username} (${agent.agent_code})`))),
                    h("p", { className: "form-hint" }, paymentType === 'cash_in'
                      ? 'Give cash to the agent. The agent transfers electronic value from their float to your wallet.'
                      : 'Give electronic value to the agent. The agent gives you the same amount in cash.'),
                    h("label", { className: "checkbox-label" },
                      h("input", { type: "checkbox", name: "cash_confirmed", value: 'yes', required: true }),
                      " I confirm the physical cash exchange with the agent.")
                  ) : h(React.Fragment, null,
                    !assistedTransfer && h("input", { type: "hidden", name: "agent_id", value: '' }),
                    h("label", null, "Recipient wallet number"),
                    h("input", { name: "recipient", placeholder: "ACC1004 or AGENT0001", required: true,
                      value: transferRecipient, onChange: e => setTransferRecipient(e.target.value) }),
                    h("p", { className: "form-hint" }, "Transfer to a customer wallet or fund an active agent's electronic float."),
                    h("details", { className: "agent-details" },
                      h("summary", null, "Optional agent assistance"),
                      h("label", { className: "checkbox-label" },
                        h("input", { type: "checkbox", checked: assistedTransfer,
                          onChange: e => setAssistedTransfer(e.target.checked) }), " Agent-assisted transfer"),
                      assistedTransfer && h(React.Fragment, null,
                        h("label", null, "Service agent"),
                        h("select", { name: "agent_id", required: true, defaultValue: '' },
                          h("option", { value: '', disabled: true }, "Select an agent"),
                          (initialData.agents || []).map(agent => h("option", { key: agent.id, value: agent.id },
                            `${agent.username} (${agent.agent_code})`))),
                        h("label", null, "Wallet assisted by the agent"),
                        h("select", { value: servicedEndpoint, onChange: e => setServicedEndpoint(e.target.value),
                          'aria-label': 'Wallet assisted by the agent' },
                          h("option", { value: 'sender' }, "My wallet"),
                          h("option", { value: 'recipient' }, "Recipient wallet")))
                    )
                  ),
                  !transactionRequestId && h("p", { className: "form-hint" },
                    "Secure request IDs are unavailable in this browser. Please use a supported browser."),
                  h("button", { type: "submit", disabled: !transactionRequestId || paymentSubmitting },
                    paymentSubmitting ? "Saving payment..." : "Confirm transaction"),
                  h("p", { className: "form-hint", role: "status" },
                    "Your payment confirmation appears after it is saved. AI review updates separately.")
                )
              ),
            ),
            h(CustomerTransactionsPanel, { transactions, model: initialData.model, page: Number(initialData.page || 1),
              pageCount: Number(initialData.transaction_pages || 1) })
          );
        case "transactions":
          return h(CustomerTransactionsPanel, { transactions, model: initialData.model, page: Number(initialData.page || 1), pageCount: Number(initialData.transaction_pages || 1) });
        case "alerts":
          return h(CustomerAlertsPanel, { alerts });
        case "activity":
          return h("section", { className: "card table-card live-feed-card" },
            h(PanelHeading, { title: "Live AML Feed", meta: h(LiveStatus, null, status) }),
            feed.length ? h("ul", null, feed.map((event, index) => (
              h("li", { key: `${event.timestamp}-${index}` }, `${event.timestamp} - ${event.text}`)
            ))) : h(EmptyState, null, "Waiting for live events.")
          );
        default:
          return null;
      }
    };

    return h("div", { className: "admin-layout" },
      h(DashboardSidebar, { sidebarItems, activeSection, setActiveSection, role: "Wallet Customer" }),
      h("div", { className: "admin-content section-transition", key: activeSection }, renderSection())
    );
  }

  function CustomerTransactionsPanel({ transactions, model, page = 1, pageCount = 1 }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Recent Transactions" }),
      transactions.length ? h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null, ["Transaction", "From / to", "Type", "Amount", "Risk", "AI finding", "Rule finding"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          transactions.map((txn, index) => h("tr", { key: txn.id || index },
            h("td", null,
              h("strong", null, `#${txn.id || ""}`),
              h("span", { className: "muted-line block-line" }, shortTime(txn.timestamp))
            ),
            h("td", null, `${txn.sender_account || ""} → ${txn.receiver_account || ""}`),
            h("td", null, labelizeTransactionType(txn.transaction_type || txn.type)),
            h("td", null, money(txn.amount)),
            h("td", null,
              h("span", { className: riskClass(txn.risk_level) }, customerRiskLabel(txn.risk_level)),
              h(TransactionScores, { transaction: txn }),
            ),
            h("td", null,
              h("strong", { className: "block-line" }, labelize(txn.ai_risk_level || "unavailable")),
              txn.ai_risk_level !== "normal" && h("span", { className: "muted-line block-line" }, displayAiReason(txn.ai_reason) || "No AI reason recorded"),
              txn.ai_risk_level === "suspicious_pattern" && hasV4Decision(txn) && h(V4Evidence, { transactionId: txn.id }),
              h(TransactionScores, { transaction: txn, part: "ai" })
            ),
            h("td", null,
              h("strong", { className: "block-line" }, labelize(txn.rule_level || "normal")),
              h("span", { className: "muted-line block-line" }, txn.rule_reason || "No rule indicators"),
              h(TransactionScores, { transaction: txn, part: "rule" })
            )
          ))
        )
      ) : h(EmptyState, null, "No transactions to show."),
      h("nav", { className: "table-pagination", "aria-label": "Customer transaction pages" },
        h("a", { className: page <= 1 ? "action-link pagination-disabled" : "action-link",
          href: page <= 1 ? undefined : `/customer?page=${page - 1}`,
          "aria-disabled": page <= 1 }, "Previous"),
        h("span", null, `Page ${page} of ${pageCount}`),
        h("a", { className: page >= pageCount ? "action-link pagination-disabled" : "action-link",
          href: page >= pageCount ? undefined : `/customer?page=${page + 1}`,
          "aria-disabled": page >= pageCount }, "Next")
      )
    );
  }

  function displayAiReason(reason) {
    return String(reason || '').replace(/;\s*threshold:\s*0\.50\b/gi, '');
  }

  function hasV4Decision(row) {
    return ['normal', 'suspicious_pattern'].includes(row.ai_risk_level) && /^V4 /.test(row.ai_reason || '');
  }

  function TransactionScores({ transaction, part = "overall" }) {
    const confidence = transaction.ai_confidence;
    const complete = hasV4Decision(transaction) && confidence != null &&
      Number.isFinite(Number(confidence)) && Number(confidence) >= 0 && Number(confidence) <= 1;
    // Stored confidence is confidence in the predicted class, not always risk.
    const aiRisk = complete ? 100 * (transaction.ai_risk_level === 'normal'
      ? 1 - Number(confidence) : Number(confidence)) : null;
    const formatScore = (value) => value != null && Number.isFinite(Number(value))
      ? `${Number(value).toFixed(2)} / 100` : 'Unavailable';
    const waiting = transaction.ai_risk_level === 'pending_v4';
    const text = part === 'rule' ? `Rule score: ${formatScore(transaction.rule_score)}`
      : part === 'ai' ? `AI score: ${complete ? formatScore(aiRisk) : waiting ? 'Pending' : 'Unavailable'}`
      : `Overall score: ${complete ? formatScore(transaction.risk_score) : 'Awaiting AI'}`;
    return h('strong', { className: 'block-line transaction-scores',
      title: part === 'overall' ? '70% AI + 30% rules. Independent findings can still require review.' : undefined }, text);
  }

  function V4Evidence({ alertId, transactionId }) {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    async function loadEvidence() {
      if (loading || result) return;
      setLoading(true); setError('');
      try {
        const response = await fetch(transactionId ? `/api/transactions/${transactionId}/ai-evidence` : `/api/alerts/${alertId}/ai-evidence`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Model evidence unavailable');
        setResult(data);
      } catch (failure) { setError(failure.message); }
      finally { setLoading(false); }
    }
    return h('div', { className: 'v4-evidence' },
      h('button', { type: 'button', onClick: loadEvidence, disabled: loading },
        loading ? 'Loading AI reasoning...' : 'Show AI reasoning'),
      error && h('p', { role: 'status' }, error),
      result && h('div', null,
        h('p', null, result.summary),
        h('p', null, result.activity),
        h('p', null, 'Factors that influenced the AI decision:'),
        h('ul', null, result.findings.map((finding) => h('li', { key: finding.feature },
          `${finding.label} — ${finding.direction}`
        )))
      )
    );
  }

  function AlertFinding({ alert, source }) {
    const reason = (source === "ai" ? displayAiReason(alert.ai_reason) : alert.rule_reason) || `No separate ${source === "ai" ? "AI" : "rule"} reasoning recorded.`;
    const level = alert[source === "ai" ? "ai_risk_level" : "rule_level"] || "unavailable";
    return h("div", null,
      h("strong", { className: "block-line" }, labelize(level)),
      (source !== "ai" || level !== "normal") && h("span", { className: "reason-preview", title: reason }, reason),
      source === 'ai' && level === 'suspicious_pattern' && hasV4Decision(alert) && alert.transaction_id && h(V4Evidence, { transactionId: alert.transaction_id }),
      h(TransactionScores, { transaction: alert, part: source }),
      source === "rule" && alert.unclassified_reason && h("details", null,
        h("summary", null, "Recorded reason ? source unavailable"),
        h("p", null, alert.unclassified_reason))
    );
  }

  function CustomerAlertsPanel({ alerts }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "AML Alerts" }),
      alerts.length ? h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null, ["Alert", "Transaction", "Risk", "AI Findings", "Rule Findings"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          alerts.map((alert, index) => h("tr", { key: alert.id || index },
            h("td", null,
              h("strong", null, `#${alert.id || ""}`),
              h("span", { className: "muted-line block-line" }, shortTime(alert.timestamp))
            ),
            h("td", null, `#${alert.transaction_id || ""}`),
            h("td", null, h("span", { className: riskClass(alert.risk_level) }, labelize(alert.risk_level || "risk")), h(TransactionScores, { transaction: alert })),
            h("td", null, h(AlertFinding, { alert, source: "ai" })),
            h("td", null, h(AlertFinding, { alert, source: "rule" }))
          )
        )
      )) : h(EmptyState, null, "No alerts for this wallet.")
    );
  }

  function MessagingSummaryCard({ audience }) {
    return h("div", { className: "card action-card messaging-summary-card" },
      h(PanelHeading, { title: "Compliance Communications", meta: h("span", { className: "status-pill" }, "Secure Messaging") }),
      h("p", { className: "muted-line" }, audience || "Direct secure channel with compliance staff and support teams."),
      h("div", { style: { marginTop: "1rem" } },
        h("a", {
          href: "/messages",
          className: "btn btn-primary",
          style: { display: "inline-flex", alignItems: "center", gap: "0.5rem" }
        },
          h(Icon, { name: "message" }),
          "Open Message Center"
        )
      )
    );
  }

  function ModelCard({ model }) {
    return h("section", { className: "card model-card" },
      h(PanelHeading, { title: "AML decision engine", meta: h("span", { className: "status-pill" }, "V4 selected") }),
      h("h3", null, "Frozen XGBoost"),
      h("p", { className: "muted-line" }, "Customer payments are assessed after commit using verified canonical history."),
      h("dl", { className: "model-facts" },
        h("dt", null, "Decision threshold"), h("dd", null, model.threshold),
        h("dt", null, "Feature contract"), h("dd", null, "40 semantic / 42 model inputs"),
        h("dt", null, "Independent AML rules"), h("dd", null, model.rules_enabled ? "On" : "Off"),
        scoringWeights(model) ? h(window.React.Fragment, null,
          h("dt", null, "Score weights for new decisions"), h("dd", null, scoringWeights(model))) : null,
        h("dt", null, "Automatic legacy fallback"), h("dd", null, "Disabled")),
      h("p", { className: "form-hint" }, "Payments and generated demo transactions use V4. Decisions and errors are recorded for analyst review."),
      scoringWeights(model) ? h("p", { className: "form-hint" }, operationalScoreHelp(model)) : null
    );
  }

  function AdminSettings({ model, simulationBlockReason }) {
    const v4 = model?.primary_model === "V4";
    const protectedLedger = v4 || Boolean(simulationBlockReason);
    const actions = [
      {
        id: "clear-watchlist", title: "Watchlist Management", button: "Clear Watchlist",
        description: "Remove all watchlist entries. Transaction history and existing alerts are retained.",
        confirmation: "Clear all watchlist entries? This action cannot be undone.",
      },
      {
        id: "clear-transactions", title: "Transaction Records", button: "Clear All Transactions",
        description: "Clear transactions, alerts, reports and related activity from an eligible demonstration database.",
        confirmation: "Clear all transactions, alerts, reports, recent activity, and the AI model?",
        restricted: protectedLedger,
        reason: "Unavailable for this verified ledger. Clearing its history would prevent V4 from assessing subsequent payments.",
      },
      {
        id: "migrate-database", title: "Database Maintenance", button: "Migrate Database",
        description: v4 ? "Verify the current database before migration. If it is up to date, no changes are made. Required schema changes are reported for approved maintenance." : "Apply missing database tables and columns.",
        confirmation: v4 ? "Check whether the V4 database needs migration? This check does not change data or schema." : "Run database migration to add missing columns?",
      },
    ];
    return h("section", { className: "settings-layout", "aria-label": "Admin Settings" },
      h("div", { className: "card maintenance-card" },
        h(PanelHeading, { title: "System Maintenance" }),
        actions.map((action) => h("div", { className: "maintenance-row", key: action.id },
          h("div", { className: "maintenance-description" },
            h("h4", null, action.title),
            h("p", null, action.description),
            action.restricted ? h("p", { className: "maintenance-restriction", id: action.id + "-reason" }, action.reason) : null
          ),
          h("form", {
            method: "post", action: "/admin/" + action.id,
            onSubmit: (event) => {
              if (action.restricted || !window.confirm(action.confirmation)) event.preventDefault();
            },
          }, h("button", {
            type: "submit", className: "danger-button", disabled: Boolean(action.restricted),
            "aria-describedby": action.restricted ? action.id + "-reason" : undefined,
          }, action.button))
        ))
      ),
      v4 ? h(ModelCard, { model }) : null
    );
  }

  function TransactionGeneration({ generation, legacyBlockReason }) {
    const [count, setCount] = useState(30);
    const [mode, setMode] = useState("mixed");
    const [submitted, setSubmitted] = useState(false);
    const [progress, setProgress] = useState(null);
    const [statusError, setStatusError] = useState(false);
    useEffect(() => {
      if (!generation) return;
      let active = true, timer, busy = false, refreshPending = false;
      const refresh = async () => {
        if (!active) return;
        if (busy) { refreshPending = true; return; }
        busy = true;
        refreshPending = false;
        clearTimeout(timer);
        try {
          const response = await fetch("/api/admin/generation", { credentials: "same-origin", cache: "no-store" });
          if (!response.ok || !response.headers.get("content-type")?.includes("application/json")) throw new Error("Status unavailable");
          const data = await response.json();
          if (active) { setProgress(data); setStatusError(false); }
          if (active && data?.pending_v4 > 0) timer = setTimeout(refresh, 4000);
        } catch (_) {
          if (active) { setStatusError(true); timer = setTimeout(refresh, 10000); }
        } finally {
          busy = false;
          if (active && refreshPending) await refresh();
        }
      };
      refresh();
      const socket = window.getAmlSocket();
      socket?.on('transaction_batch', refresh);
      socket?.on('connect', refresh);
      window.addEventListener('focus', refresh);
      return () => {
        active = false;
        clearTimeout(timer);
        socket?.off('transaction_batch', refresh);
        socket?.off('connect', refresh);
        window.removeEventListener('focus', refresh);
      };
    }, [generation]);
    const choice = generation?.choices.find(item => item.count === count && item.mode === mode);
    const restricted = generation ? !choice : Boolean(legacyBlockReason);
    const modes = { mixed: "Balanced Mix (70% Routine / 30% Suspicious Scenarios)", ordinary: "Routine Payments", structuring: "Repeated Split Payments", network: "Wallet Network", agent: "Agent Cash Activity" };
    const routineInputs = mode === "mixed" ? Math.ceil(count * 0.7) : mode === "ordinary" ? count : 0;
    return h("section", { className: "card action-card generation-card" },
      h(PanelHeading, { title: "Transaction Generation" }),
      h("p", { className: "muted-line" }, generation
        ? `Uses ${generation.wallet_count} existing customer wallets. Payments update their balances and remain in the verified ledger. V4 analysis runs after they are saved.`
        : "Generate cash-ins, cash-outs and wallet transfers for demonstration."),
      generation && h("p", { className: "form-hint" }, generation.agent_count
        ? "Active agents are available for cash scenarios."
        : "No active agents are registered. Wallet transfers are available; cash scenarios require an active agent."),
      h("form", {
        method: "post", action: "/admin/generate-transactions",
        onSubmit: event => {
          if (restricted || submitted || !window.confirm(`Generate ${count} demo transactions? This updates customer wallet balances and adds permanent transaction records.`)) {
            event.preventDefault(); return;
          }
          setSubmitted(true);
        },
      },
        generation && h("input", { type: "hidden", name: "csrf", value: generation.csrf }),
        generation && h("input", { type: "hidden", name: "generation_token", value: choice?.token || "" }),
        generation && h("label", { htmlFor: "generation-mode" }, "Scenario"),
        generation && h("select", { id: "generation-mode", value: mode, onChange: e => setMode(e.target.value), disabled: submitted },
          Object.entries(modes).map(([value, label]) => h("option", {
            key: value, value, disabled: !generation.choices.some(item => item.mode === value),
          }, label))),
        h("label", { htmlFor: "generation-count" }, "Number of Transactions"),
        h("select", { id: "generation-count", name: "count", value: count, onChange: e => setCount(Number(e.target.value)), disabled: submitted },
          (generation ? [1, 10, 30, 100, 500, 1000, 2000, 5000] : [100, 500, 1000, 2000, 5000]).map(value => h("option", { key: value, value }, value === 30 ? '30 (demonstration)' : value.toLocaleString()))),
        generation && h("p", { className: "form-hint", "aria-live": "polite" }, `Planned inputs: ${routineInputs.toLocaleString()} routine payments and ${(count - routineInputs).toLocaleString()} suspicious-scenario payments. These are scenario intentions, not V4 results or an accuracy score.`),
        h("p", { className: "form-hint" }, "Payments use current timestamps and existing customer balances. Routine amounts and counterparties follow up to 100 recent outgoing transfers classified normal or low risk; fewer than five records means a limited baseline. Large or repeated batches can trigger independent velocity rules. V4 determines each prediction from verified history; its result ratio may differ from the input mix."),
        restricted && h("p", { className: "maintenance-restriction" }, generation ? "At least six customer wallets are required." : legacyBlockReason),
        h("button", { type: "submit", disabled: restricted || submitted }, submitted ? "Saving Transactions…" : "Generate Transactions")
      ),
      generation?.baseline_summary && h("details", { className: "card customer-baselines" },
        h("summary", null, "Customer simulation baselines"),
        h("p", null, "All customer wallets are eligible. Routine senders rotate across the customer list; a small batch may not reach every customer. Existing history is preserved. Historical normal/low classifications are observations, not proof of legitimate activity. Immediate batches do not reproduce historical timing and can trigger velocity rules."),
        h("div", { className: "table-responsive", tabIndex: 0, role: "region", "aria-label": "Customer simulation baselines" }, h("table", null,
          h("thead", null, h("tr", null, ["Wallet", "History records", "Typical amount (USD)", "Baseline", "Usual recipients"].map(label => h("th", { key: label }, label)))),
          h("tbody", null, Object.entries(generation.baseline_summary).map(([account, profile]) => h("tr", { key: account },
            h("td", null, account), h("td", null, profile.sample_count),
            h("td", null, (profile.median_minor / 100).toFixed(2)),
            h("td", null, profile.sufficient_history ? "Historical" : "Limited history"),
            h("td", null, profile.counterparties.join(", ") || "No established customer recipient"))))
        ))),
      statusError && h("p", { role: "status", className: "form-hint" }, "Generation status is temporarily unavailable. Do not submit another batch to retry analysis."),
      generation?.last_request && progress?.saved === 0 && h("form", {
        method: "post", action: "/admin/generate-transactions",
        onSubmit: event => { if (!window.confirm("Retry the previous request with its original payment IDs?")) event.preventDefault(); },
      },
        h("input", { type: "hidden", name: "csrf", value: generation.csrf }),
        h("input", { type: "hidden", name: "generation_token", value: generation.last_request.token }),
        h("button", { type: "submit", className: "secondary-button" }, "Retry Previous Request")
      ),
      progress && h("div", { className: "generation-progress", role: "status", "aria-live": "polite" },
        h("h4", null, "Latest Batch"),
        progress.ordinary_inputs != null && h("p", null, `Input scenarios: ${progress.ordinary_inputs} routine · ${progress.suspicious_inputs} suspicious`),
        h("p", null, `${progress.saved} / ${progress.requested} saved · ${progress.normal} V4 normal · ${progress.suspicious_pattern} V4 suspicious · ${progress.pending_v4} pending · ${progress.inference_error} errors`),
        progress.pending_v4 > 0 && h("progress", { max: progress.requested, value: progress.normal + progress.suspicious_pattern + progress.inference_error, "aria-label": "V4 analysis progress" }),
        progress.inference_error > 0 && h("p", { className: "form-hint" }, "Errors remain available for compliance review and audited inference retry. Payments must not be repeated.")
      )
    );
  }

  function AdminDashboard({ initialData }) {
    const [users, setUsers] = useState(initialData.users || []);
    const [activity, setActivity] = useState(initialData.activity || []);
    const [transactions, setTransactions] = useState(initialData.transactions || []);
    const [watchlist, setWatchlist] = useState(initialData.watchlist || []);
    const [stats, setStats] = useState(initialData.system_stats || {});
    const [activeSection, setActiveSection] = useState("overview");
    const [selectedUserId, setSelectedUserId] = useState(String(initialData.users?.[0]?.id || ""));
    const [kycSaving, setKycSaving] = useState(false);
    const selectedUser = users.find(user => String(user.id) === selectedUserId);
    const [kycDraft, setKycDraft] = useState(null);
    async function saveKyc(event) {
      event.preventDefault();
      if (kycSaving) return;
      const body = new FormData(event.currentTarget);
      setKycSaving(true);
      try {
        const response = await fetch('/admin', { method: 'POST', body, headers: { Accept: 'application/json' } });
        if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('Unable to update KYC. Check your session and try again.');
        const data = await response.json();
        if (data.status !== 'success') throw new Error('KYC update failed.');
        setUsers(current => current.map(user => String(user.id) === String(data.user.user_id) ? { ...user, kyc_status: data.user.kyc_status } : user));
        setKycDraft(null);
        window.showAmlNotification('KYC status updated.', 'kyc-update', 'success');
      } catch (error) {
        window.showAmlNotification(error.message, 'kyc-update', 'error');
      } finally { setKycSaving(false); }
    }


    const sidebarItems = [
      { id: "overview", label: "Overview", icon: "home" },
      { id: "users", label: "User Management", icon: "users" },
      { id: "transactions", label: "Transactions", icon: "list" },
      { id: "generation", label: "Transaction Generation", icon: "activity" },
      { id: "watchlist", label: "Watchlist", icon: "shield" },
      { id: "activity", label: "Activity Feed", icon: "activity" },
      { id: "messages", label: "Messages", href: "/messages", icon: "message" },
      { id: "settings", label: "Settings", icon: "settings" },
      { id: "reports", label: "Reports", href: "/reports", icon: "file" },
      { id: "signout", label: "Sign Out", href: "/logout", icon: "logout" }
    ];



    useRealtime({
      transaction: (txn) => {
        setTransactions((current) => upsertRecentTransaction(current, txn, 20));
      },
      balance: (event) => {
        setUsers((current) => current.map((user) => (
          user.account_number === event.account_number
            ? { ...user, balance: event.balance, kyc_status: event.kyc_status || user.kyc_status }
            : user
        )));
      },
      user: (event) => {
        setUsers((current) => current.map((user) => (
          user.id === event.user_id
            ? { ...user, balance: event.balance, kyc_status: event.kyc_status || user.kyc_status }
            : user
        )));
      },
      activity: (event) => setActivity((current) => trim([event, ...current], 25)),
      ai_model: (model) => setActivity((current) => trim([{
        timestamp: model.timestamp,
        action: "ai_model",
        detail: `${model.trained ? "trained" : "waiting for more labels"} on ${model.training_rows} rows`,
      }, ...current], 25)),
      transaction_batch: (batch) => setActivity((current) => trim([{
        timestamp: batch.timestamp,
        action: "transaction_batch",
        detail: `generated ${batch.count} transactions`,
      }, ...current], 25)),
      watchlist: (entry) => setWatchlist((current) => trim([entry, ...current], 20)),
      stats: setStats,
      reset: () => {
        setTransactions([]);
        setActivity([]);
      },
    });

    const metricItems = [
      { label: "Users", value: stats.total_users ?? users.length, caption: "registered wallets" },
      { label: "KYC outstanding", value: stats.kyc_pending || 0, caption: "requires review" },
      { label: "PEP customers", value: stats.pep_customers || 0, caption: "enhanced due diligence" },
      { label: "Transactions", value: stats.total_transactions || 0, caption: "monitored ledger" },
      { label: "Open alerts", value: stats.open_alerts || 0, caption: "active cases" },
      { label: "Draft SARs", value: stats.pending_sars || 0, caption: "pending review" },
      { label: "Pending CTRs", value: stats.pending_ctrs || 0, caption: "currency reports" },
    ];

    const renderSection = () => {
      switch (activeSection) {
        case "overview":
          return h(window.React.Fragment, null,
            h(StatGrid, { items: metricItems }),
            h("section", { className: "react-dashboard-grid" },
              h(TransactionGeneration, { generation: initialData.generation, legacyBlockReason: initialData.simulation_block_reason }),
              h("div", { className: "card action-card" },
                h(PanelHeading, { title: "Manage Users" }),
                h("form", { method: "post", action: "/admin", onSubmit: saveKyc },
                  h("input", { type: "hidden", name: "action", value: "update_role" }),
                  h("label", null, "User"),
                  h("select", { name: "user_id", value: selectedUserId, disabled: kycSaving, onChange: event => { setSelectedUserId(event.target.value); setKycDraft(null); } },
                    users.map((user) => h("option", { value: user.id, key: user.id }, `${user.username} (${user.role})`))
                  ),
                  h("label", null, "KYC Status"),
                  h("p", { role: "status", "aria-live": "polite" }, `Current KYC status: ${selectedUser?.kyc_status || "pending"}`),
                  h("select", { name: "kyc_status", value: kycDraft ?? selectedUser?.kyc_status ?? "pending", disabled: kycSaving, onChange: event => setKycDraft(event.target.value) },
                    h("option", { value: "pending" }, "Pending"),
                    h("option", { value: "verified" }, "Verified"),
                    h("option", { value: "rejected" }, "Rejected"),
                    h("option", { value: "pending_edd" }, "Pending enhanced due diligence")
                  ),
                  h("button", { type: "submit", disabled: kycSaving }, kycSaving ? "Saving..." : "Update User")
                )
              ),
              h("div", { className: "card action-card" },
                h(PanelHeading, { title: "Watchlist Entry" }),
                h("form", { method: "post", action: "/admin" },
                  h("input", { type: "hidden", name: "action", value: "add_watchlist" }),
                  h("label", null, "Name"),
                  h("input", { name: "wl_name", required: true }),
                  h("label", null, "ID Number"),
                  h("input", { name: "wl_id_number" }),
                  h("label", null, "List Type"),
                  h("select", { name: "wl_type", defaultValue: "internal" },
                    h("option", { value: "internal" }, "Internal"),
                    h("option", { value: "pep" }, "PEP"),
                    h("option", { value: "sanctions" }, "Sanctions")
                  ),
                  h("label", null, "Reason"),
                  h("input", { name: "wl_reason" }),
                  h("button", { type: "submit" }, "Add to Watchlist")
                )
              ),
              h(MessagingSummaryCard, { audience: "Coordinate with compliance officers and customer support without leaving the AML control workflow." })
            )
          );
        case "users":
          return h(UsersTable, { users });
        case "transactions":
          return h(AdminTransactionsPanel, { transactions });
        case "generation":
          return h(TransactionGeneration, { generation: initialData.generation, legacyBlockReason: initialData.simulation_block_reason });
        case "watchlist":
          return h(WatchlistPanel, { watchlist });
        case "activity":
          return h(ActivityPanel, { activity });
        case "settings":
          return h(AdminSettings, { model: initialData.model, simulationBlockReason: initialData.simulation_block_reason });
        default:
          return null;
      }
    };

    return h("div", { className: "admin-layout" },
      h(DashboardSidebar, { sidebarItems, activeSection, setActiveSection, role: "Institutional Admin" }),
      h("div", { className: "admin-content section-transition", key: activeSection }, renderSection())
    );
  }

  function ActivityPanel({ activity }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Recent Activity" }),
      activity.length ? h("ul", null, activity.map((event, index) => (
        h("li", { className: "activity-item", key: `${event.timestamp || ""}-${index}` },
          h("strong", null, `${event.actor || "system"}: ${labelize(event.action || "")}`),
          h("span", { className: "muted-line block-line" }, shortTime(event.timestamp)),
          h("p", null, `${event.detail || ""}${event.ip_address ? ` · ${event.ip_address}` : ""}`)
        )
      ))) : h(EmptyState, null, "No activity recorded yet.")
    );
  }

  function AdminTransactionsPanel({ transactions }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Recent Transactions" }),
      transactions.length ? h("table", { className: "data-table admin-transactions-table" },
        h("thead", null,
          h("tr", null, ["ID", "Time", "Route", "Type / channel", "Amount", "Risk", "AI Findings", "Rule Findings", "CTR / SAR", "Status"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          transactions.map((txn, index) => h("tr", { key: txn.id || index },
            h("td", null, txn.id || ""),
            h("td", null, shortTime(txn.timestamp)),
            h("td", null, `${txn.sender_account || ""} -> ${txn.receiver_account || ""}`),
            h("td", null, `${labelizeTransactionType(txn.transaction_type)} / ${txn.channel || "online"}`),
            h("td", null, money(txn.amount)),
            h("td", null, h("span", { className: riskClass(txn.risk_level) }, labelize(txn.risk_level)), h(TransactionScores, { transaction: txn })),
            h("td", null, h(AlertFinding, { alert: { ...txn, transaction_id: txn.id }, source: "ai" })),
            h("td", null, h(AlertFinding, { alert: txn, source: "rule" })),
            h("td", null, txn.ctr_required && txn.sar_required ? "CTR / SAR" : txn.ctr_required ? "CTR" : txn.sar_required ? "SAR" : "—"),
            h("td", null, txn.status || "Completed")
          ))
        )
      ) : h(EmptyState, null, "No transactions to show.")
    );
  }

  function WatchlistPanel({ watchlist }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Watchlist" }),
      watchlist.length ? h("ul", null, watchlist.map((entry, index) => (
        h("li", { className: "activity-item", key: entry.id || index },
          h("strong", null, `${entry.name || ""} (${entry.list_type || "internal"})`),
          h("span", { className: "status-pill block-fit" }, entry.list_type || "internal"),
          h("p", null, `${entry.reason || "No reason recorded"} · ${entry.account_number || entry.id_number || "No account/ID"} · added by ${entry.added_by || "unknown"} ${shortTime(entry.added_at)}`)
        )
      ))) : h(EmptyState, null, "No watchlist entries.")
    );
  }

  function UsersTable({ users }) {
    return h("section", { className: "card table-card" },
      h(PanelHeading, { title: "Registered Users" }),
      h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null,
            ["ID", "Username", "Email", "ID Number", "Wallet Number", "Role", "Balance", "KYC", "PEP", "Risk", "Wealth", "Created"].map((head) => h("th", { key: head }, head))
          )
        ),
        h("tbody", null,
          users.map((user) => h("tr", { key: user.id },
            h("td", null, user.id),
            h("td", null, user.username),
            h("td", null, user.email),
            h("td", null, user.id_number),
            h("td", null, user.account_number),
            h("td", null, user.role),
            h("td", null, money(user.balance)),
            h("td", null, h("span", { className: user.kyc_status === "verified" ? "status-pill" : "status-pill alert" }, user.kyc_status || "pending")),
            h("td", null, user.pep_flag ? "Yes" : "No"),
            h("td", null, labelize(user.risk_rating || "standard")),
            h("td", null, labelize(user.wealth_segment || "average")),
            h("td", null, user.created_at)
          ))
        )
      )
    );
  }

  function ComplianceDashboard({ initialData }) {
    const [transactions, setTransactions] = useState(initialData.transactions || []);
    const [alerts, setAlerts] = useState(initialData.open_alerts || []);
    const [stats, setStats] = useState(initialData.stats || {});
    const [feed, setFeed] = useState([]);
    const [status, setStatus] = useState("Connecting to live updates");
    const [activeSection, setActiveSection] = useState("overview");
    const filterValue = initialData.filter_value || "all";

    const sidebarItems = [
      { id: "overview", label: "Overview", icon: "home" },
      { id: "alerts", label: "Alerts", icon: "alert" },
      { id: "transactions", label: "Transactions", icon: "list" },
      { id: "activity", label: "Activity Feed", icon: "activity" },
      { id: "messages", label: "Messages", href: "/messages", icon: "message" },
      { id: "reports", label: "Reports", href: "/reports", icon: "file" },
      { id: "signout", label: "Sign Out", href: "/logout", icon: "logout" }
    ];


    const addFeed = (text) => setFeed((current) => trim([{ text, timestamp: new Date().toLocaleTimeString() }, ...current], 30));
    const passesFilter = (txn) => {
      if (filterValue === "flagged") return txn.risk_level !== "normal";
      if (filterValue === "suspicious") return suspiciousLevels.includes(txn.risk_level);
      if (filterValue === "ctr") return Boolean(txn.ctr_required);
      if (filterValue === "sar") return Boolean(txn.sar_required);
      return true;
    };

    useRealtime({
      connect: () => setStatus("Live updates connected"),
      disconnect: () => setStatus("Disconnected. Reconnecting..."),
      connect_error: () => setStatus("Live updates unavailable. Reload to refresh."),
      transaction: (txn) => {
        setTransactions((current) => passesFilter(txn)
          ? upsertRecentTransaction(current, txn, 25)
          : current.filter((item) => String(item.id) !== String(txn.id)));
        addFeed(`Transaction | Tx #${txn.id || ""} | ${txn.risk_level || "normal"} | Score ${score(txn.risk_score)}`);
      },
      alert: (alert) => {
        setAlerts((current) => upsert(current, alert, 30));
        setStatus("New alert received | stream active");
        addFeed(`Alert | Tx #${alert.transaction_id || ""} | ${alert.risk_level || ""} | AI: ${(alert.ai_risk_level === "normal" ? "Normal" : displayAiReason(alert.ai_reason) || "Not recorded")} | Rules: ${alert.rule_reason || "Not recorded"}`);
      },
      alert_update: (alert) => {
        setAlerts((current) => {
          if (alert.status !== "open") return current.filter((item) => String(item.id) !== String(alert.id));
          const exists = current.some((item) => String(item.id) === String(alert.id));
          return exists
            ? current.map((item) => String(item.id) === String(alert.id) ? { ...item, ...alert } : item)
            : upsert(current, alert, 30);
        });
        addFeed(`Alert status | #${alert.id || ""} | ${alert.status || ""}`);
      },
      ai_model: (model) => addFeed(`AI model | ${model.trained ? "trained" : "waiting for more labels"} | ${model.training_rows} rows`),
      sar_report: (report) => addFeed(`SAR report | #${report.id || ""} | ${report.status || "created"}`),
      ctr_report: (report) => addFeed(`CTR report | #${report.id || ""} | ${report.status || "created"}`),
      transaction_batch: (batch) => addFeed(`Batch | generated ${batch.count || 0} transactions`),
      stats: setStats,
      reset: () => {
        setTransactions([]);
        setAlerts([]);
        setFeed([]);
        setStatus("Reset received | stream active");
      },
    });

    const alertPageCount = useMemo(() => {
      return Math.max(1, Math.ceil(Number(initialData.open_alert_count || 0) / Number(initialData.page_size || 25)));
    }, [initialData.open_alert_count, initialData.page_size]);

    const metricItems = [
      { label: "Total transactions", value: stats.total_transactions ?? 0, caption: "all recorded transactions" },
      { label: "Open alerts", value: stats.open_alerts ?? alerts.length, caption: "needs review" },
      { label: "High risk today", value: stats.high_risk_today || 0, caption: "new severe activity" },
      { label: "Draft SARs", value: stats.pending_sars || 0, caption: "case narratives" },
      { label: "Pending CTRs", value: stats.pending_ctrs || 0, caption: "currency reports" },
    ];

    const renderSection = () => {
      switch (activeSection) {
        case "overview":
          return h(window.React.Fragment, null,
            h(StatGrid, { items: metricItems }),
            h("section", { className: "compliance-dashboard-grid grid" },
              h(AlertsPanel, { alerts, page: initialData.alert_page, pageCount: alertPageCount }),
            )
          );
        case "alerts":
          return h(AlertsPanel, { alerts, page: initialData.alert_page, pageCount: alertPageCount });
        case "transactions":
          return h(ComplianceTransactionsPanel, { transactions, model: initialData.model });
        case "activity":
          return h("section", { className: "card table-card" },
            h(PanelHeading, { title: "Live Compliance Feed", meta: h(LiveStatus, null, status) }),
            feed.length ? h("ul", null, feed.map((event, index) => (
              h("li", { className: "activity-item", key: `${event.timestamp}-${index}` },
                h("strong", null, event.timestamp),
                h("p", null, event.text)
              )
            ))) : h(EmptyState, null, "Waiting for live events.")
          );
        default:
          return null;
      }
    };

    return h("div", { className: "admin-layout" },
      h(DashboardSidebar, { sidebarItems, activeSection, setActiveSection, role: "Compliance Operations" }),
      h("div", { className: "admin-content section-transition", key: activeSection }, renderSection())
    );
  }

  function ComplianceTransactionsPanel({ transactions, model }) {
    const [filter, setFilter] = useState("all");

    const filteredTransactions = filter === "all"
      ? transactions
      : transactions.filter(txn => txn.risk_level === filter);

    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Transactions" }),
      h("div", { className: "filter-bar" },
        h("label", null, "Filter by Risk:"),
        h("select", {
          value: filter,
          onChange: (e) => setFilter(e.target.value),
          className: "filter-select"
        },
          h("option", { value: "all" }, "All"),
          h("option", { value: "critical" }, "Critical"),
          h("option", { value: "high_risk" }, "High Risk"),
          h("option", { value: "suspicious" }, "Suspicious"),
          h("option", { value: "normal" }, "Normal")
        )
      ),
      filteredTransactions.length ? h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null, ["Transaction", "Type", "Amount", "Risk", "AI Findings", "Rule Findings"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          filteredTransactions.map((txn, index) => h("tr", { key: txn.id || index },
            h("td", null,
              h("strong", null, `#${txn.id || ""}`),
              h("span", { className: "muted-line block-line" }, shortTime(txn.timestamp))
            ),
            h("td", null, labelizeTransactionType(txn.transaction_type || txn.type)),
            h("td", null, money(txn.amount)),
            h("td", null, h("span", { className: riskClass(txn.risk_level) }, labelize(txn.risk_level)), h(TransactionScores, { transaction: txn })),
            h("td", null,
              h("span", { className: riskClass(txn.ai_risk_level || txn.risk_level) }, labelize(txn.ai_risk_level || "unavailable")),
              txn.ai_risk_level !== "normal" && h("span", { className: "muted-line block-line" }, displayAiReason(txn.ai_reason) || "No AI reason recorded"),
              txn.ai_risk_level === "suspicious_pattern" && hasV4Decision(txn) && h(V4Evidence, { transactionId: txn.id }),
              h(TransactionScores, { transaction: txn, part: "ai" })
            ),
            h("td", null, txn.rule_reason || "No rule indicators", h(TransactionScores, { transaction: txn, part: "rule" }))
          ))
        )
      ) : h(EmptyState, null, "No transactions match this filter.")
    );
  }

  function AlertsPanel({ alerts, page = 1, pageCount = 1 }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Open Alerts" }),
      alerts.length ? h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null, ["Alert", "Wallet", "Risk", "AI Findings", "Rule Findings", "Action"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          alerts.map((alert, index) => h("tr", { key: alert.id || index },
            h("td", null,
              h("strong", null, `#${alert.id || ""}`),
              h("span", { className: "muted-line block-line" }, `Tx #${alert.transaction_id || ""}`)
            ),
            h("td", null, alert.account_number || ""),
            h("td", null, h("span", { className: riskClass(alert.risk_level) }, labelize(alert.risk_level || "risk")), h(TransactionScores, { transaction: alert })),
            h("td", null, h(AlertFinding, { alert, source: "ai" })),
            h("td", null, h(AlertFinding, { alert, source: "rule" })),
            h("td", null, alert.id
              ? h("a", { className: "action-link", href: `/compliance/alert/${alert.id}` }, "Review")
              : h("span", { className: "muted-line" }, "Pending")
            )
          )
        )
      )) : h(EmptyState, null, "No open alerts."),
      pageCount > 1 ? h("nav", { className: "queue-pagination", "aria-label": "Open alert pages" },
        h("a", {
          className: page <= 1 ? "action-link pagination-disabled" : "action-link",
          href: page <= 1 ? undefined : `/compliance?alert_page=${page - 1}`,
          "aria-disabled": page <= 1
        }, "Previous"),
        h("span", { className: "muted-line" }, `Page ${page} of ${pageCount}`),
        h("a", {
          className: page >= pageCount ? "action-link pagination-disabled" : "action-link",
          href: page >= pageCount ? undefined : `/compliance?alert_page=${page + 1}`,
          "aria-disabled": page >= pageCount
        }, "Next")
      ) : null
    );
  }

  if (adminRoot) {
    window.ReactDOM.createRoot(adminRoot).render(
      h(AdminDashboard, { initialData: readJson("admin-dashboard-data") })
    );
  }

  if (complianceRoot) {
    window.ReactDOM.createRoot(complianceRoot).render(
      h(ComplianceDashboard, { initialData: readJson("compliance-dashboard-data") })
    );
  }

  if (customerRoot) {
    window.ReactDOM.createRoot(customerRoot).render(
      h(CustomerDashboard, { initialData: readJson("customer-dashboard-data") })
    );
  }
})();
