// =============================
// Helpers
// =============================
function safeNumber(val) {
    return val === null || val === undefined ? "-" : val;
}

function escapeHtml(str) {
    return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function toFixedOrDash(v, digits = 2) {
    if (v === null || v === undefined || v === "") return "-";
    const n = Number(v);
    if (Number.isNaN(n)) return "-";
    return n.toFixed(digits);
}

// =============================
// Table mode state
// =============================
let isTableMode = false;

const tableState = {
    page: 1,
    per_page: 200,
    total: 0,
    lastQuery: "" // team_id, year, h_a, result
};

function buildQueryFromFilters() {
    const t = document.getElementById("filterTeam")?.value || "";
    const y = document.getElementById("filterYear")?.value || "";
    const ha = document.getElementById("filterHA")?.value || "";
    const r = document.getElementById("filterResult")?.value || "";

    const params = [];
    if (t) params.push(`team_id=${encodeURIComponent(t)}`);
    if (y) params.push(`year=${encodeURIComponent(y)}`);
    if (ha) params.push(`h_a=${encodeURIComponent(ha)}`);
    if (r) params.push(`result=${encodeURIComponent(r)}`);

    return params.length ? params.join("&") : "";
}

function updatePagerUI() {
    const pageInfo = document.getElementById("tblPageInfo");
    const prevBtn = document.getElementById("tblPrev");
    const nextBtn = document.getElementById("tblNext");

    const totalPages = Math.max(1, Math.ceil((tableState.total || 0) / tableState.per_page));

    if (pageInfo) pageInfo.textContent = `Page ${tableState.page} / ${totalPages}`;
    if (prevBtn) prevBtn.disabled = tableState.page <= 1;
    if (nextBtn) nextBtn.disabled = tableState.page >= totalPages;
}

// =============================
// Dropdown filling
// =============================
async function loadTeamsForFilter() {
    try {
        const res = await fetch("/api/teams?per_page=5000"); // <-- kritik
        if (!res.ok) throw new Error("Failed to load teams");
        const data = await res.json();

        const sel = document.getElementById("filterTeam");
        if (!sel) return;

        sel.innerHTML = `<option value="">All Teams</option>`;
        (data.items || []).forEach(t => {
            sel.innerHTML += `<option value="${t.team_id}">${t.team_name}</option>`;
        });
    } catch (err) {
        console.error(err);
    }
}


async function loadYearsForFilter() {
    try {
        const res = await fetch("/api/seasons/years");
        if (!res.ok) throw new Error("Failed to load years");
        const data = await res.json();

        const sel = document.getElementById("filterYear");
        if (!sel) return;

        sel.innerHTML = `<option value="">All Years</option>`;
        (data.years || []).forEach((y) => {
            sel.innerHTML += `<option value="${y}">${y}</option>`;
        });
    } catch (err) {
        console.error(err);
    }
}

// =============================
// View mode toggles
// =============================
function showGridView() {
    const grid = document.getElementById("seasonsGrid");
    const table = document.getElementById("seasonsTableContainer");
    const pager = document.getElementById("seasonsTablePager"); // varsa

    if (grid) grid.style.display = "grid";
    if (table) table.style.display = "none";
    if (pager) pager.style.display = "none";
}

function showTableView() {
    const grid = document.getElementById("seasonsGrid");
    const table = document.getElementById("seasonsTableContainer");
    const pager = document.getElementById("seasonsTablePager"); // varsa

    if (grid) grid.style.display = "none";
    if (table) table.style.display = "block";
    if (pager) pager.style.display = "flex";
}

// =============================
// Card Grid render
// =============================
async function loadSeasonsGrid(params = "") {
    try {
        const url = "/api/seasons" + params;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load seasons (grid)");

        const data = await res.json();
        const grid = document.getElementById("seasonsGrid");
        if (!grid) return;

        grid.innerHTML = "";
        showGridView();

        if (!data.items || data.items.length === 0) {
            grid.innerHTML = `<p style="color:white; text-align:center; opacity:0.7;">No seasons found.</p>`;
            return;
        }

        data.items.forEach((s) => {
            grid.innerHTML += `
        <div class="season-card">
          <h3>${escapeHtml(s.team_name || "Unknown Team")} - ${s.year ?? "-"}</h3>
          <div class="season-field">Title: ${escapeHtml(s.title || "-")}</div>
          <div class="season-field">Result: ${escapeHtml(s.result || "-")}</div>
          <div class="season-field">xG: ${safeNumber(s.xG)} | xGA: ${safeNumber(s.xGA)}</div>
          <div class="season-field">PPDA Att: ${safeNumber(s.ppda_att)}</div>

          <button
            type="button"
            onclick="viewSeason(${s.seasonentryid})"
            class="outline"
            style="margin-top:1rem; width:100%;"
          >
            Details →
          </button>
        </div>
      `;
        });
    } catch (err) {
        console.error(err);
    }
}

// =============================
// Table render (pagination)
// =============================
async function loadSeasonsTablePage(page = 1) {
    try {
        tableState.page = Math.max(1, page);

        const base = tableState.lastQuery ? `?${tableState.lastQuery}&` : "?";
        const url = `/api/seasons${base}page=${tableState.page}&per_page=${tableState.per_page}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load seasons (table)");

        const data = await res.json();
        tableState.total = data.total ?? 0;

        const tbody = document.getElementById("seasonsTableBody");
        if (!tbody) return;

        tbody.innerHTML = "";
        showTableView();

        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; opacity:0.7;">No seasons found.</td></tr>`;
            updatePagerUI();
            return;
        }

        data.items.forEach((s) => {
            tbody.innerHTML += `
        <tr>
          <td>${escapeHtml(s.team_name || "-")}</td>
          <td>${s.year ?? "-"}</td>
          <td>${escapeHtml(s.result || "-")}</td>
          <td>${safeNumber(s.xG)}</td>
          <td>${safeNumber(s.xGA)}</td>
          <td>${safeNumber(s.ppda_att)}</td>
          <td>
            <button type="button" class="details-btn" onclick="viewSeason(${s.seasonentryid})">
              Details →
            </button>
          </td>
        </tr>
      `;
        });

        updatePagerUI();
    } catch (err) {
        console.error(err);
    }
}

