async function loadTeams(q = "") {
    let url = "/api/teams?q=" + encodeURIComponent(q);
    let res = await fetch(url);
    let data = await res.json();

    let grid = document.getElementById("teamsGrid");
    grid.innerHTML = "";

    data.items.forEach(t => {
        grid.innerHTML += `
            <div class="team-card">
                <h3>${t.team_name}</h3>
                <p>ID: ${t.team_id}</p>
                <button onclick="viewTeam(${t.team_id})">View Seasons →</button>
            </div>
        `;
    });
}
function viewSeasons(teamId) {
    window.location.href = `/seasons?team_id=${teamId}`;
}

function viewTeam(id) {
    window.location.href = "/seasons?team_id=" + id;
}

document.getElementById("btnSearch").onclick = () =>
    loadTeams(document.getElementById("searchTeam").value);

document.getElementById("btnReset").onclick = () => {
    document.getElementById("searchTeam").value = "";
    loadTeams();
};

document.getElementById("btnViewAll").onclick = () => loadTeams("");

loadTeams();
