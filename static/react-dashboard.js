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

  window.__amlSidebarController = window.__amlSidebarController || {
    listeners: new Set(),
    register(handler) {
      this.listeners.add(handler);
      return () => this.listeners.delete(handler);
    },
    toggle() {
      this.listeners.forEach((handler) => handler());
    },
    close() {
      this.listeners.forEach((handler) => handler(false));
    }
  };

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
    return `$${Number(value || 0).toFixed(2)}`;
  }

  function score(value) {
    return Number(value || 0).toFixed(0);
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
      items.map((item) => h("div", { className: "metric-tile", key: item.label },
        h("span", { className: "metric-label" }, item.label),
        h("strong", null, item.value),
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
    return [item, ...items.filter((row) => String(row.id) !== String(item.id))].slice(0, limit);
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

    // Listen for sidebar toggle click from header
    useEffect(() => {
      const handleToggleClick = (nextValue) => {
        if (typeof nextValue === 'boolean') {
          setSidebarOpen(nextValue);
          return;
        }
        setSidebarOpen((prev) => !prev);
      };
      const unregister = window.__amlSidebarController.register(handleToggleClick);
      const fallback = () => handleToggleClick();
      window.addEventListener('sidebar-toggle-click', fallback);
      return () => {
        unregister();
        window.removeEventListener('sidebar-toggle-click', fallback);
      };
    }, []);

    return h(window.React.Fragment, null,
      sidebarOpen && h("div", {
        className: "sidebar-overlay active",
        onClick: () => setSidebarOpen(false)
      }),
      h("aside", { className: `admin-sidebar ${sidebarOpen ? "open" : ""}` },
        h("div", { className: "sidebar-brand" },
          h("span", { className: "sidebar-brand__title" }, "WORKSPACE"),
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
                setSidebarOpen(false);
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
    const [activeSection, setActiveSection] = useState("overview");
    // Native form resubmissions preserve this value; a new dashboard draft gets a new one.
    const [transactionRequestId] = useState(() =>
      window.crypto && window.crypto.randomUUID ? window.crypto.randomUUID() : "");

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
        addFeed(`Alert | Tx #${alert.transaction_id || ""} | ${alert.risk_level || ""} | Score ${score(alert.risk_score)} | ${alert.reason || ""}`);
      },
      alert_update: (alert) => {
        if (alert.account_number !== accountNumber) return;
        setAlerts((current) => {
          if (alert.status !== "open") return current.filter((item) => String(item.id) !== String(alert.id));
          const exists = current.some((item) => String(item.id) === String(alert.id));
          return exists
            ? current.map((item) => String(item.id) === String(alert.id) ? alert : item)
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
      { label: "Transactions", value: stats.total_tx || transactions.length, caption: "wallet history" },
      { label: "Flagged", value: stats.flagged || 0, caption: "requires attention" },
      { label: "Open alerts", value: stats.open_alerts || alerts.filter((alert) => alert.status === "open").length, caption: "live cases" },
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
                h("form", { method: "post", action: "/customer/transaction" },
                  h("input", { type: "hidden", name: "client_request_id", value: transactionRequestId }),
                  h("input", { type: "hidden", name: "canonical_version", value: "mobile_money.canonical.v1" }),
                  h("input", { type: "hidden", name: "currency", value: "USD" }),
                  h("label", null, "Type"),
                  h("select", { name: "type", defaultValue: "wallet_to_wallet" },
                    h("option", { value: "cash_in" }, "Cash In"),
                    h("option", { value: "cash_out" }, "Cash Out"),
                    h("option", { value: "wallet_to_wallet" }, "Send Money")
                  ),
                  h("label", null, "Amount"),
                  h("input", { type: "number", min: "0.01", max: "15000.00", step: "0.01", name: "amount", required: true }),
                  h("label", null, "Recipient Wallet Number"),
                  h("input", { name: "recipient", placeholder: "ACC1004" }),
                  h("p", { className: "form-hint" }, "For direct transfers, enter the receiving wallet. For cash in or cash out, complete the agent service details below."),
                  h("details", { className: "agent-details" },
                  h("summary", null, "Agent service / cash transaction details"),
                  h("label", null, "Service channel"),
                  h("select", { name: "channel", defaultValue: "direct_wallet" },
                    h("option", { value: "direct_wallet" }, "Direct wallet transfer"),
                    h("option", { value: "agent" }, "Agent service")
                  ),
                  h("label", null, "Agent ID (required for agent service)"),
                  h("input", { name: "agent_id", inputMode: "numeric" }),
                  h("label", null, "Wallet serviced by the agent"),
                  h("input", { name: "serviced_wallet", placeholder: accountNumber }),
                  h("label", null, "Cash direction"),
                  h("select", { name: "agent_flow_direction", defaultValue: "none" },
                    h("option", { value: "none" }, "No cash — wallet transfer"),
                    h("option", { value: "cash_in" }, "Cash in"),
                    h("option", { value: "cash_out" }, "Cash out")
                  ),
                  h("p", { className: "form-hint" }, "Cash requires an agent, your wallet as the serviced wallet, and the matching cash direction. For agent-assisted transfers, name exactly one serviced endpoint. Leave agent and serviced wallet empty for direct transfers."),
                  ),
                  !transactionRequestId && h("p", { className: "form-hint" },
                    "Secure request IDs are unavailable in this browser. Please use a supported browser."),
                  h("button", { type: "submit", disabled: !transactionRequestId },
                    "Confirm transaction")
                )
              ),
            )
          );
        case "transactions":
          return h(CustomerTransactionsPanel, { transactions });
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
      h("div", { className: "admin-content" }, renderSection())
    );
  }

  function CustomerTransactionsPanel({ transactions }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "Recent Transactions" }),
      transactions.length ? h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null, ["Transaction", "Type", "Amount", "Risk", "Recorded AI"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          transactions.map((txn, index) => h("tr", { key: txn.id || index },
            h("td", null,
              h("strong", null, `#${txn.id || ""}`),
              h("span", { className: "muted-line block-line" }, shortTime(txn.timestamp))
            ),
            h("td", null, labelizeTransactionType(txn.transaction_type || txn.type)),
            h("td", null, money(txn.amount)),
            h("td", null,
              h("span", { className: riskClass(txn.risk_level) }, labelize(txn.risk_level)),
              h("span", { className: "muted-line block-line" }, `Operational score ${score(txn.risk_score)}`)
            ),
            h("td", null,
              h("span", null, labelize(txn.ai_risk_level || "unavailable")),
              h("span", { className: "muted-line block-line" }, confidence(["pending_v4", "inference_error"].includes(txn.ai_risk_level) ? null : txn.ai_confidence))
            )
          ))
        )
      ) : h(EmptyState, null, "No transactions to show.")
    );
  }

  function CustomerAlertsPanel({ alerts }) {
    return h("div", { className: "card table-card" },
      h(PanelHeading, { title: "AML Alerts" }),
      alerts.length ? h("table", { className: "data-table" },
        h("thead", null,
          h("tr", null, ["Alert", "Transaction", "Risk", "Reason"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          alerts.map((alert, index) => h("tr", { key: alert.id || index },
            h("td", null,
              h("strong", null, `#${alert.id || ""}`),
              h("span", { className: "muted-line block-line" }, shortTime(alert.timestamp))
            ),
            h("td", null, `#${alert.transaction_id || ""}`),
            h("td", null, h("span", { className: riskClass(alert.risk_level) }, labelize(alert.risk_level || "risk"))),
            h("td", null, alert.reason || "")
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
        h("dt", null, "Automatic legacy fallback"), h("dd", null, "Disabled")),
      h("p", { className: "form-hint" }, "Batch generators and destructive maintenance are unavailable in V4 mode. Decisions and errors are recorded for analyst review.")
    );
  }

  function AdminDashboard({ initialData }) {
    const [users, setUsers] = useState(initialData.users || []);
    const [activity, setActivity] = useState(initialData.activity || []);
    const [transactions, setTransactions] = useState(initialData.transactions || []);
    const [watchlist, setWatchlist] = useState(initialData.watchlist || []);
    const [stats, setStats] = useState(initialData.system_stats || {});
    const [activeSection, setActiveSection] = useState("overview");

    const sidebarItems = [
      { id: "overview", label: "Overview", icon: "home" },
      { id: "users", label: "User Management", icon: "users" },
      { id: "transactions", label: "Transactions", icon: "list" },
      { id: "watchlist", label: "Watchlist", icon: "shield" },
      { id: "activity", label: "Activity Feed", icon: "activity" },
      { id: "messages", label: "Messages", href: "/messages", icon: "message" },
      { id: "settings", label: "Settings", icon: "settings" },
      { id: "reports", label: "Reports", href: "/reports", icon: "file" },
      { id: "signout", label: "Sign Out", href: "/logout", icon: "logout" }
    ];



    useRealtime({
      transaction: (txn) => {
        setTransactions((current) => upsert(current, txn, 20));
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
      { label: "Users", value: stats.total_users || users.length, caption: "registered wallets" },
      { label: "KYC outstanding", value: stats.kyc_pending || 0, caption: "requires review" },
      { label: "PEP customers", value: stats.pep_customers || 0, caption: "enhanced due diligence" },
      { label: "Transactions", value: stats.total_transactions || 0, caption: "monitored ledger" },
      { label: "Flagged transactions", value: stats.flagged_transactions || 0, caption: "AML indicators" },
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
              initialData.model?.primary_model === "V4" ? h(ModelCard, { model: initialData.model }) : h("div", { className: "card action-card" },
                h(PanelHeading, { title: "Mobile-Money Transaction Simulator", meta: h("span", { className: "status-pill" }, "Wallet users only") }),
                h("p", { className: "muted-line" }, "Generate realistic cash-ins, cash-outs, and wallet transfers using registered EpoCash wallets."),
                h("form", { method: "post", action: "/admin/generate-transactions" },
                  h("label", null, "Number of Transactions"),
                  h("select", { name: "count", defaultValue: "100" },
                    h("option", { value: "100" }, "100"),
                    h("option", { value: "500" }, "500"),
                    h("option", { value: "1000" }, "1000"),
                    h("option", { value: "2000" }, "2000"),
                    h("option", { value: "5000" }, "5000")
                  ),
                  h("button", { type: "submit" }, "Generate Transactions")
                )
              ),
              h("div", { className: "card action-card" },
                h(PanelHeading, { title: "Manage Users" }),
                h("form", { method: "post", action: "/admin" },
                  h("input", { type: "hidden", name: "action", value: "update_role" }),
                  h("label", null, "User"),
                  h("select", { name: "user_id" },
                    users.map((user) => h("option", { value: user.id, key: user.id }, `${user.username} (${user.role})`))
                  ),
                  h("label", null, "KYC Status"),
                  h("select", { name: "kyc_status", defaultValue: "pending" },
                    h("option", { value: "pending" }, "Pending"),
                    h("option", { value: "verified" }, "Verified"),
                    h("option", { value: "rejected" }, "Rejected")
                  ),
                  h("button", { type: "submit" }, "Update User")
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
        case "watchlist":
          return h(WatchlistPanel, { watchlist });
        case "activity":
          return h(ActivityPanel, { activity });
        case "settings":
          if (initialData.model?.primary_model === "V4") return h(ModelCard, { model: initialData.model });
          return h("section", { className: "admin-danger-zone" },
            h("div", { className: "card action-card" },
              h(PanelHeading, { title: "System Maintenance" }),
              h("form", {
                method: "post",
                action: "/admin/clear-transactions",
                onSubmit: (event) => {
                  if (!window.confirm("Clear all transactions, alerts, reports, recent activity, and the AI model?")) {
                    event.preventDefault();
                  }
                },
              },
                h("button", { type: "submit", className: "danger-button" }, "Clear All Transactions")
              ),
              h("form", {
                method: "post",
                action: "/admin/clear-watchlist",
                onSubmit: (event) => {
                  if (!window.confirm("Clear all watchlist entries?")) {
                    event.preventDefault();
                  }
                },
              },
                h("button", { type: "submit", className: "danger-button" }, "Clear Watchlist")
              ),
              h("form", {
                method: "post",
                action: "/admin/migrate-database",
                onSubmit: (event) => {
                  if (!window.confirm("Run database migration to add missing columns?")) {
                    event.preventDefault();
                  }
                },
              },
                h("button", { type: "submit", className: "danger-button" }, "Migrate Database")
              )
            )
          );
        default:
          return null;
      }
    };

    return h("div", { className: "admin-layout" },
      h(DashboardSidebar, { sidebarItems, activeSection, setActiveSection, role: "Institutional Admin" }),
      h("div", { className: "admin-content" }, renderSection())
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
          h("tr", null, ["ID", "Time", "Route", "Type / channel", "Amount", "Risk", "CTR / SAR", "Status"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          transactions.map((txn, index) => h("tr", { key: txn.id || index },
            h("td", null, txn.id || ""),
            h("td", null, shortTime(txn.timestamp)),
            h("td", null, `${txn.sender_account || ""} -> ${txn.receiver_account || ""}`),
            h("td", null, `${labelizeTransactionType(txn.transaction_type)} / ${txn.channel || "online"}`),
            h("td", null, money(txn.amount)),
            h("td", null, h("span", { className: riskClass(txn.risk_level) }, `${labelize(txn.risk_level)} (${score(txn.risk_score)})`)),
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
        if (passesFilter(txn)) setTransactions((current) => upsert(current, txn, 25));
        addFeed(`Transaction | Tx #${txn.id || ""} | ${txn.risk_level || "normal"} | Score ${score(txn.risk_score)}`);
      },
      alert: (alert) => {
        setAlerts((current) => upsert(current, alert, 30));
        setStatus("New alert received | stream active");
        addFeed(`Alert | Tx #${alert.transaction_id || ""} | ${alert.risk_level || ""} | ${alert.reason || ""}`);
      },
      alert_update: (alert) => {
        setAlerts((current) => {
          if (alert.status !== "open") return current.filter((item) => String(item.id) !== String(alert.id));
          const exists = current.some((item) => String(item.id) === String(alert.id));
          return exists
            ? current.map((item) => String(item.id) === String(alert.id) ? alert : item)
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
      { label: "Open alerts", value: stats.open_alerts || alerts.length, caption: "needs review" },
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
          return h(ComplianceTransactionsPanel, { transactions });
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
      h("div", { className: "admin-content" }, renderSection())
    );
  }

  function ComplianceTransactionsPanel({ transactions }) {
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
          h("tr", null, ["Transaction", "Type", "Amount", "AI Assessment"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          filteredTransactions.map((txn, index) => h("tr", { key: txn.id || index },
            h("td", null,
              h("strong", null, `#${txn.id || ""}`),
              h("span", { className: "muted-line block-line" }, shortTime(txn.timestamp))
            ),
            h("td", null, labelizeTransactionType(txn.transaction_type || txn.type)),
            h("td", null, money(txn.amount)),
            h("td", null,
              h("span", { className: riskClass(txn.ai_risk_level || txn.risk_level) }, labelize(txn.ai_risk_level || "unavailable")),
              h("span", { className: "muted-line block-line" }, `Operational score ${score(txn.risk_score)}`)
            )
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
          h("tr", null, ["Alert", "Wallet", "Risk", "Reason", "Action"].map((head) => h("th", { key: head }, head)))
        ),
        h("tbody", null,
          alerts.map((alert, index) => h("tr", { key: alert.id || index },
            h("td", null,
              h("strong", null, `#${alert.id || ""}`),
              h("span", { className: "muted-line block-line" }, `Tx #${alert.transaction_id || ""}`)
            ),
            h("td", null, alert.account_number || ""),
            h("td", null, h("span", { className: riskClass(alert.risk_level) }, labelize(alert.risk_level || "risk"))),
            h("td", null, h("span", { className: "reason-preview", title: alert.reason || "" }, alert.reason || "")),
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
