/* Pay2Slay Faucet – MVP UI Logic */
(function () {
  "use strict";

  // ── State ────────────────────────────────────────────
  let user = null;        // { discord_user_id, discord_username, epic_account_id }
  let isAdmin = false;
  let productConfig = null;
  let isDryRun = false;
  let schedulerIntervalMinutes = 20; // Default from configs/payout.yaml
  let countdownStartTime = Date.now(); // Track when countdown started

  // ── DOM refs ─────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ── Init ─────────────────────────────────────────────
  async function init() {
    await loadProductConfig();
    setupNav();

    // Check if user already has a session (e.g., returning from OAuth redirect)
    const hasSession = await checkExistingSession();
    if (hasSession) {
      showPage("dashboard");
    } else {
      showPage("login");
    }
  }

  async function checkExistingSession() {
    try {
      const r = await fetch("/me/status");
      if (r.ok) {
        // Session cookie is valid — user is logged in
        user = { discord_username: "You" };
        $(".username").textContent = user.discord_username;
        return true;
      }
    } catch (_) {}
    return false;
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
        // Hide demo-only elements when not in dry run mode
        const seedBtn = $("#seed-btn");
        const schedulerBtn = $("#scheduler-btn");
        const demoLoginBtn = $("#demo-login-btn");
        if (!isDryRun) {
          if (seedBtn) seedBtn.style.display = "none";
          if (schedulerBtn) schedulerBtn.style.display = "none";
          if (demoLoginBtn) demoLoginBtn.style.display = "none";
        }
      }
    } catch (_) { /* config not critical */ }
    
    // Load payout config for scheduler timing
    try {
      const r = await fetch("/config/payout");
      if (r.ok) {
        const payoutConfig = await r.json();
        if (payoutConfig.scheduler_minutes) {
          schedulerIntervalMinutes = payoutConfig.scheduler_minutes;
        }
      }
    } catch (_) { /* payout config not critical */ }
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
    
    // Show/hide footer based on user login
    const footer = $("#app-footer");
    if (footer) footer.style.display = user ? "block" : "none";

    // Load data for page
    if (name === "dashboard" && user) loadDashboard();
    if (name === "wallet" && user) loadWallet();
    if (name === "admin" && user) loadAdmin();
  }

  // ── Login ────────────────────────────────────────────
  window.discordLogin = function () {
    // Redirect to server-side Discord OAuth flow
    window.location.href = "/auth/discord/login";
  };

  window.demoLogin = async function () {
    const btn = $("#demo-login-btn");
    btn.disabled = true;
    btn.textContent = "Logging in...";
    try {
      const r = await fetch("/auth/demo-login", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      user = await r.json();
      $(".username").textContent = user.discord_username;

      // Auto-seed demo data so dashboard isn't empty on first visit
      btn.textContent = "Setting up demo...";
      try {
        await fetch("/demo/seed", { method: "POST" });
      } catch (_) { /* non-critical */ }

      toast("Logged in as " + user.discord_username, "success");
      showPage("dashboard");
    } catch (e) {
      toast("Login failed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Demo Login";
    }
  };

  window.logout = function () {
    user = null;
    isAdmin = false;
    document.cookie = "p2s_session=; Max-Age=0; path=/";
    document.cookie = "p2s_admin=; Max-Age=0; path=/";
    showPage("login");
  };

  // ── Dashboard ────────────────────────────────────────
  async function loadDashboard() {
    await Promise.all([loadStatus(), loadAccruals(), loadPayouts()]);
  }

  async function loadStatus() {
    try {
      const r = await fetch("/me/status");
      if (r.ok) {
        const s = await r.json();
        $("#stat-accrued").textContent = parseFloat(s.accrued_rewards_ban || 0).toFixed(2);
        const linkedEl = $("#stat-linked");
        linkedEl.textContent = s.linked ? "Yes" : "No";
        linkedEl.style.color = s.linked ? "var(--success)" : "var(--text-muted)";
        $("#stat-verified").textContent = s.last_verified_status || "none";
        $("#stat-verified-at").textContent = s.last_verified_at
          ? new Date(s.last_verified_at).toLocaleString()
          : "never";
      }
    } catch (_) {}
  }

  async function loadAccruals() {
    try {
      const r = await fetch("/me/accruals?limit=10");
      if (r.ok) {
        const data = await r.json();
        renderAccruals(data.accruals || []);
      }
    } catch (_) {}
  }

  async function loadPayouts() {
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
      const hint = isDryRun ? ' Click "Seed Demo Data" to generate sample data.' : '';
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No accruals yet.${hint}</td></tr>`;
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
      const hint = isDryRun ? ' Run the scheduler to settle pending accruals.' : '';
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No payouts yet.${hint}</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((p) => `
      <tr>
        <td>${p.id}</td>
        <td>${parseFloat(p.amount_ban).toFixed(2)} BAN</td>
        <td><span class="badge badge-${p.status}">${p.status}</span></td>
        <td class="tx-hash" title="${p.tx_hash || ""}">${p.tx_hash ? p.tx_hash.substring(0, 12) + "..." : "-"}</td>
        <td>${p.created_at ? new Date(p.created_at).toLocaleString() : "-"}</td>
      </tr>
    `).join("");
  }

  // ── Wallet ───────────────────────────────────────────
  async function loadWallet() {
    try {
      const r = await fetch("/me/status");
      if (r.ok) {
        const s = await r.json();
        const status = $("#wallet-status");
        const linkedCard = $("#wallet-linked-card");
        const linkedAddr = $("#wallet-linked-address");
        const formTitle = $("#wallet-form-title");
        
        if (status) {
          status.textContent = s.linked ? "Linked" : "Not linked";
          status.className = "badge " + (s.linked ? "badge-ok" : "badge-pending");
        }
        
        if (s.linked && s.wallet_address) {
          if (linkedCard) linkedCard.style.display = "block";
          if (linkedAddr) linkedAddr.textContent = s.wallet_address;
          if (formTitle) formTitle.textContent = "Update Wallet";
        } else {
          if (linkedCard) linkedCard.style.display = "none";
          if (formTitle) formTitle.textContent = "Link Banano Wallet";
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
    // Try to authenticate via Discord username (server checks ADMIN_DISCORD_USERNAMES)
    if (!isAdmin) {
      try {
        const r = await fetch("/admin/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        if (r.ok) {
          isAdmin = true;
        }
      } catch (_) {}
    }

    if (!isAdmin) {
      $("#admin-authed").style.display = "none";
      $("#admin-unauthorized").style.display = "block";
      return;
    }
    $("#admin-unauthorized").style.display = "none";
    $("#admin-authed").style.display = "block";
    await Promise.all([loadAdminStats(), loadAdminAudit()]);
  }

  async function loadAdminStats() {
    try {
      const r = await fetch("/admin/stats");
      if (r.ok) {
        const s = await r.json();
        // System stats
        $("#admin-users").textContent = s.users_total;
        $("#admin-payouts-ban").textContent = parseFloat(s.payouts_sent_ban).toFixed(2);
        $("#admin-payouts-pending").textContent = parseFloat(s.payouts_pending_ban || 0).toFixed(2);
        $("#admin-accruals-ban").textContent = parseFloat(s.accruals_total_ban).toFixed(2);
        $("#admin-accruals-pending").textContent = parseFloat(s.accruals_pending_ban || 0).toFixed(2);
        $("#admin-abuse").textContent = s.abuse_flags;

        // Operator wallet
        if (s.operator_balance_ban !== null) {
          $("#admin-operator-balance").textContent = parseFloat(s.operator_balance_ban).toFixed(2);
        } else {
          $("#admin-operator-balance").textContent = "—";
        }
        if (s.operator_pending_ban !== null) {
          $("#admin-operator-pending").textContent = parseFloat(s.operator_pending_ban).toFixed(2);
        } else {
          $("#admin-operator-pending").textContent = "—";
        }
        if (s.operator_account) {
          $("#admin-operator-account").textContent = s.operator_account;
        }

        // Payout config
        $("#admin-ban-per-kill").textContent = parseFloat(s.ban_per_kill || 0).toFixed(2);
        $("#admin-daily-cap").textContent = s.daily_payout_cap || "—";
        $("#admin-weekly-cap").textContent = s.weekly_payout_cap || "—";
        $("#admin-scheduler").textContent = s.scheduler_minutes || "—";

        // Dry run status
        const dryRunEl = $("#admin-dry-run-status");
        if (dryRunEl) {
          if (s.dry_run) {
            dryRunEl.innerHTML = '<span class="badge badge-pending">🧪 DRY RUN MODE</span> No real transactions';
          } else {
            dryRunEl.innerHTML = '<span class="badge badge-sent">🚀 LIVE MODE</span> Real Banano transactions';
          }
        }
      }
    } catch (_) {}

    // Load operator seed status
    await loadOperatorSeedStatus();
  }

  async function loadOperatorSeedStatus() {
    const statusEl = $("#operator-seed-status");
    const addressEl = $("#operator-seed-address");
    const qrContainerEl = $("#operator-qr-code");
    const qrCanvasEl = $("#operator-qr-canvas");
    if (!statusEl) return;
    try {
      const r = await fetch("/admin/config/operator-seed/status");
      if (r.ok) {
        const data = await r.json();
        if (data.configured) {
          const date = data.updated_at ? new Date(data.updated_at).toLocaleDateString() : "unknown";
          statusEl.innerHTML = `<span class="badge badge-sent">✓ Configured</span> Last updated: ${date} by ${data.set_by || "unknown"}`;
          // Show derived address
          if (addressEl && data.address) {
            addressEl.innerHTML = `<strong>Derived Address:</strong><br><code style="font-size:11px;word-break:break-all;">${data.address}</code>`;
            addressEl.style.display = "block";
            // Generate QR code for the address
            if (qrContainerEl && qrCanvasEl && typeof qrcode !== "undefined") {
              qrCanvasEl.innerHTML = "";
              const qr = qrcode(0, "M");
              qr.addData(data.address);
              qr.make();
              qrCanvasEl.innerHTML = qr.createSvgTag(5, 0);
              qrContainerEl.style.display = "block";
            }
            // Update the operator wallet display to use this address
            const balanceEl = $("#admin-operator-balance");
            const accountEl = $("#admin-operator-account");
            if (accountEl) {
              accountEl.textContent = data.address;
            }
          }
        } else {
          statusEl.innerHTML = '<span class="badge badge-pending">⚠ Not configured</span> Set a seed to enable payouts';
          if (addressEl) addressEl.style.display = "none";
          if (qrContainerEl) qrContainerEl.style.display = "none";
        }
      }
    } catch (_) {
      statusEl.textContent = "Unable to check status";
    }
  }

  window.saveOperatorSeed = async function () {
    const input = $("#operator-seed-input");
    const seed = input.value.trim();
    if (!seed) {
      toast("Enter a wallet seed", "error");
      return;
    }
    if (!/^[0-9a-fA-F]{64}$/.test(seed)) {
      toast("Seed must be 64 hexadecimal characters", "error");
      return;
    }
    if (!confirm("Save this operator seed? This will encrypt and store it securely.")) {
      return;
    }
    const btn = $("#save-seed-btn");
    btn.disabled = true;
    btn.textContent = "Saving...";
    try {
      const r = await fetch("/admin/config/operator-seed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed }),
      });
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.detail || "Failed to save");
      }
      toast("Operator seed saved securely", "success");
      input.value = "";
      await loadOperatorSeedStatus();
    } catch (e) {
      toast("Failed to save seed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Save Seed Securely";
    }
  };

  async function loadAdminAudit() {
    try {
      const r = await fetch("/admin/audit?limit=20");
      if (r.ok) {
        const data = await r.json();
        const tbody = $("#audit-tbody");
        if (!tbody) return;
        const events = data.events || [];
        if (events.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No audit events yet.</td></tr>';
          return;
        }
        tbody.innerHTML = events.map((e) => `
          <tr>
            <td>${e.created_at ? new Date(e.created_at).toLocaleString() : "-"}</td>
            <td><span class="badge badge-ok">${e.action}</span></td>
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

  // ── Clear Demo Data ──────────────────────────────────
  window.clearDemoData = async function () {
    if (!confirm("Clear all demo users and their data? This cannot be undone.")) return;
    const btn = $("#clear-demo-btn");
    btn.disabled = true;
    btn.textContent = "Clearing...";
    try {
      const r = await fetch("/demo/clear", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      if (data.cleared) {
        toast(`Cleared: ${data.users} users, ${data.accruals} accruals, ${data.payouts} payouts`, "success");
      } else {
        toast(data.message || "No demo data to clear", "info");
      }
      loadAdminStats();
    } catch (e) {
      toast("Clear failed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "🗑️ Clear Demo Data";
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

  // ── Countdown Timers ─────────────────────────────────
  function updateCountdowns() {
    const now = Date.now();
    const intervalMs = schedulerIntervalMinutes * 60 * 1000;
    
    // Calculate time elapsed since countdown started
    const elapsed = now - countdownStartTime;
    // Calculate time until next run (cycles through the interval)
    const msUntilNext = intervalMs - (elapsed % intervalMs);
    
    // Format time as HH:MM:SS
    const formatTime = (ms) => {
      const totalSec = Math.floor(ms / 1000);
      const hours = Math.floor(totalSec / 3600);
      const minutes = Math.floor((totalSec % 3600) / 60);
      const seconds = totalSec % 60;
      return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    };
    
    const accrualEl = $("#countdown-accrual");
    const settlementEl = $("#countdown-settlement");
    
    // Both accrual and settlement run together in the same scheduler cycle
    if (accrualEl) accrualEl.textContent = formatTime(msUntilNext);
    if (settlementEl) settlementEl.textContent = formatTime(msUntilNext);
  }
  
  function startCountdownTimers() {
    // Update immediately
    updateCountdowns();
    // Then update every second
    setInterval(updateCountdowns, 1000);
  }

  // ── Boot ─────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    init();
    startCountdownTimers();
  });
})();
