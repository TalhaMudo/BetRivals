let matchCurrentPage = 1;
let matchEditId = null;

async function loadMatches(page = 1) {
    matchCurrentPage = page;
    const team = document.getElementById('filterTeam').value.trim();
    const season = document.getElementById('filterSeason').value;
    const params = new URLSearchParams({ page, limit: 50 });
    if (team) params.set('team', team);
    if (season) params.set('season', season);

    const res = await fetch('/api/admin/matches?' + params.toString());
    const data = await res.json();
    if (!data.success) {
        showAlert(data.error || 'Failed loading matches', 'error');
        return;
    }

    renderMatchesTable(data.matches || []);
    renderMatchesPagination(data.total || 0, 50);

    // populate season dropdown (first time)
    const set = new Set((data.matches || []).map(m => m.season).filter(Boolean));
    const sel = document.getElementById('filterSeason');
    sel.innerHTML = '<option value="">Any Season</option>';
    Array.from(set).sort((a,b)=> b - a).forEach(s => sel.insertAdjacentHTML('beforeend', `<option value="${s}">${s}</option>`));
}

function renderMatchesTable(matches) {
    const tbody = document.getElementById('matchesTableBody');
    if (!matches || matches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#888">No matches found</td></tr>';
        return;
    }

    tbody.innerHTML = matches.map(m => `
        <tr>
            <td>${m.match_id}</td>
            <td>${m.season ?? ''}</td>
            <td>${m.date ? new Date(m.date).toLocaleString() : ''}</td>
            <td>${m.team_h ?? ''}</td>
            <td>${m.h_goals != null ? m.h_goals : '-'} : ${m.a_goals != null ? m.a_goals : '-'}</td>
            <td>${m.team_a ?? ''}</td>
            <td>${m.league ?? ''}</td>
            <td class="actions">
                <button class="edit-btn" onclick="editMatch(${m.match_id})">Edit</button>
                <button class="del-btn" onclick="deleteMatchAction(${m.match_id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function renderMatchesPagination(total, limit) {
    const pages = Math.max(1, Math.ceil((total || 0) / limit));
    const container = document.getElementById('paginationContainer');
    let html = '';
    for (let i=1;i<=pages;i++) {
        html += `<button class="page-btn ${i===matchCurrentPage? 'active':''}" onclick="loadMatches(${i})">${i}</button>`;
    }
    container.innerHTML = html;
}

function openCreateModal() {
    matchEditId = null;
    document.getElementById('matchForm').reset();
    document.getElementById('modalTitle').textContent = 'Add Match';
    document.getElementById('submitBtn').textContent = 'Add Match';
    const mid = document.getElementById('field_match_id'); if (mid) mid.disabled = false;
    // today's date is default for new matches
    const dateField = document.getElementById('field_date');
    if (dateField) {
        const today = new Date().toISOString().slice(0, 16);
        dateField.value = today;
    }
    // hide "Add Shots" button when creating new match
    document.getElementById('addShotsBtn').style.display = 'none';
    
    document.getElementById('matchModal').classList.add('active');
}

async function addShotsToMatch() {
    const matchId = document.getElementById('field_match_id').value;
    if (!matchId) {
        showAlert('No match ID available', 'error');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(matchId);
    } catch (err) {
        // its for fallback, still continue with redirect
    }
    
    showRedirectPopup(matchId);
}

function showRedirectPopup(matchId) {
    const overlay = document.createElement('div');
    overlay.id = 'redirectPopup';
    overlay.className = 'redirect-popup-overlay';
    
    overlay.innerHTML = `
        <div class="redirect-popup">
            <div class="popup-icon">📋</div>
            <h3>Match ID Copied!</h3>
            <p class="popup-match-id">${matchId}</p>
            <p class="popup-message">Redirecting to add shots page...<br>Paste the match ID in the form.</p>
            <div class="countdown-bar-container">
                <div class="countdown-bar"></div>
            </div>
            <div class="popup-buttons">
                <button class="popup-btn-go" onclick="redirectToShots()">Go Now</button>
                <button class="popup-btn-cancel" onclick="cancelRedirect()">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // start countdown animation
    const countdownBar = overlay.querySelector('.countdown-bar');
    countdownBar.style.animation = 'countdown 5s linear forwards';
    
    // auto redirect after 5 seconds
    window.redirectTimeout = setTimeout(() => {
        redirectToShots();
    }, 5000);
}

function redirectToShots() {
    clearTimeout(window.redirectTimeout);
    const popup = document.getElementById('redirectPopup');
    if (popup) popup.remove();
    window.location.href = '/admin/shots/add';
}

function cancelRedirect() {
    clearTimeout(window.redirectTimeout);
    const popup = document.getElementById('redirectPopup');
    if (popup) popup.remove();
}

function closeModal() { document.getElementById('matchModal').classList.remove('active'); }

async function editMatch(id) {
    matchEditId = id;
    try {
        const res = await fetch(`/api/admin/matches/${id}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Not found');

        const m = data.match;
        document.getElementById('field_match_id').value = m.match_id || '';
        document.getElementById('field_date').value = m.date ? new Date(m.date).toISOString().slice(0,16) : '';
        document.getElementById('field_season').value = m.season || '';
        document.getElementById('field_league').value = m.league || '';
        document.getElementById('field_league_id').value = m.league_id != null ? m.league_id : '';
        document.getElementById('field_team_h').value = m.team_h || '';
        document.getElementById('field_team_a').value = m.team_a || '';
        document.getElementById('field_h_goals').value = m.h_goals != null ? m.h_goals : '';
        document.getElementById('field_a_goals').value = m.a_goals != null ? m.a_goals : '';
        document.getElementById('field_h_xg').value = m.h_xg != null ? m.h_xg : '';
        document.getElementById('field_a_xg').value = m.a_xg != null ? m.a_xg : '';
        document.getElementById('field_h_shot').value = m.h_shot != null ? m.h_shot : '';
        document.getElementById('field_a_shot').value = m.a_shot != null ? m.a_shot : '';
        document.getElementById('field_h_shotOnTarget').value = m.h_shotOnTarget != null ? m.h_shotOnTarget : '';
        document.getElementById('field_a_shotOnTarget').value = m.a_shotOnTarget != null ? m.a_shotOnTarget : '';
        document.getElementById('field_h_deep').value = m.h_deep != null ? m.h_deep : '';
        document.getElementById('field_a_deep').value = m.a_deep != null ? m.a_deep : '';
        document.getElementById('field_h_ppda').value = m.h_ppda != null ? m.h_ppda : '';
        document.getElementById('field_a_ppda').value = m.a_ppda != null ? m.a_ppda : '';
        document.getElementById('field_h_w').value = m.h_w != null ? m.h_w : '';
        document.getElementById('field_h_d').value = m.h_d != null ? m.h_d : '';
        document.getElementById('field_h_l').value = m.h_l != null ? m.h_l : '';

        document.getElementById('modalTitle').textContent = `Edit Match ${id}`;
        document.getElementById('submitBtn').textContent = 'Save changes';
        const mid = document.getElementById('field_match_id'); if (mid) { mid.disabled = true; }
        
        // show "Add Shots" button when editing
        document.getElementById('addShotsBtn').style.display = 'inline-block';
        
        document.getElementById('matchModal').classList.add('active');
    } catch (err) {
        showAlert(err.message || 'Could not load match', 'error');
    }
}

async function saveMatch(e) {
    e.preventDefault();
    const form = document.getElementById('matchForm');
    
    // check required fields before sending to backend. other fields may be added later
    const matchId = document.getElementById('field_match_id').value.trim();
    const teamH = document.getElementById('field_team_h').value.trim();
    const teamA = document.getElementById('field_team_a').value.trim();
    
    if (!matchId || matchId === '') {
        showAlert('Match ID is required', 'error');
        return;
    }
    if (!teamH || teamH === '') {
        showAlert('Home Team is required', 'error');
        return;
    }
    if (!teamA || teamA === '') {
        showAlert('Away Team is required', 'error');
        return;
    }
    
    const payload = {
        match_id: parseInt(matchId) || null,
        date: document.getElementById('field_date').value || null,
        season: parseInt(document.getElementById('field_season').value) || null,
        league: document.getElementById('field_league').value || null,
        league_id: document.getElementById('field_league_id').value !== '' ? parseInt(document.getElementById('field_league_id').value) : null,
        team_h: teamH,
        team_a: teamA,
        h_goals: document.getElementById('field_h_goals').value !== '' ? parseInt(document.getElementById('field_h_goals').value) : null,
        a_goals: document.getElementById('field_a_goals').value !== '' ? parseInt(document.getElementById('field_a_goals').value) : null,
        h_xg: document.getElementById('field_h_xg').value !== '' ? parseFloat(document.getElementById('field_h_xg').value) : null,
        a_xg: document.getElementById('field_a_xg').value !== '' ? parseFloat(document.getElementById('field_a_xg').value) : null,
        h_shot: document.getElementById('field_h_shot').value !== '' ? parseInt(document.getElementById('field_h_shot').value) : null,
        a_shot: document.getElementById('field_a_shot').value !== '' ? parseInt(document.getElementById('field_a_shot').value) : null,
        h_shotOnTarget: document.getElementById('field_h_shotOnTarget').value !== '' ? parseInt(document.getElementById('field_h_shotOnTarget').value) : null,
        a_shotOnTarget: document.getElementById('field_a_shotOnTarget').value !== '' ? parseInt(document.getElementById('field_a_shotOnTarget').value) : null,
        h_deep: document.getElementById('field_h_deep').value !== '' ? parseInt(document.getElementById('field_h_deep').value) : null,
        a_deep: document.getElementById('field_a_deep').value !== '' ? parseInt(document.getElementById('field_a_deep').value) : null,
        h_ppda: document.getElementById('field_h_ppda').value !== '' ? parseFloat(document.getElementById('field_h_ppda').value) : null,
        a_ppda: document.getElementById('field_a_ppda').value !== '' ? parseFloat(document.getElementById('field_a_ppda').value) : null,
        h_w: document.getElementById('field_h_w').value !== '' ? parseFloat(document.getElementById('field_h_w').value) : null,
        h_d: document.getElementById('field_h_d').value !== '' ? parseFloat(document.getElementById('field_h_d').value) : null,
        h_l: document.getElementById('field_h_l').value !== '' ? parseFloat(document.getElementById('field_h_l').value) : null
    };

    const url = matchEditId ? `/api/admin/matches/${matchEditId}` : '/api/admin/matches';
    const method = matchEditId ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Failed');

        showAlert(data.message || 'Saved');
        closeModal();
        loadMatches(matchCurrentPage);
    } catch (err) {
        showAlert(err.message || 'Error saving', 'error');
    }
}

async function deleteMatchAction(matchId) {
    if (!confirm('Delete this match?')) return;
    try {
        const res = await fetch(`/api/admin/matches/${matchId}`, { method: 'DELETE' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Delete failed');
        showAlert('Match deleted');
        loadMatches(matchCurrentPage);
    } catch (err) { showAlert(err.message || 'Delete failed', 'error'); }
}

function showAlert(message, type = 'success') {
    // close modal first so the alert will be visible
    closeModal();
    
    const el = document.getElementById('alert');
    el.textContent = message; 
    el.className = `alert show alert-${type}`;
    setTimeout(() => el.classList.remove('show'), 4000);
}

async function loadSeasons() {
    try {
        const res = await fetch('/api/match/seasons');
        const data = await res.json();
        const sel = document.getElementById('filterSeason');
        const modalSel = document.getElementById('field_season');
        if (sel && data.seasons) {
            sel.innerHTML = '<option value="">Any Season</option>' + data.seasons.map(s => `<option value="${s}">${s}</option>`).join('');
        }
        if (modalSel && data.seasons) {
            modalSel.innerHTML = '<option value="">-- select season --</option>' + data.seasons.map(s => `<option value="${s}">${s}</option>`).join('');
        }
    } catch (e) {
        console.warn('Could not load seasons', e);
    }
}

// load initial
document.addEventListener('DOMContentLoaded', async () => { await loadSeasons(); await loadMatches(); });
