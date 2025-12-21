let playerCurrentPage = 1;

async function loadPlayers(page = 1) {
    playerCurrentPage = page;
    const name = document.getElementById('filterName').value.trim();
    const team = document.getElementById('filterTeam').value.trim();
    const year = document.getElementById('filterYear').value;
    
    const params = new URLSearchParams({ page, limit: 50 });
    if (name) params.set('name', name);
    if (team) params.set('team', team);
    if (year) params.set('year', year);

    try {
        const res = await fetch('/api/admin/players?' + params.toString());
        const data = await res.json();
        if (!data.success) {
            showAlert(data.error || 'Failed loading players', 'error');
            return;
        }

        renderPlayersTable(data.players || []);
        renderPlayersPagination(data.total || 0, 50);

        // Populate year dropdown (first time)
        const yearSet = new Set((data.players || []).map(p => p.year).filter(Boolean));
        const yearSel = document.getElementById('filterYear');
        if (yearSel.children.length <= 1) { // Only "Any Year" option
            Array.from(yearSet).sort((a, b) => b - a).forEach(y => {
                const option = document.createElement('option');
                option.value = y;
                option.textContent = y;
                yearSel.appendChild(option);
            });
        }
    } catch (err) {
        showAlert('Network error: ' + err.message, 'error');
    }
}

function renderPlayersTable(players) {
    const tbody = document.getElementById('playersTableBody');
    if (!players || players.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:#888">No players found</td></tr>';
        return;
    }

    tbody.innerHTML = players.map(p => `
        <tr>
            <td>${p.season_player_id || '-'}</td>
            <td>${p.player_name || '-'}</td>
            <td>${p.team_title || '-'}</td>
            <td>${p.position || '-'}</td>
            <td>${p.year || '-'}</td>
            <td>${p.goals != null ? p.goals : '-'}</td>
            <td>${p.assists != null ? p.assists : '-'}</td>
            <td>${p.games != null ? p.games : '-'}</td>
            <td class="actions">
                <button class="edit-btn" onclick="editPlayer(${p.season_player_id})">Edit</button>
                <button class="del-btn" onclick="deletePlayerAction(${p.season_player_id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function renderPlayersPagination(total, limit) {
    const pages = Math.max(1, Math.ceil((total || 0) / limit));
    const container = document.getElementById('paginationContainer');
    let html = '';
    for (let i = 1; i <= pages; i++) {
        html += `<button class="page-btn ${i === playerCurrentPage ? 'active' : ''}" onclick="loadPlayers(${i})">${i}</button>`;
    }
    container.innerHTML = html;
}

function editPlayer(seasonPlayerId) {
    // Redirect to edit page with season_player_id as query parameter
    window.location.href = `/players/edit?season_player_id=${seasonPlayerId}`;
}

async function deletePlayerAction(seasonPlayerId) {
    if (!confirm(`Are you sure you want to delete player season entry ${seasonPlayerId}? This action cannot be undone.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/admin/players/season/${seasonPlayerId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        
        if (data.success) {
            showAlert('Player deleted successfully', 'success');
            loadPlayers(playerCurrentPage);
        } else {
            showAlert(data.error || 'Failed to delete player', 'error');
        }
    } catch (err) {
        showAlert('Network error: ' + err.message, 'error');
    }
}

function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert ${type} show`;
    setTimeout(() => {
        alert.classList.remove('show');
    }, 3000);
}

// Load players on page load
loadPlayers();