// =============================
// URL → team_id helper
// =============================
function getTeamIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("team_id") || "";
}

// =============================
// Navigate to detail page
// =============================
function viewSeason(id) {
    if (!id) return;
    window.location.href = `/seasons/${id}`;
}

// =============================
// Season Insights (Accordion)
// =============================
let insightsLoadedOnce = false;

function getSelectedOrLatestYear() {
    const yearSelect = document.getElementById("filterYear");
    if (!yearSelect) return "";

    let year = yearSelect.value;

    if (!year) {
        const opts = Array.from(yearSelect.options)
            .map((o) => o.value)
            .filter((v) => v);
        year = opts.length ? opts[0] : "";
    }
    return year;
}

function updateInsightsPill() {
    const pill = document.getElementById("insightsYearPill");
    if (!pill) return;
    const year = getSelectedOrLatestYear();
    pill.textContent = `Year: ${year || "Latest"}`;
}

async function loadSeasonInsights() {
    const body = document.getElementById("insightsBody");
    const status = document.getElementById("insightsStatus");
    if (!body) return;

    const year = getSelectedOrLatestYear();
    updateInsightsPill();

    if (status) status.textContent = "Loading insights...";
    body.innerHTML = `<tr><td colspan="7" class="acc-empty">Loading...</td></tr>`;

    try {
        const qs = new URLSearchParams();
        if (year) qs.set("year", year);
        qs.set("limit", "10");

        const res = await fetch(`/api/seasons/top?${qs.toString()}`);
        const data = await res.json();

        if (!data.success || !Array.isArray(data.items)) {
            if (status) status.textContent = "No insights available.";
            body.innerHTML = `<tr><td colspan="7" class="acc-empty">No insights available.</td></tr>`;
            return;
        }

        if (data.items.length === 0) {
            if (status) status.textContent = "No rows found for this year.";
            body.innerHTML = `<tr><td colspan="7" class="acc-empty">No rows found for this year.</td></tr>`;
            return;
        }

        if (status) status.textContent = `Showing top ${data.items.length} teams.`;

        body.innerHTML = data.items
            .map((r, i) => {
                return `
          <tr>
            <td class="col-rank">${i + 1}</td>
            <td>${escapeHtml(r.team_name ?? "-")}</td>
            <td class="col-num">${safeNumber(r.pts)}</td>
            <td class="col-num">${toFixedOrDash(r.xG, 2)}</td>
            <td class="col-num">${toFixedOrDash(r.xGA, 2)}</td>
            <td class="col-num">${toFixedOrDash(r.xg_diff, 2)}</td>
            <td><a class="acc-link" href="/seasons/${r.seasonentryid}">Open</a></td>
          </tr>
        `;
            })
            .join("");

        insightsLoadedOnce = true;
    } catch (e) {
        console.error(e);
        if (status) status.textContent = "Failed to load insights.";
        body.innerHTML = `<tr><td colspan="7" class="acc-empty">Failed to load insights.</td></tr>`;
    }
}

