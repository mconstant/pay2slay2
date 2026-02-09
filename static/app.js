/* Pay2Slay Faucet – MVP UI Logic */
(function () {
  "use strict";

  // ── State ────────────────────────────────────────────
  let user = null;        // { discord_user_id, discord_username, epic_account_id }
  let isAdmin = false;
  let productConfig = null;
  let isDryRun = false;

  // ── DOM refs ─────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ── Init ─────────────────────────────────────────────
  async function init() {
    await loadProductConfig();
    setupNav();
    showPage("login");
  }

  async function loadProductConfig() {
    try {
      const r = await fetch("/config/product");
      if (r.ok) {
        productConfig = await r.json();
        const brand = $(".brand-name");
        if (brand && productConfig.app_name) brand.textContent = productConfig.app_name;
        isDryRun = !!(productConfig.feature_flags && productConfig.feature_flags.dry_run_banner);
        const banner = $(".dry-run-banner");
        if (banner && isDryRun) banner.classList.add("visible");
      }
    } catch (_) { /* config not critical */ }
  }

  // ── Navigation ───────────────────────────────────────
  function setupNav() {
    $$("nav button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const page = btn.dataset.page;
        if (page === "login" || (!user && page !== "login")) return;
        showPage(page);
      });
    });
  }

  function showPage(name) {
    $$(".page").forEach((p) => p.classList.remove("active"));
    const el = $(`#page-${name}`);
    if (el) el.classList.add("active");

    $$("nav button").forEach((b) => b.classList.remove("active"));
    const navBtn = $(`nav button[data-page="${name}"]`);
    if (navBtn) navBtn.classList.add("active");

    // Update nav visibility
    const navEl = $("nav");
    if (navEl) navEl.style.display = user ? "flex" : "none";
    const userInfo = $(".user-info");
    if (userInfo) userInfo.style.display = user ? "flex" : "none";

    // Load data for page
    if (name === "dashboard" && user) loadDashboard();
    if (name === "wallet" && user) loadWallet();
    if (name === "admin" && user) loadAdmin();
  }

  // ── Login ────────────────────────────────────────────
  window.demoLogin = async function () {
    const btn = $("#demo-login-btn");
    btn.disabled = true;
    btn.textContent = "Logging in...";
    try {
      const r = await fetch("/auth/demo-login", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      user = await r.json();
      $(".username").textContent = user.discord_username;
      toast("Logged in as " + user.discord_username, "success");
      showPage("dashboard");
    } catch (e) {
      toast("Login failed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Demo Login (Dry Run)";
    }
  };

  window.logout = function () {
    // Clear the session cookie by making a request (or just clear client state)
    user = null;
    isAdmin = false;
    document.cookie = "p2s_session=; Max-Age=0; path=/";
    document.cookie = "p2s_admin=; Max-Age=0; path=/";
    showPage("login");
  };

  // ── Dashboard ────────────────────────────────────────
  async function loadDashboard() {
    // Load status
    try {
      const r = await fetch("/me/status");
      if (r.ok) {
        const s = await r.json();
        $("#stat-accrued").textContent = parseFloat(s.accrued_rewards_ban || 0).toFixed(2);
        $("#stat-linked").textContent = s.linked ? "Yes" : "No";
        $("#stat-verified").textContent = s.last_verified_status || "none";
        $("#stat-verified-at").textContent = s.last_verified_at
          ? new Date(s.last_verified_at).toLocaleString()
          : "never";
      }
    } catch (_) {}

    // Load recent accruals
    try {
      const r = await fetch("/me/accruals?limit=10");
      if (r.ok) {
        const data = await r.json();
        renderAccruals(data.accruals || []);
      }
    } catch (_) {}

    // Load recent payouts
    try {
      const r = await fetch("/me/payouts?limit=10");
      if (r.ok) {
        const data = await r.json();
        renderPayouts(data.payouts || []);
      }
    } catch (_) {}
  }

  function renderAccruals(rows) {
    const tbody = $("#accruals-tbody");
    if (!tbody) return;
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No accruals yet. Seed demo data or wait for the scheduler.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map((a) => `
      <tr>
        <td>${a.id}</td>
        <td>${a.kills}</td>
        <td>${parseFloat(a.amount_ban).toFixed(2)} BAN</td>
        <td><span class="badge ${a.settled ? "badge-sent" : "badge-pending"}">${a.settled ? "settled" : "pending"}</span></td>
        <td>${a.created_at ? new Date(a.created_at).toLocaleString() : "-"}</td>
      </tr>
    `).join("");
  }

  function renderPayouts(rows) {
    const tbody = $("#payouts-tbody");
    if (!tbody) return;
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No payouts yet.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map((p) => `
      <tr>
        <td>${p.id}</td>
        <td>${parseFloat(p.amount_ban).toFixed(2)} BAN</td>
        <td><span class="badge badge-${p.status}">${p.status}</span></td>
        <td title="${p.tx_hash || ""}">${p.tx_hash ? p.tx_hash.substring(0, 16) + "..." : "-"}</td>
        <td>${p.created_at ? new Date(p.created_at).toLocaleString() : "-"}</td>
      </tr>
    `).join("");
  }

  // ── Wallet ───────────────────────────────────────────
  async function loadWallet() {
    // Show current status
    try {
      const r = await fetch("/me/status");
      if (r.ok) {
        const s = await r.json();
        const status = $("#wallet-status");
        if (status) {
          status.textContent = s.linked ? "Wallet linked" : "No wallet linked";
          status.className = "badge " + (s.linked ? "badge-ok" : "badge-pending");
        }
      }
    } catch (_) {}
  }

  window.linkWallet = async function () {
    const input = $("#wallet-address");
    const addr = input.value.trim();
    if (!addr) { toast("Enter a Banano address", "error"); return; }
    try {
      const r = await fetch("/link/wallet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ banano_address: addr }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ detail: "Failed" }));
        throw new Error(err.detail || "Failed");
      }
      const data = await r.json();
      toast("Wallet linked: " + data.address, "success");
      loadWallet();
      input.value = "";
    } catch (e) {
      toast(e.message, "error");
    }
  };

  // ── Admin ────────────────────────────────────────────
  async function loadAdmin() {
    if (!isAdmin) {
      $("#admin-authed").style.display = "none";
      $("#admin-login-form").style.display = "block";
      return;
    }
    $("#admin-login-form").style.display = "none";
    $("#admin-authed").style.display = "block";
    await Promise.all([loadAdminStats(), loadAdminAudit()]);
  }

  window.adminLogin = async function () {
    const email = $("#admin-email").value.trim();
    if (!email) { toast("Enter admin email", "error"); return; }
    try {
      const r = await fetch("/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!r.ok) throw new Error("Unauthorized");
      isAdmin = true;
      toast("Admin authenticated", "success");
      loadAdmin();
    } catch (e) {
      toast("Admin login failed: " + e.message, "error");
    }
  };

  async function loadAdminStats() {
    try {
      const r = await fetch("/admin/stats");
      if (r.ok) {
        const s = await r.json();
        $("#admin-users").textContent = s.users_total;
        $("#admin-payouts-ban").textContent = parseFloat(s.payouts_sent_ban).toFixed(2);
        $("#admin-accruals-ban").textContent = parseFloat(s.accruals_total_ban).toFixed(2);
        $("#admin-abuse").textContent = s.abuse_flags;
      }
    } catch (_) {}
  }

  async function loadAdminAudit() {
    try {
      const r = await fetch("/admin/audit?limit=20");
      if (r.ok) {
        const data = await r.json();
        const tbody = $("#audit-tbody");
        if (!tbody) return;
        const events = data.events || [];
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No audit events.</td></tr>';
          return;
        }
        tbody.innerHTML = events.map((e) => `
          <tr>
            <td>${e.created_at ? new Date(e.created_at).toLocaleString() : "-"}</td>
            <td>${e.action}</td>
            <td>${e.actor_email || "-"}</td>
            <td>${e.target_type || "-"}</td>
            <td>${e.summary || "-"}</td>
          </tr>
        `).join("");
      }
    } catch (_) {}
  }

  // ── Demo Seed ────────────────────────────────────────
  window.seedDemoData = async function () {
    const btn = $("#seed-btn");
    btn.disabled = true;
    btn.textContent = "Seeding...";
    try {
      const r = await fetch("/demo/seed", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      toast("Seeded: " + data.summary, "success");
      loadDashboard();
    } catch (e) {
      toast("Seed failed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Seed Demo Data";
    }
  };

  // ── Trigger Scheduler ────────────────────────────────
  window.triggerScheduler = async function () {
    const btn = $("#scheduler-btn");
    btn.disabled = true;
    btn.textContent = "Running...";
    try {
      const r = await fetch("/demo/run-scheduler", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      toast("Scheduler: " + data.summary, "success");
      loadDashboard();
    } catch (e) {
      toast("Scheduler failed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Run Scheduler Now";
    }
  };

  // ── Toast ────────────────────────────────────────────
  function toast(msg, type) {
    const el = $(".toast");
    el.textContent = msg;
    el.className = "toast toast-" + type + " visible";
    setTimeout(() => el.classList.remove("visible"), 3000);
  }

  // ── Boot ─────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", init);
})();
