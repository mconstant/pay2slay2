/* Pay2Slay Faucet – UI with hash routing & auto-refresh */
(function () {
  "use strict";

  // ── State ────────────────────────────────────────────
  let user = null;
  let isAdmin = false;
  let productConfig = null;
  let isDryRun = false;
  let refreshTimer = null;
  const REFRESH_INTERVAL = 30000; // 30s auto-refresh

  // ── DOM refs ─────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // Pages that require auth
  const AUTH_PAGES = new Set(["dashboard", "wallet", "admin"]);
  const ALL_PAGES = new Set(["leaderboard", "activity", "donations", "boosted", "dashboard", "wallet", "help", "admin", "login"]);

  // ── Init ─────────────────────────────────────────────
  async function init() {
    await loadProductConfig();
    setupNav();
    await checkExistingSession();
    updateNavVisibility();
    // Route to current hash (or default to leaderboard)
    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    // Start auto-refresh
    startAutoRefresh();
  }

  // ── Hash Routing ────────────────────────────────────
  function handleHashChange() {
    const hash = window.location.hash.replace("#", "") || "activity";
    const page = ALL_PAGES.has(hash) ? hash : "activity";

    if (AUTH_PAGES.has(page) && !user) {
      // Need login — show login page but preserve intended destination
      showPage("login");
      return;
    }
    showPage(page);
  }

  function navigate(page) {
    window.location.hash = page;
  }

  async function checkExistingSession() {
    try {
      const r = await fetch("/me/status");
      if (r.ok) {
        const s = await r.json();
        user = { discord_username: s.discord_username || "You" };
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
        if (!isDryRun) {
          const ids = ["seed-btn", "demo-login-btn", "demo-login-btn-2"];
          ids.forEach(function (id) {
            const el = $("#" + id);
            if (el) el.style.display = "none";
          });
        }
      }
    } catch (_) { /* config not critical */ }
  }

  // ── Navigation ───────────────────────────────────────
  function setupNav() {
    $$("nav button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        navigate(btn.dataset.page);
      });
    });
  }

  function updateNavVisibility() {
    $$("nav button.auth-only").forEach(function (btn) {
      btn.style.display = user ? "" : "none";
    });
    const userInfo = $(".user-info");
    if (userInfo) userInfo.style.display = user ? "flex" : "none";
    // Hide login CTAs on public pages if logged in
    const cta = $("#leaderboard-login-cta");
    if (cta) cta.style.display = user ? "none" : "";
    const actCta = $("#activity-login-cta");
    if (actCta) actCta.style.display = user ? "none" : "";
  }

  function showPage(name) {
    $$(".page").forEach(function (p) { p.classList.remove("active"); });
    const el = $("#page-" + name);
    if (el) el.classList.add("active");

    $$("nav button").forEach(function (b) { b.classList.remove("active"); });
    const navBtn = $('nav button[data-page="' + name + '"]');
    if (navBtn) navBtn.classList.add("active");

    updateNavVisibility();

    // Load data for page
    loadPageData(name);
  }

  function loadPageData(name) {
    if (name === "leaderboard") loadLeaderboard();
    if (name === "activity") loadActivityFeed();
    if (name === "donations") loadDonations();
    if (name === "boosted") loadBoostedUsers();
    if (name === "dashboard" && user) loadDashboard();
    if (name === "wallet" && user) loadWallet();
    if (name === "admin" && user) loadAdmin();
  }

  // ── Auto-refresh ───────────────────────────────────
  function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(function () {
      const hash = window.location.hash.replace("#", "") || "activity";
      const page = ALL_PAGES.has(hash) ? hash : "activity";
      if (page === "login") return;
      loadPageData(page);
    }, REFRESH_INTERVAL);
  }

  // ── Login ────────────────────────────────────────────
  window.discordLogin = function () {
    window.location.href = "/auth/discord/login";
  };

  window.demoLogin = async function () {
    const btn = $("#demo-login-btn") || $("#demo-login-btn-2");
    if (btn) { btn.disabled = true; btn.textContent = "Logging in..."; }
    try {
      const r = await fetch("/auth/demo-login", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      user = await r.json();
      $(".username").textContent = user.discord_username;

      // Auto-seed demo data
      if (btn) btn.textContent = "Setting up demo...";
      try { await fetch("/demo/seed", { method: "POST" }); } catch (_) {}

      toast("Logged in as " + user.discord_username, "success");
      updateNavVisibility();
      navigate("dashboard");
    } catch (e) {
      toast("Login failed: " + e.message, "error");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Demo Login"; }
    }
  };

  window.logout = function () {
    user = null;
    isAdmin = false;
    document.cookie = "p2s_session=; Max-Age=0; path=/";
    document.cookie = "p2s_admin=; Max-Age=0; path=/";
    updateNavVisibility();
    navigate("leaderboard");
  };

  // ── Leaderboard ────────────────────────────────────
  async function loadLeaderboard() {
    try {
      const r = await fetch("/api/leaderboard?limit=50");
      if (r.ok) {
        const data = await r.json();
        renderLeaderboard(data.players || []);
        const countEl = $("#leaderboard-count");
        if (countEl) countEl.textContent = data.total + " players";
      }
    } catch (_) {}
  }

  function renderLeaderboard(rows) {
    const tbody = $("#leaderboard-tbody");
    if (!tbody) return;
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No players yet. Be the first!</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (p, i) {
      var paid = parseFloat(p.total_paid_ban).toFixed(2);
      var owed = parseFloat(p.total_accrued_ban).toFixed(2);
      return '<tr>' +
        '<td class="rank">' + (i + 1) + '</td>' +
        '<td class="player-name">' + escapeHtml(p.discord_username) + '</td>' +
        '<td>' + p.total_kills + '</td>' +
        '<td class="earned-cell"><span class="earned-paid" title="Paid (settled)">' + paid + '</span> <span class="earned-sep">/</span> <span class="earned-owed" title="Owed (accrued)">' + owed + '</span></td>' +
        '</tr>';
    }).join("");
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  /** Parse an ISO timestamp from the API (UTC but missing Z suffix) into local time string. */
  function fmtDate(iso) {
    if (!iso) return "-";
    var d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    return isNaN(d) ? iso : d.toLocaleString();
  }

  /** Compact date: "Jan 5" or "Jan 5 '24" if different year. */
  function shortDate(iso) {
    if (!iso) return "";
    var d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    if (isNaN(d)) return "";
    var mon = d.toLocaleString(undefined, { month: "short" });
    var day = d.getDate();
    var yr = d.getFullYear();
    var now = new Date().getFullYear();
    return yr === now ? mon + " " + day : mon + " " + day + " '" + String(yr).slice(2);
  }

  /** Build tx hash cell: clickable link to creeper + copy icon + optional date. */
  function txHashCell(hash, date) {
    if (!hash) return '<td class="tx-hash">' + (date ? '<span class="cell-date">' + date + '</span>' : '-') + '</td>';
    var short = hash.substring(0, 10) + "\u2026";
    var url = "https://creeper.banano.cc/hash/" + encodeURIComponent(hash);
    return '<td class="tx-hash">' +
      '<a href="' + url + '" target="_blank" rel="noopener" class="tx-link" title="View on Creeper">' + short + '</a>' +
      '<button class="tx-copy" onclick="copyHash(\'' + hash + '\')" title="Copy hash">&#128203;</button>' +
      (date ? ' <span class="cell-date">' + date + '</span>' : '') +
      '</td>';
  }

  /** Copy a tx hash to clipboard and show toast. */
  window.copyHash = function (hash) {
    navigator.clipboard.writeText(hash).then(function () {
      toast("Hash copied!", "success");
    }).catch(function () {
      toast("Copy failed", "error");
    });
  };

  // ── Activity Feed ──────────────────────────────────
  async function loadActivityFeed() {
    try {
      const r = await fetch("/api/feed?limit=30");
      if (r.ok) {
        const data = await r.json();
        renderFeedAccruals(data.accruals || []);
        renderFeedPayouts(data.payouts || []);
      }
    } catch (_) {}
  }

  function renderFeedAccruals(rows) {
    const tbody = $("#feed-accruals-tbody");
    if (!tbody) return;
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No accruals yet.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (a) {
      var statusLabel = a.settled ? "settled" : "pending";
      var statusClass = a.settled ? "badge-sent" : "badge-pending";
      var date = shortDate(a.created_at);
      return '<tr>' +
        '<td class="player-name">' + escapeHtml(a.discord_username) + '</td>' +
        '<td>' + a.kills + '</td>' +
        '<td>' + parseFloat(a.amount_ban).toFixed(2) + ' BAN</td>' +
        '<td><span class="badge ' + statusClass + '">' + statusLabel + '</span>' + (date ? ' <span class="cell-date">' + date + '</span>' : '') + '</td>' +
        '</tr>';
    }).join("");
  }

  function renderFeedPayouts(rows) {
    const tbody = $("#feed-payouts-tbody");
    if (!tbody) return;
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No payouts yet.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (p) {
      var date = shortDate(p.created_at);
      return '<tr>' +
        '<td class="player-name">' + escapeHtml(p.discord_username) + '</td>' +
        '<td>' + parseFloat(p.amount_ban).toFixed(2) + ' BAN</td>' +
        '<td><span class="badge badge-' + p.status + '">' + p.status + '</span></td>' +
        txHashCell(p.tx_hash, date) +
        '</tr>';
    }).join("");
  }

  // ── Donations ────────────────────────────────────────
  async function loadDonations() {
    try {
      var r = await fetch("/api/donations");
      if (!r.ok) return;
      var data = await r.json();

      // Thermometer
      var totalEl = $("#donation-total");
      var pctEl = $("#donation-pct");
      var fillEl = $("#donation-fill");
      if (totalEl) totalEl.textContent = formatBan(data.total_donated);
      if (pctEl) pctEl.textContent = data.progress_pct + "%";
      if (fillEl) fillEl.style.width = Math.min(data.progress_pct, 100) + "%";

      // Current milestone
      var curEl = $("#donation-current-milestone");
      if (curEl && data.current_milestone) {
        var cm = data.current_milestone;
        curEl.innerHTML =
          '<span class="milestone-badge unlocked">' + cm.emoji + " " + cm.name + '</span>' +
          '<span class="milestone-mult">' + cm.payout_multiplier + 'x payout boost active</span>';
      }

      // Next milestone
      var nxtEl = $("#donation-next-milestone");
      if (nxtEl) {
        if (data.next_milestone) {
          var nm = data.next_milestone;
          nxtEl.innerHTML =
            'Next: <strong>' + nm.emoji + " " + nm.name + '</strong> at ' +
            formatBan(nm.threshold) + ' BAN (' + formatBan(nm.remaining) + ' to go)';
        } else {
          nxtEl.innerHTML = '<strong>🎉 All milestones unlocked!</strong>';
        }
      }

      // Milestones list
      var listEl = $("#milestones-list");
      if (listEl && data.milestones) {
        listEl.innerHTML = data.milestones.map(function(m) {
          var cls = m.unlocked ? "milestone-item unlocked" : "milestone-item locked";
          var icon = m.unlocked ? "✅" : "🔒";
          return '<div class="' + cls + '">' +
            '<div class="milestone-left">' +
              '<span class="milestone-emoji">' + m.emoji + '</span>' +
              '<div class="milestone-info">' +
                '<strong>' + m.name + '</strong>' +
                '<span class="milestone-desc">' + m.description + '</span>' +
              '</div>' +
            '</div>' +
            '<div class="milestone-right">' +
              '<span class="milestone-threshold">' + formatBan(m.threshold) + ' BAN</span>' +
              '<span class="milestone-status">' + icon + '</span>' +
            '</div>' +
          '</div>';
        }).join("");
      }

      // Economics transparency
      if (data.economics) {
        var ec = data.economics;
        var effEl = $("#econ-effective-rate");
        var baseEl = $("#econ-base-rate");
        var mileEl = $("#econ-milestone-mult");
        var sustEl = $("#econ-sustainability");
        var donatedEl = $("#econ-donated");
        var paidEl = $("#econ-paid-out");
        var seedEl = $("#econ-seed-fund");
        var dcapEl = $("#econ-daily-cap");
        var wcapEl = $("#econ-weekly-cap");
        var formulaEl = $("#econ-formula");

        if (effEl) effEl.textContent = ec.effective_rate.toFixed(4);
        if (baseEl) baseEl.textContent = ec.base_rate;
        if (mileEl) mileEl.textContent = ec.milestone_multiplier.toFixed(2);
        if (sustEl) {
          sustEl.textContent = ec.sustainability_factor.toFixed(2);
          var sf = ec.sustainability_factor;
          sustEl.className = "econ-value " + (sf >= 1 ? "econ-healthy" : sf >= 0.5 ? "econ-caution" : "econ-critical");
        }
        if (donatedEl) donatedEl.textContent = formatBan(data.total_donated) + " BAN";
        if (paidEl) paidEl.textContent = formatBan(ec.total_paid_out) + " BAN";
        if (seedEl) seedEl.textContent = formatBan(ec.seed_fund) + " BAN";
        if (dcapEl) dcapEl.textContent = ec.daily_cap_ban;
        if (wcapEl) wcapEl.textContent = ec.weekly_cap_ban;
        if (formulaEl) {
          formulaEl.innerHTML =
            '<span class="econ-formula-label">Formula:</span> ' +
            ec.base_rate + ' × ' + ec.milestone_multiplier.toFixed(2) + 'x × ' +
            ec.sustainability_factor.toFixed(2) + 'x = <strong>' +
            ec.effective_rate.toFixed(4) + '</strong> BAN/kill';
        }
      }

      // Donation leaderboard
      var lbEl = $("#donation-leaderboard");
      if (lbEl && data.leaderboard) {
        if (data.leaderboard.length === 0) {
          lbEl.innerHTML = '<div class="empty-state">No donations yet — be the first!</div>';
        } else {
          var rows = data.leaderboard.map(function(d, i) {
            var addr = d.address || "";
            var short = addr.length > 16 ? addr.slice(0, 12) + "…" + addr.slice(-6) : addr;
            var creeperUrl = "https://creeper.banano.cc/account/" + addr;
            var medal = i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : "#" + (i + 1);
            return '<div class="donor-row">' +
              '<span class="donor-rank">' + medal + '</span>' +
              '<a href="' + creeperUrl + '" target="_blank" rel="noopener" class="donor-address" title="' + addr + '">' + short + '</a>' +
              '<span class="donor-amount">' + formatBan(d.total_donated) + ' BAN</span>' +
            '</div>';
          }).join("");
          lbEl.innerHTML = rows;
        }
      }
    } catch (e) {
      console.error("loadDonations error", e);
    }
  }

  function formatBan(n) {
    if (n == null) return "0";
    return Number(n).toLocaleString(undefined, {maximumFractionDigits: 2});
  }

  // ── Boosted Users ────────────────────────────────────
  async function loadBoostedUsers() {
    try {
      var r = await fetch("/hodl/boosted");
      if (!r.ok) return;
      var data = await r.json();
      var countEl = $("#boosted-count");
      if (countEl) countEl.textContent = data.total + " boosted player" + (data.total !== 1 ? "s" : "");
      var tbody = $("#boosted-tbody");
      if (!tbody) return;
      if (!data.boosted_users || data.boosted_users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No boosted players yet — be the first to HODL $JPMT!</td></tr>';
        return;
      }
      tbody.innerHTML = data.boosted_users.map(function (u) {
        return '<tr>' +
          '<td class="player-name">' + u.discord_username + '</td>' +
          '<td>' + u.tier_name + '</td>' +
          '<td style="font-size:1.4em;">' + u.tier_badge + '</td>' +
          '<td>' + formatNumber(u.jpmt_balance) + '</td>' +
          '<td class="boost-mult">' + u.multiplier.toFixed(2) + '×</td>' +
        '</tr>';
      }).join("");
    } catch (e) {
      console.error("loadBoostedUsers error", e);
    }
  }

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
          ? fmtDate(s.last_verified_at)
          : "never";
        // Update username if we get it from the status response
        if (s.discord_username && user) {
          user.discord_username = s.discord_username;
          $(".username").textContent = s.discord_username;
        }
        var discordEl = $("#stat-discord-id");
        if (discordEl) discordEl.textContent = s.discord_username || "—";

        // HODL boost status
        var hodlBal = $("#hodl-balance");
        var hodlTier = $("#hodl-tier");
        var hodlMult = $("#hodl-multiplier");
        var hodlVerified = $("#hodl-verified");
        var hodlBadge = $("#hodl-badge");
        if (hodlBal) hodlBal.textContent = s.jpmt_balance ? formatNumber(s.jpmt_balance) : "—";
        if (hodlTier) hodlTier.textContent = s.jpmt_tier || "—";
        if (hodlMult) {
          hodlMult.textContent = (s.jpmt_multiplier || 1.0).toFixed(2) + "x";
          hodlMult.style.color = s.jpmt_multiplier > 1 ? "var(--success)" : "var(--text-muted)";
        }
        if (hodlVerified) hodlVerified.textContent = s.jpmt_verified_at ? fmtDate(s.jpmt_verified_at) : "never";
        if (hodlBadge) {
          hodlBadge.textContent = s.jpmt_badge || "";
          hodlBadge.title = s.jpmt_tier || "";
        }
        // Show connected wallet address if already linked
        if (s.solana_wallet) {
          var short = s.solana_wallet.slice(0, 6) + "…" + s.solana_wallet.slice(-4);
          var statusEl = $("#sol-wallet-status");
          var displayEl = $("#sol-wallet-display");
          var connectBtn = $("#sol-connect-btn");
          var verifyBtn = $("#sol-verify-btn");
          if (statusEl) statusEl.style.display = "flex";
          if (displayEl) displayEl.textContent = short + " (linked)";
          if (connectBtn) connectBtn.textContent = "🔄 Reconnect Wallet";
          if (verifyBtn) verifyBtn.style.display = "";
        }
      }
    } catch (_) {}
  }

  function formatNumber(n) {
    if (n >= 1000000000) return (n / 1000000000).toFixed(1) + "B";
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 1000) return (n / 1000).toFixed(1) + "K";
    return String(n);
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
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No accruals yet.' + hint + '</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (a) {
      var statusLabel = a.settled ? "settled" : "pending";
      var statusClass = a.settled ? "badge-sent" : "badge-pending";
      var date = shortDate(a.created_at);
      return '<tr>' +
        '<td>' + a.id + '</td>' +
        '<td>' + a.kills + '</td>' +
        '<td>' + parseFloat(a.amount_ban).toFixed(2) + ' BAN</td>' +
        '<td><span class="badge ' + statusClass + '">' + statusLabel + '</span>' + (date ? ' <span class="cell-date">' + date + '</span>' : '') + '</td>' +
        '</tr>';
    }).join("");
  }

  function renderPayouts(rows) {
    const tbody = $("#payouts-tbody");
    if (!tbody) return;
    if (rows.length === 0) {
      const hint = isDryRun ? ' Run the scheduler to settle pending accruals.' : '';
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No payouts yet.' + hint + '</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (p) {
      var date = shortDate(p.created_at);
      return '<tr>' +
        '<td>' + p.id + '</td>' +
        '<td>' + parseFloat(p.amount_ban).toFixed(2) + ' BAN</td>' +
        '<td><span class="badge badge-' + p.status + '">' + p.status + '</span></td>' +
        txHashCell(p.tx_hash, date) +
        '</tr>';
    }).join("");
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
        const err = await r.json().catch(function () { return { detail: "Failed" }; });
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

  // ── Solana Wallet ─────────────────────────────────────
  var _solanaProvider = null;
  var _solanaPublicKey = null;

  function _isMobile() {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  }

  function _getSolanaProvider() {
    if (window.phantom && window.phantom.solana && window.phantom.solana.isPhantom) {
      return window.phantom.solana;
    }
    if (window.solflare && window.solflare.isSolflare) {
      return window.solflare;
    }
    if (window.solana) {
      return window.solana;
    }
    return null;
  }

  window.connectSolanaWallet = async function () {
    var provider = _getSolanaProvider();
    if (!provider) {
      if (_isMobile()) {
        // On mobile without injected provider, show wallet picker
        var picker = $("#sol-mobile-picker");
        if (picker) {
          picker.style.display = picker.style.display === "flex" ? "none" : "flex";
        }
        return;
      }
      toast("No Solana wallet found. Install Phantom or Solflare.", "error");
      window.open("https://phantom.app/", "_blank");
      return;
    }
    try {
      var resp = await provider.connect();
      _solanaProvider = provider;
      _solanaPublicKey = resp.publicKey.toString();
      var short = _solanaPublicKey.slice(0, 6) + "…" + _solanaPublicKey.slice(-4);
      var statusEl = $("#sol-wallet-status");
      var displayEl = $("#sol-wallet-display");
      var connectBtn = $("#sol-connect-btn");
      var verifyBtn = $("#sol-verify-btn");
      if (statusEl) statusEl.style.display = "flex";
      if (displayEl) displayEl.textContent = short;
      if (connectBtn) connectBtn.style.display = "none";
      if (verifyBtn) verifyBtn.style.display = "";
      toast("Wallet connected: " + short, "success");
    } catch (e) {
      toast("Wallet connection cancelled", "error");
    }
  };

  window.verifySolanaWallet = async function () {
    if (!_solanaProvider || !_solanaPublicKey) {
      toast("Connect your Solana wallet first", "error");
      return;
    }
    try {
      // Build challenge message
      var ts = Math.floor(Date.now() / 1000);
      var message = "Verify wallet ownership for Pay2Slay\nWallet: " + _solanaPublicKey + "\nTimestamp: " + ts;
      var encodedMessage = new TextEncoder().encode(message);

      // Request signature from wallet
      var signResult = await _solanaProvider.signMessage(encodedMessage, "utf8");
      var sigBytes = signResult.signature || signResult;
      // Convert signature to base64
      var sigB64 = btoa(String.fromCharCode.apply(null, new Uint8Array(sigBytes)));

      // Send to backend
      var r = await fetch("/me/verify-solana", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          solana_address: _solanaPublicKey,
          signature: sigB64,
          message: message,
        }),
      });
      if (!r.ok) {
        var err = await r.json().catch(function () { return { detail: "Failed" }; });
        throw new Error(err.detail || "Verification failed");
      }
      var data = await r.json();
      toast(
        data.jpmt_balance > 0
          ? data.tier + " — " + data.multiplier.toFixed(2) + "x boost! (" + formatNumber(data.jpmt_balance) + " $JPMT)"
          : "Wallet verified but no $JPMT found",
        data.jpmt_balance > 0 ? "success" : "info"
      );
      loadStatus();
    } catch (e) {
      toast(e.message || "Signature rejected", "error");
    }
  };

  window.openInPhantom = function () {
    var url = encodeURIComponent(window.location.href);
    window.location.href = "https://phantom.app/ul/browse/" + url;
  };

  window.copyPageUrl = function () {
    navigator.clipboard.writeText(window.location.href).then(function () {
      toast("URL copied! Open your wallet app and paste in its browser.", "success");
    }).catch(function () {
      // Fallback for older browsers
      var ta = document.createElement("textarea");
      ta.value = window.location.href;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      toast("URL copied! Open your wallet app and paste in its browser.", "success");
    });
  };

  // ── Admin ────────────────────────────────────────────
  async function loadAdmin() {
    if (!isAdmin) {
      try {
        const r = await fetch("/admin/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        if (r.ok) isAdmin = true;
      } catch (_) {}
    }

    if (!isAdmin) {
      $("#admin-authed").style.display = "none";
      $("#admin-unauthorized").style.display = "block";
      return;
    }
    $("#admin-unauthorized").style.display = "none";
    $("#admin-authed").style.display = "block";
    await Promise.all([loadAdminStats(), loadAdminAudit(), loadSchedulerStatus(), loadSchedulerConfig(), loadPayoutConfig()]);
  }

  async function loadAdminStats() {
    try {
      const r = await fetch("/admin/stats");
      if (r.ok) {
        const s = await r.json();
        $("#admin-users").textContent = s.users_total;
        $("#admin-payouts-ban").textContent = parseFloat(s.payouts_sent_ban).toFixed(2);
        $("#admin-payouts-pending").textContent = parseFloat(s.payouts_pending_ban || 0).toFixed(2);
        $("#admin-accruals-ban").textContent = parseFloat(s.accruals_total_ban).toFixed(2);
        $("#admin-accruals-pending").textContent = parseFloat(s.accruals_pending_ban || 0).toFixed(2);
        $("#admin-abuse").textContent = s.abuse_flags;

        if (s.operator_balance_ban !== null) {
          $("#admin-operator-balance").textContent = parseFloat(s.operator_balance_ban).toFixed(2);
        } else {
          $("#admin-operator-balance").textContent = "\u2014";
        }
        if (s.operator_pending_ban !== null) {
          $("#admin-operator-pending").textContent = parseFloat(s.operator_pending_ban).toFixed(2);
        } else {
          $("#admin-operator-pending").textContent = "\u2014";
        }
        if (s.operator_account) {
          $("#admin-operator-account").textContent = s.operator_account;
        }

        $("#admin-scheduler").textContent = s.scheduler_minutes || "\u2014";

        const dryRunEl = $("#admin-dry-run-status");
        if (dryRunEl) {
          if (s.dry_run) {
            dryRunEl.innerHTML = '<span class="badge badge-pending">DRY RUN MODE</span> No real transactions';
          } else {
            dryRunEl.innerHTML = '<span class="badge badge-sent">LIVE MODE</span> Real Banano transactions';
          }
        }
      }
    } catch (_) {}

    await loadOperatorSeedStatus();
  }

  async function loadSchedulerStatus() {
    const el = $("#admin-scheduler-status");
    if (!el) return;
    try {
      const r = await fetch("/admin/scheduler/status");
      if (r.ok) {
        const d = await r.json();
        if (d.alive) {
          const ago = Math.round(d.last_heartbeat_ago_sec);
          el.innerHTML = '<span class="badge badge-sent">alive</span> Last heartbeat ' + ago + 's ago';
        } else {
          el.innerHTML = '<span class="badge badge-failed">dead</span> ' + (d.error || d.detail || "not running");
        }
      }
    } catch (_) {
      el.innerHTML = '<span class="badge badge-pending">unknown</span>';
    }
  }

  async function loadSchedulerConfig() {
    try {
      const r = await fetch("/admin/scheduler/config");
      if (r.ok) {
        const d = await r.json();
        var ai = $("#accrual-interval-input");
        var si = $("#settlement-interval-input");
        if (ai) ai.value = d.accrual_interval_seconds;
        if (si) si.value = d.settlement_interval_seconds;
      }
    } catch (_) {}
  }

  window.saveSchedulerConfig = async function () {
    var ai = $("#accrual-interval-input");
    var si = $("#settlement-interval-input");
    var body = {};
    if (ai && ai.value) body.accrual_interval_seconds = parseInt(ai.value, 10);
    if (si && si.value) body.settlement_interval_seconds = parseInt(si.value, 10);
    try {
      var r = await fetch("/admin/scheduler/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      var d = await r.json();
      toast("Intervals updated: accrual=" + d.accrual_interval_seconds + "s, settlement=" + d.settlement_interval_seconds + "s", "success");
      fetchCountdown();
    } catch (e) {
      toast("Failed: " + e.message, "error");
    }
  };

  async function loadPayoutConfig() {
    try {
      const r = await fetch("/admin/payout/config");
      if (r.ok) {
        const d = await r.json();
        var bpk = $("#payout-ban-per-kill");
        var dc = $("#payout-daily-cap");
        var wc = $("#payout-weekly-cap");
        if (bpk) bpk.value = d.ban_per_kill;
        if (dc) dc.value = d.daily_kill_cap;
        if (wc) wc.value = d.weekly_kill_cap;
        var hint = $("#payout-override-hint");
        if (hint && d.has_overrides) {
          hint.innerHTML = '<span class="badge badge-pending">overridden</span> Runtime overrides active. Changes take effect on the next scheduler cycle.';
        }
      }
    } catch (_) {}
  }

  window.savePayoutConfig = async function () {
    var bpk = $("#payout-ban-per-kill");
    var dc = $("#payout-daily-cap");
    var wc = $("#payout-weekly-cap");
    var body = {};
    if (bpk && bpk.value) body.ban_per_kill = parseFloat(bpk.value);
    if (dc && dc.value) body.daily_kill_cap = parseInt(dc.value, 10);
    if (wc && wc.value) body.weekly_kill_cap = parseInt(wc.value, 10);
    try {
      var r = await fetch("/admin/payout/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      toast("Payout config updated", "success");
      await loadPayoutConfig();
    } catch (e) {
      toast("Failed: " + e.message, "error");
    }
  };

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
          const date = data.updated_at ? fmtDate(data.updated_at) : "unknown";
          statusEl.innerHTML = '<span class="badge badge-sent">Configured</span> Last updated: ' + date + ' by ' + escapeHtml(data.set_by || "unknown");
          if (addressEl && data.address) {
            addressEl.innerHTML = '<strong>Derived Address:</strong><br><code style="font-size:11px;word-break:break-all;">' + escapeHtml(data.address) + '</code>';
            addressEl.style.display = "block";
            if (qrContainerEl && qrCanvasEl && typeof qrcode !== "undefined") {
              qrCanvasEl.innerHTML = "";
              const qr = qrcode(0, "M");
              qr.addData(data.address);
              qr.make();
              qrCanvasEl.innerHTML = qr.createSvgTag(5, 0);
              qrContainerEl.style.display = "block";
            }
            const accountEl = $("#admin-operator-account");
            if (accountEl) accountEl.textContent = data.address;
          }
        } else {
          statusEl.innerHTML = '<span class="badge badge-pending">Not configured</span> Set a seed to enable payouts';
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
    if (!seed) { toast("Enter a wallet seed", "error"); return; }
    if (!/^[0-9a-fA-F]{64}$/.test(seed)) {
      toast("Seed must be 64 hexadecimal characters", "error"); return;
    }
    if (!confirm("Save this operator seed? This will encrypt and store it securely.")) return;
    const btn = $("#save-seed-btn");
    btn.disabled = true;
    btn.textContent = "Saving...";
    try {
      const r = await fetch("/admin/config/operator-seed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed: seed }),
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
        tbody.innerHTML = events.map(function (e) {
          return '<tr>' +
            '<td>' + (e.created_at ? fmtDate(e.created_at) : "-") + '</td>' +
            '<td><span class="badge badge-ok">' + escapeHtml(e.action) + '</span></td>' +
            '<td>' + escapeHtml(e.actor_email || "-") + '</td>' +
            '<td>' + escapeHtml(e.target_type || "-") + '</td>' +
            '<td>' + escapeHtml(e.summary || "-") + '</td>' +
            '</tr>';
        }).join("");
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
        toast("Cleared: " + data.users + " users, " + data.accruals + " accruals, " + data.payouts + " payouts", "success");
      } else {
        toast(data.message || "No demo data to clear", "info");
      }
      loadAdminStats();
    } catch (e) {
      toast("Clear failed: " + e.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Clear Demo Data";
    }
  };

  // ── Trigger Scheduler ────────────────────────────────
  window.triggerScheduler = async function () {
    const btn = $("#scheduler-btn") || document.querySelector('[onclick="triggerScheduler()"]');
    if (btn) { btn.disabled = true; btn.textContent = "Running..."; }
    try {
      var r = await fetch("/admin/scheduler/trigger", { method: "POST" });
      if (r.status === 401) {
        // Not admin — try demo endpoint only if dry-run mode
        if (isDryRun) {
          r = await fetch("/demo/run-scheduler", { method: "POST" });
        } else {
          throw new Error("Admin access required");
        }
      }
      if (!r.ok) throw new Error(await r.text());
      var data = await r.json();
      toast("Scheduler: " + (data.summary || data.detail), "success");
      loadPageData(window.location.hash.replace("#", "") || "activity");
    } catch (e) {
      toast("Scheduler failed: " + e.message, "error");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Run Scheduler Now"; }
    }
  };

  // ── Trigger Settlement ─────────────────────────────
  window.triggerSettlement = async function () {
    const btn = document.querySelector('[onclick="triggerSettlement()"]');
    if (btn) { btn.disabled = true; btn.textContent = "Settling..."; }
    try {
      const r = await fetch("/admin/scheduler/settle", { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      toast("Settlement: " + data.candidates + " candidates, " + data.payouts + " payouts, " + data.accruals_settled + " settled", "success");
      loadPageData("admin");
    } catch (e) {
      toast("Settlement failed: " + e.message, "error");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Settle Payouts"; }
    }
  };

  // ── Toast ────────────────────────────────────────────
  function toast(msg, type) {
    const el = $(".toast");
    el.textContent = msg;
    el.className = "toast toast-" + type + " visible";
    setTimeout(function () { el.classList.remove("visible"); }, 3000);
  }

  // ── Cycle Countdown ─────────────────────────────────
  let accrualRemaining = null;
  let settlementRemaining = null;
  let countdownTimer = null;

  async function fetchCountdown() {
    try {
      const r = await fetch("/api/scheduler/countdown");
      if (r.ok) {
        const d = await r.json();
        if (d.next_accrual_in !== null) accrualRemaining = d.next_accrual_in;
        if (d.next_settlement_in !== null) settlementRemaining = d.next_settlement_in;
        if (!countdownTimer) {
          countdownTimer = setInterval(tickCountdown, 1000);
        }
        renderCountdown();
      }
    } catch (_) {}
  }

  function tickCountdown() {
    if (accrualRemaining !== null) accrualRemaining = Math.max(0, accrualRemaining - 1);
    if (settlementRemaining !== null) settlementRemaining = Math.max(0, settlementRemaining - 1);
    renderCountdown();
    if ((accrualRemaining !== null && accrualRemaining <= 0) ||
        (settlementRemaining !== null && settlementRemaining <= 0)) {
      setTimeout(fetchCountdown, 5000);
    }
  }

  function fmtTime(sec) {
    if (sec === null) return "--:--";
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    return m + ":" + (s < 10 ? "0" : "") + s;
  }

  function renderCountdown() {
    var a = $("#cycle-countdown-accrual");
    var s = $("#cycle-countdown-settlement");
    if (a) a.textContent = "Accrual: " + fmtTime(accrualRemaining);
    if (s) s.textContent = "Settlement: " + fmtTime(settlementRemaining);
  }

  // ── Donate Info ─────────────────────────────────────
  async function fetchDonateInfo() {
    try {
      var r = await fetch("/api/donate-info");
      if (!r.ok) return;
      var d = await r.json();
      if (!d.address) return;
      var bar = $("#donate-bar");
      if (!bar) return;
      bar.style.display = "block";
      var addrEl = $("#donate-address");
      if (addrEl) addrEl.textContent = d.address;
      var balEl = $("#donate-balance-value");
      if (balEl && d.balance !== null) balEl.textContent = parseFloat(d.balance).toFixed(2);
      // Render QR code
      var qrEl = $("#donate-qr");
      if (qrEl && typeof qrcode !== "undefined") {
        var qr = qrcode(0, "M");
        qr.addData(d.address);
        qr.make();
        qrEl.innerHTML = qr.createSvgTag(3, 0);
      }
    } catch (_) {}
  }

  /** Copy the donate address to clipboard. */
  window.copyDonateAddress = function () {
    var addrEl = $("#donate-address");
    if (!addrEl || !addrEl.textContent) { toast("No address available", "error"); return; }
    navigator.clipboard.writeText(addrEl.textContent).then(function () {
      toast("Donate address copied!", "success");
    }).catch(function () {
      toast("Copy failed", "error");
    });
  };

  // ── Boot ─────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", function () {
    init();
    fetchCountdown();
    fetchDonateInfo();
    // Re-sync countdown from server every 60s
    setInterval(fetchCountdown, 60000);
    // Re-sync donate info every 5 minutes
    setInterval(fetchDonateInfo, 300000);
  });
})();
