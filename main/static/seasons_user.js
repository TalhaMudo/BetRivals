// =============================
// Dropdown doldurma
// =============================
async function loadTeamsForFilter() {
    let res = await fetch("/api/teams");
    let data = await res.json();

    let sel = document.getElementById("filterTeam");
    sel.innerHTML = `<option value="">All Teams</option>`;

    data.items.forEach(t => {
        sel.innerHTML += `<option value="${t.team_id}">${t.team_name}</option>`;
    });
}
async function loadYearsForFilter() {
    let res = await fetch("/api/seasons?per_page=9999");
    let data = await res.json();

    let years = new Set();

    data.items.forEach(s => years.add(s.year));

    let sel = document.getElementById("filterYear");
    sel.innerHTML = `<option value="">All Years</option>`;

    [...years].sort((a, b) => b - a).forEach(y => {
        sel.innerHTML += `<option value="${y}">${y}</option>`;
    });
}

// =============================
// VIEW MODE CONTROLS
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
// Card Mode (Grid) Render
// =============================
async function loadSeasonsGrid(params = "") {
    let url = "/api/seasons" + params;
    let res = await fetch(url);
    let data = await res.json();

    let grid = document.getElementById("seasonsGrid");
    grid.innerHTML = "";
    showGridView();

    if (!data.items || data.items.length === 0) {
        grid.innerHTML = `<p style="color:white; text-align:center; opacity:0.7;">No seasons found.</p>`;
        return;
    }

    data.items.forEach(s => {
        grid.innerHTML += `
            <div class="season-card">
                <h3>${s.team_name} - ${s.year}</h3>
                <div class="season-field">Title: ${s.title || "-"}</div>
                <div class="season-field">Result: ${s.result || "-"}</div>
                <div class="season-field">xG: ${s.xG} | xGA: ${s.xGA}</div>
                <div class="season-field">PPDA: ${s.ppda_att}</div>

                <button onclick="viewSeason(${s.seasonentryid})" class="outline" style="margin-top:1rem; width:100%;">
                    Details →
                </button>
            </div>
        `;
    });
}

// =============================
// Table Mode Render (View All)
// =============================
async function loadSeasonsTable(params = "") {
    let url = "/api/seasons" + params;
    let res = await fetch(url);
    let data = await res.json();

    let tbody = document.getElementById("seasonsTableBody");
    tbody.innerHTML = "";
    showTableView();

    if (!data.items || data.items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; opacity:0.7;">No seasons found.</td></tr>`;
        return;
    }

    data.items.forEach(s => {
        tbody.innerHTML += `
            <tr>
                <td>${s.team_name}</td>
                <td>${s.year}</td>
                <td>${s.result}</td>
                <td>${s.xG}</td>
                <td>${s.xGA}</td>
                <td>${s.ppda_att}</td>
                <td>
                    <button class="details-btn" onclick="viewSeason(${s.seasonentryid})">
                        Details →
                    </button>
                </td>
            </tr>
        `;
    });
}

// =============================
// URL parametresinden team_id alma
// =============================
function getTeamIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("team_id") || "";
}

// =============================
// Sayfa ilk açıldığında otomatik davranış
// =============================
async function autoFilterFromURL() {
    const teamId = getTeamIdFromURL();
    await loadTeamsForFilter();
    await loadYearsForFilter();

    // Eğer URL'de team_id yoksa → tüm sezonları kart modunda yükle
    if (!teamId) {
        loadSeasonsGrid("");
        return;
    }

    // Eğer URL'den bir takım geldiyse → dropdown seçili olsun + sadece o takım görünsün
    document.getElementById("filterTeam").value = teamId;
    loadSeasonsGrid(`?team_id=${teamId}`);
}

// =============================
// Detay butonu (opsiyonel)
// =============================
function viewSeason(id) {
    alert("Season detail page (opsiyonel). ID: " + id);
}

// =============================
// SEARCH
// =============================
document.getElementById("btnSearch").onclick = () => {
    let t = document.getElementById("filterTeam").value;
    let y = document.getElementById("filterYear").value;
    let ha = document.getElementById("filterHA").value;
    let r = document.getElementById("filterResult").value;

    let q = `?team_id=${t}&year=${y}&h_a=${ha}&result=${r}`;
    loadSeasonsGrid(q);
};

// =============================
// RESET → kart görünümü + temiz URL
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
// VIEW ALL → tablo görünümüne geçiş
// =============================
document.getElementById("btnViewAll").onclick = () => {
    window.history.replaceState({}, "", "/seasons");
    loadSeasonsTable("?per_page=5000");
};

// =============================
// SAYFA BAŞLANGICI
// =============================
autoFilterFromURL();