function setAccordionOpen(isOpen) {
    const acc = document.getElementById("seasonInsights");
    const panel = document.getElementById("insightsPanel");
    const btn = document.getElementById("toggleInsights");

    if (!acc || !panel || !btn) return;

    acc.classList.toggle("open", isOpen);
    btn.setAttribute("aria-expanded", String(isOpen));

    if (isOpen) {
        panel.hidden = false;
        if (!insightsLoadedOnce) loadSeasonInsights();
    } else {
        panel.hidden = true;
    }
}

// =============================
// Initial load
// =============================
async function autoFilterFromURL() {
    const teamId = getTeamIdFromURL();

    await loadTeamsForFilter();
    await loadYearsForFilter();
    updateInsightsPill();

    const btnViewAll = document.getElementById("btnViewAll");
    if (btnViewAll) btnViewAll.textContent = "View All";

    isTableMode = false;

    if (!teamId) {
        loadSeasonsGrid("");
        return;
    }

    const teamSel = document.getElementById("filterTeam");
    if (teamSel) teamSel.value = teamId;

    loadSeasonsGrid(`?team_id=${encodeURIComponent(teamId)}`);
}

// =============================
// Wire events only after DOM ready
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const btnSearch = document.getElementById("btnSearch");
    const btnReset = document.getElementById("btnReset");
    const btnViewAll = document.getElementById("btnViewAll");

    const toggleBtn = document.getElementById("toggleInsights");
    const refreshBtn = document.getElementById("btnRefreshInsights");
    const yearSelect = document.getElementById("filterYear");

    // Table pager elements
    const prevBtn = document.getElementById("tblPrev");
    const nextBtn = document.getElementById("tblNext");
    const perSel = document.getElementById("tblPerPage");

    // Search (grid veya table mode)
    if (btnSearch) {
        btnSearch.addEventListener("click", () => {
            const q = buildQueryFromFilters();
            const queryStr = q ? "?" + q : "";

            if (isTableMode) {
                tableState.lastQuery = q;
                loadSeasonsTablePage(1);
            } else {
                loadSeasonsGrid(queryStr);
            }
        });
    }

    // Reset
    if (btnReset) {
        btnReset.addEventListener("click", () => {
            history.replaceState(null, "", "/seasons");

            const elTeam = document.getElementById("filterTeam");
            const elYear = document.getElementById("filterYear");
            const elHA = document.getElementById("filterHA");
            const elRes = document.getElementById("filterResult");

            if (elTeam) elTeam.value = "";
            if (elYear) elYear.value = "";
            if (elHA) elHA.value = "";
            if (elRes) elRes.value = "";

            updateInsightsPill();

            if (isTableMode) {
                tableState.lastQuery = "";
                loadSeasonsTablePage(1);
            } else {
                loadSeasonsGrid("");
            }
        });
    }

    // View All => TOGGLE (table <-> grid)
    if (btnViewAll) {
        btnViewAll.addEventListener("click", () => {
            // Eğer table modundaysak -> grid'e dön
            if (isTableMode) {
                isTableMode = false;
                btnViewAll.textContent = "View All";

                const q = buildQueryFromFilters();
                const queryStr = q ? "?" + q : "";
                loadSeasonsGrid(queryStr);
                return;
            }

            // Table moda geç
            window.history.replaceState({}, "", "/seasons");

            isTableMode = true;
            btnViewAll.textContent = "Back to Cards";

            tableState.lastQuery = buildQueryFromFilters();
            tableState.per_page = Number(perSel?.value || 200);

            loadSeasonsTablePage(1);
        });
    }

    // Table pager events
    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (!isTableMode) return;
            loadSeasonsTablePage(Math.max(1, tableState.page - 1));
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (!isTableMode) return;
            const totalPages = Math.max(1, Math.ceil((tableState.total || 0) / tableState.per_page));
            loadSeasonsTablePage(Math.min(totalPages, tableState.page + 1));
        });
    }

    if (perSel) {
        perSel.addEventListener("change", () => {
            if (!isTableMode) return;
            tableState.per_page = Number(perSel.value || 200);
            loadSeasonsTablePage(1);
        });
    }

    // Accordion toggle
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const isOpen = toggleBtn.getAttribute("aria-expanded") === "true";
            setAccordionOpen(!isOpen);
        });
    }

    // Refresh insights
    if (refreshBtn) refreshBtn.addEventListener("click", loadSeasonInsights);

    // Year changed => refresh pill & insights (açıksa)
    if (yearSelect) {
        yearSelect.addEventListener("change", () => {
            updateInsightsPill();

            const isOpen = toggleBtn && toggleBtn.getAttribute("aria-expanded") === "true";
            if (isOpen) loadSeasonInsights();
        });
    }

    // Start closed
    setAccordionOpen(false);

    // Kick off initial load
    autoFilterFromURL();
});
