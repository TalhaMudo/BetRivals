// =============================
// Helpers
// =============================
function escapeHtml(str) {
    return String(str ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function debounce(fn, wait = 250) {
    let t = null;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), wait);
    };
}

function toFixedOrDash(v, digits = 2) {
    if (v === null || v === undefined || v === "") return "-";
    const n = Number(v);
    if (Number.isNaN(n)) return "-";
    return n.toFixed(digits);
}

// =============================
// Navigation
// =============================
function viewTeam(id) {
    if (!id && id !== 0) return;
    window.location.href = "/seasons?team_id=" + encodeURIComponent(id);
}
window.viewTeam = viewTeam; // onclick için

// =============================
// Mode state
// =============================
let isTableMode = false;

function showGridView() {
    const grid = document.getElementById("teamsGrid");
    const table = document.getElementById("teamsTableContainer");
    if (grid) grid.style.display = "grid";
    if (table) table.style.display = "none";

    const btnViewAll = document.getElementById("btnViewAll");
    if (btnViewAll) btnViewAll.textContent = "View All";
}

function showTableView() {
    const grid = document.getElementById("teamsGrid");
    const table = document.getElementById("teamsTableContainer");
    if (grid) grid.style.display = "none";
    if (table) table.style.display = "block";

    const btnViewAll = document.getElementById("btnViewAll");
    if (btnViewAll) btnViewAll.textContent = "Back to Cards";
}

// =============================
// Fetch teams (single source)
// =============================
async function fetchTeams(q = "") {
    const url =
        "/api/teams?per_page=5000&q=" + encodeURIComponent(q); // <-- kritik
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load teams");
    const data = await res.json();
    return data.items || [];
}

// =============================
// Render grid
// =============================
async function loadTeamsGrid(q = "") {
    try {
        const items = await fetchTeams(q);

        const grid = document.getElementById("teamsGrid");
        if (!grid) return;

        grid.innerHTML = "";
        showGridView();

        if (!items.length) {
            grid.innerHTML = `<p style="opacity:.7; text-align:center;">No teams found.</p>`;
            return;
        }

        items.forEach((t) => {
            const logoUrl = `/static/team_logos/${t.team_id}.png`;

            grid.insertAdjacentHTML(
                "beforeend",
                `
      <div class="team-card">
        <div class="team-head">
          <img class="team-logo"
               src="${logoUrl}"
               alt="${escapeHtml(t.team_name || "Team")}"
               onerror="this.src='/static/team_logos/default.png'; this.onerror=null;">
          <div class="team-meta">
            <h3>${escapeHtml(t.team_name || "Unknown Team")}</h3>
            <p class="team-id">#${escapeHtml(t.team_id)}</p>
          </div>
        </div>

        <button type="button" onclick="viewTeam(${t.team_id})">View Seasons →</button>
      </div>
    `
            );
        });

    } catch (e) {
        console.error(e);
    }
}

// =============================
// Render table (NO pagination)
// =============================
async function loadTeamsTable(q = "") {
    try {
        const items = await fetchTeams(q);

        const tbody = document.getElementById("teamsTableBody");
        if (!tbody) return;

        tbody.innerHTML = "";
        showTableView();

        if (!items.length) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; opacity:.7;">No teams found.</td></tr>`;
            return;
        }

        items.forEach((t, i) => {
            tbody.insertAdjacentHTML(
                "beforeend",
                `
        <tr>
          <td class="col-rank">${i + 1}</td>
          <td>${escapeHtml(t.team_name || "-")}</td>
          <td class="col-num mono">${escapeHtml(t.team_id)}</td>
          <td class="col-actions">
            <button type="button" class="table-action-btn" onclick="viewTeam(${JSON.stringify(t.team_id)})">
              View Seasons →
            </button>
          </td>
        </tr>
        `
            );
        });
    } catch (e) {
        console.error(e);
    }
}

// =============================
// Autocomplete
// =============================
function hideSuggest() {
    const box = document.getElementById("teamSuggest");
    if (!box) return;
    box.hidden = true;
    box.innerHTML = "";
}

function renderSuggest(items) {
    const box = document.getElementById("teamSuggest");
    if (!box) return;

    if (!items.length) return hideSuggest();

    box.innerHTML = items.slice(0, 8).map(t => `
    <div class="typeahead-item" data-team-name="${escapeHtml(t.team_name)}">
      <div class="typeahead-name">${escapeHtml(t.team_name)}</div>
      <div class="typeahead-id">#${escapeHtml(t.team_id)}</div>
    </div>
  `).join("");

    box.hidden = false;
}

async function fetchSuggest(q) {
    const trimmed = (q || "").trim();
    if (trimmed.length < 1) return hideSuggest();

    try {
        const items = await fetchTeams(trimmed);
        renderSuggest(items);
    } catch (e) {
        console.error(e);
        hideSuggest();
    }
}
const debouncedSuggest = debounce(fetchSuggest, 220);

