// =============================
// Helpers
// =============================
function safeNumber(val) {
    return val === null || val === undefined ? "-" : val;
}

// =============================
// Dropdown filling
// =============================
async function loadTeamsForFilter() {
    try {
        const res = await fetch("/api/teams");
        if (!res.ok) throw new Error("Failed to load teams");
        const data = await res.json();

        const sel = document.getElementById("filterTeam");
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
        const res = await fetch("/api/seasons?per_page=9999");
        if (!res.ok) throw new Error("Failed to load seasons for years");
        const data = await res.json();

        const years = new Set();
        (data.items || []).forEach(s => {
            if (s.year !== null && s.year !== undefined) {
                years.add(s.year);
            }
        });

        const sel = document.getElementById("filterYear");
        sel.innerHTML = `<option value="">All Years</option>`;
        [...years].sort((a, b) => b - a).forEach(y => {
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
    document.getElementById("seasonsGrid").style.display = "grid";
    document.getElementById("seasonsTableContainer").style.display = "none";
}

function showTableView() {
    document.getElementById("seasonsGrid").style.display = "none";
    document.getElementById("seasonsTableContainer").style.display = "block";
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
        grid.innerHTML = "";
        showGridView();

        if (!data.items || data.items.length === 0) {
            grid.innerHTML = `<p style="color:white; text-align:center; opacity:0.7;">No seasons found.</p>`;
            return;
        }

        data.items.forEach(s => {
            grid.innerHTML += `
                <div class="season-card">
                    <h3>${s.team_name || "Unknown Team"} - ${s.year ?? "-"}</h3>
                    <div class="season-field">Title: ${s.title || "-"}</div>
                    <div class="season-field">Result: ${s.result || "-"}</div>
                    <div class="season-field">xG: ${safeNumber(s.xG)} | xGA: ${safeNumber(s.xGA)}</div>
                    <div class="season-field">PPDA Att: ${safeNumber(s.ppda_att)}</div>

                    <button onclick="viewSeason(${s.seasonentryid})"
                            class="outline"
                            style="margin-top:1rem; width:100%;">
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
// Table render (View All)
// =============================
async function loadSeasonsTable(params = "") {
    try {
        const url = "/api/seasons" + params;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load seasons (table)");

        const data = await res.json();
        const tbody = document.getElementById("seasonsTableBody");
        tbody.innerHTML = "";
        showTableView();

        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; opacity:0.7;">No seasons found.</td></tr>`;
            return;
        }

        data.items.forEach(s => {
            tbody.innerHTML += `
                <tr>
                    <td>${s.team_name || "-"}</td>
                    <td>${s.year ?? "-"}</td>
                    <td>${s.result || "-"}</td>
                    <td>${safeNumber(s.xG)}</td>
                    <td>${safeNumber(s.xGA)}</td>
                    <td>${safeNumber(s.ppda_att)}</td>
                    <td>
                        <button class="details-btn" onclick="viewSeason(${s.seasonentryid})">
                            Details →
                        </button>
                    </td>
                </tr>
            `;
        });
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
// Auto filter on first load
// =============================
async function autoFilterFromURL() {
    const teamId = getTeamIdFromURL();
    await loadTeamsForFilter();
    await loadYearsForFilter();

    if (!teamId) {
        loadSeasonsGrid("");
        return;
    }

    document.getElementById("filterTeam").value = teamId;
    loadSeasonsGrid(`?team_id=${encodeURIComponent(teamId)}`);
}

// =============================
// Navigate to detail page
// =============================
function viewSeason(id) {
    if (!id) return;
    window.location.href = `/seasons/${id}`;
}

// =============================
// Search button
// =============================
document.getElementById("btnSearch").onclick = () => {
    const t = document.getElementById("filterTeam").value;
    const y = document.getElementById("filterYear").value;
    const ha = document.getElementById("filterHA").value;
    const r = document.getElementById("filterResult").value;

    const params = [];
    if (t) params.push(`team_id=${encodeURIComponent(t)}`);
    if (y) params.push(`year=${encodeURIComponent(y)}`);
    if (ha) params.push(`h_a=${encodeURIComponent(ha)}`);
    if (r) params.push(`result=${encodeURIComponent(r)}`);

    const q = params.length ? "?" + params.join("&") : "";
    loadSeasonsGrid(q);
};

// =============================
// Reset button
// =============================
document.getElementById("btnReset").onclick = () => {
    history.replaceState(null, "", "/seasons");

    document.getElementById("filterTeam").value = "";
    document.getElementById("filterYear").value = "";
    document.getElementById("filterHA").value = "";
    document.getElementById("filterResult").value = "";

    loadSeasonsGrid("");
};

// =============================
// View All → table mode
// =============================
document.getElementById("btnViewAll").onclick = () => {
    window.history.replaceState({}, "", "/seasons");
    loadSeasonsTable("?per_page=5000");
};

// =============================
// Initial load
// =============================
autoFilterFromURL();