// =============================
// Team Summary (API aggregation)
// =============================
async function loadTeamSummary() {
    const body = document.getElementById("teamSummaryBody");
    const status = document.getElementById("teamSummaryStatus");
    const minSel = document.getElementById("minSeasonsSelect");

    if (!body) return;

    const minSeasons = minSel ? minSel.value : "3";

    if (status) status.textContent = "Loading summary...";
    body.innerHTML = `<tr><td colspan="8" class="acc-empty">Loading...</td></tr>`;

    try {
        const res = await fetch(`/api/teams/summary?min_seasons=${encodeURIComponent(minSeasons)}&limit=24`);
        if (!res.ok) throw new Error("Failed to load summary");
        const data = await res.json();

        if (!data.success || !Array.isArray(data.items)) {
            if (status) status.textContent = "No summary available.";
            body.innerHTML = `<tr><td colspan="8" class="acc-empty">No summary available.</td></tr>`;
            return;
        }

        if (data.items.length === 0) {
            if (status) status.textContent = "No rows found.";
            body.innerHTML = `<tr><td colspan="8" class="acc-empty">No rows found.</td></tr>`;
            return;
        }

        if (status) status.textContent = `Showing ${data.items.length} teams.`;

        body.innerHTML = data.items.map((r, i) => `
      <tr>
        <td class="col-rank">${i + 1}</td>
        <td>${escapeHtml(r.team_name ?? "-")}</td>
        <td class="col-num mono">${escapeHtml(r.total_seasons ?? "-")}</td>
        <td class="col-num mono">${toFixedOrDash(r.avg_xG, 2)}</td>
        <td class="col-num mono">${toFixedOrDash(r.avg_xGA, 2)}</td>
        <td class="col-num mono">${toFixedOrDash(r.avg_xg_diff, 2)}</td>
        <td class="col-num mono">${escapeHtml(r.total_points ?? "-")}</td>
        <td class="col-num mono">${toFixedOrDash(r.avg_points, 2)}</td>
      </tr>
    `).join("");
    } catch (e) {
        console.error(e);
        if (status) status.textContent = "Failed to load summary.";
        body.innerHTML = `<tr><td colspan="8" class="acc-empty">Failed to load summary.</td></tr>`;
    }
}

// =============================
// Accordion wiring (Team Summary)
// =============================
let teamSummaryLoadedOnce = false;

function updateTeamSummaryPill() {
    const pill = document.getElementById("teamSummaryPill");
    const minSel = document.getElementById("minSeasonsSelect");
    if (!pill || !minSel) return;
    pill.textContent = `Min seasons: ${minSel.value}`;
}

function setTeamSummaryOpen(isOpen) {
    const acc = document.getElementById("teamSummaryAcc");
    const panel = document.getElementById("teamSummaryPanel");
    const btn = document.getElementById("toggleTeamSummary");

    if (!acc || !panel || !btn) return;

    acc.classList.toggle("open", isOpen);
    btn.setAttribute("aria-expanded", String(isOpen));

    if (isOpen) {
        panel.hidden = false;
        updateTeamSummaryPill();
        if (!teamSummaryLoadedOnce) {
            loadTeamSummary();
            teamSummaryLoadedOnce = true;
        }
    } else {
        panel.hidden = true;
    }
}

// =============================
// Wire events
// =============================
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchTeam");
    const btnSearch = document.getElementById("btnSearch");
    const btnReset = document.getElementById("btnReset");
    const btnViewAll = document.getElementById("btnViewAll");
    const suggestBox = document.getElementById("teamSuggest");

    // Search
    if (btnSearch) {
        btnSearch.addEventListener("click", () => {
            const q = input?.value || "";
            hideSuggest();
            if (isTableMode) loadTeamsTable(q);
            else loadTeamsGrid(q);
        });
    }

    // Reset
    if (btnReset) {
        btnReset.addEventListener("click", () => {
            if (input) input.value = "";
            hideSuggest();
            if (isTableMode) loadTeamsTable("");
            else loadTeamsGrid("");
        });
    }

    // View All toggle
    if (btnViewAll) {
        btnViewAll.addEventListener("click", () => {
            hideSuggest();
            const q = input?.value || "";

            isTableMode = !isTableMode;
            if (isTableMode) loadTeamsTable(q);
            else loadTeamsGrid(q);
        });
    }

    // Autocomplete
    if (input) {
        input.addEventListener("input", (e) => debouncedSuggest(e.target.value));
        input.addEventListener("focus", () => debouncedSuggest(input.value));

        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                btnSearch?.click();
            }
            if (e.key === "Escape") hideSuggest();
        });
    }

    // Suggest click
    if (suggestBox) {
        suggestBox.addEventListener("click", (e) => {
            const item = e.target.closest(".typeahead-item");
            if (!item) return;

            const name = item.getAttribute("data-team-name") || "";
            if (input) input.value = name;

            hideSuggest();
            btnSearch?.click();
        });
    }

    // Click outside => close suggestions
    document.addEventListener("click", (e) => {
        if (!suggestBox || !input) return;
        const inside = suggestBox.contains(e.target) || input.contains(e.target);
        if (!inside) hideSuggest();
    });

    // Accordion events
    const toggleBtn = document.getElementById("toggleTeamSummary");
    const refreshBtn = document.getElementById("btnRefreshSummary");
    const minSel = document.getElementById("minSeasonsSelect");

    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const openNow = toggleBtn.getAttribute("aria-expanded") === "true";
            setTeamSummaryOpen(!openNow);
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            teamSummaryLoadedOnce = true;
            updateTeamSummaryPill();
            loadTeamSummary();
        });
    }

    if (minSel) {
        minSel.addEventListener("change", () => {
            updateTeamSummaryPill();
            const isOpen = toggleBtn && toggleBtn.getAttribute("aria-expanded") === "true";
            if (isOpen) {
                teamSummaryLoadedOnce = true;
                loadTeamSummary();
            }
        });
    }

    // Start closed
    setTeamSummaryOpen(false);

    // initial load
    isTableMode = false;
    loadTeamsGrid("");
});
