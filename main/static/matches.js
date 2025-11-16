// Matches page functionality

// js codes for matches.html

function parseDate(d) {
    return d ? new Date(d) : null;
}

// this function will return matches based on filters
async function fetchMatches(filters) { // filters will affect the sql query
    const res = await fetch('/api/matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
    });
    
    if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    const data = await res.json();
    return data.matches || [];
}

function renderTable(matches) {
    const container = document.getElementById('results');
    if (!matches || matches.length === 0) {
        container.innerHTML = '<p>No matches found.</p>';
        return;
    }

    const cols = [
        'match_id', 'date', 'season', 'league',
        'team_h', 'team_a', 'h_goals', 'a_goals',
        'h_xg', 'a_xg', 'h_shot', 'a_shot'
    ];
    
    let html = '<div class="dataset-grid">';
    html += '<div class="dataset-card results-container">';
    html += '<table class="results-table">';
    html += '<thead><tr>' + cols.map(c => 
        `<th>${c.replace(/_/g, ' ').toUpperCase()}</th>`
    ).join('') + '</tr></thead>';
    html += '<tbody>' + matches.map(m => {
        return '<tr>' + cols.map(c =>
            `<td>${m[c] ?? ''}</td>`
        ).join('') + '</tr>';
    }).join('') + '</tbody>';
    html += '</table></div></div>';
    
    container.innerHTML = html;
}

function collectFilters() {
    return {
        q: document.getElementById('q').value.trim(),
        season: document.getElementById('season').value,
        league: document.getElementById('league').value.trim(),
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
        min_goals: document.getElementById('min_goals').value,
        max_goals: document.getElementById('max_goals').value,
        min_xg: document.getElementById('min_xg').value,
        isResult: document.getElementById('is_result').value,
        team_home: document.getElementById('team_home').value,
        team_away: document.getElementById('team_away').value
    };
}

function populateTeamSelects(matches) {
    const teams = new Set();
    matches.forEach(m => {
        if (m.team_h) teams.add(m.team_h);
        if (m.team_a) teams.add(m.team_a);
    });
    
    const arr = Array.from(teams).sort();
    const home = document.getElementById('team_home');
    const away = document.getElementById('team_away');
    
    [home, away].forEach(s => {
        s.innerHTML = '<option value="">— any —</option>';
    });
    
    arr.forEach(t => {
        const o = `<option value="${t}">${t}</option>`;
        home.insertAdjacentHTML('beforeend', o);
        away.insertAdjacentHTML('beforeend', o);
    });
}

function populateSeasons(matches) {
    const seasons = new Set(matches.map(m => m.season).filter(Boolean));
    const sel = document.getElementById('season');
    sel.innerHTML = '<option value="">Any</option>';
    Array.from(seasons)
        .sort((a, b) => b - a)
        .forEach(s => sel.insertAdjacentHTML('beforeend',
            `<option value="${s}">${s}</option>`
        ));
}

async function doSearch() {
    try {
        const filters = collectFilters();
        const matches = await fetchMatches(filters);
        renderTable(matches);
    } catch (error) {
        console.error('Search failed:', error);
        document.getElementById('results').innerHTML = 
            '<p class="error">Error loading matches. Please try again.</p>';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', async () => {
    // Setup event listeners
    document.getElementById('btn_search')
        .addEventListener('click', async e => {
            e.preventDefault();
            await doSearch();
        });

    document.getElementById('btn_reset')
        .addEventListener('click', e => {
            e.preventDefault();
            // Reset all form fields
            [
                'q', 'season', 'league', 'date_from', 'date_to',
                'min_goals', 'max_goals', 'min_xg', 'is_result',
                'team_home', 'team_away'
            ].forEach(id => document.getElementById(id).value = '');
            // Load initial data
            doSearch();
        });

    document.getElementById('btn_team_headtohead')
        .addEventListener('click', async e => {
            e.preventDefault();
            const home = document.getElementById('team_home').value;
            const away = document.getElementById('team_away').value;
            
            if (!home || !away) {
                alert('Please select both home and away teams to show head-to-head matches.');
                return;
            }
            
            const filters = { team_home: home, team_away: away };
            try {
                const matches = await fetchMatches(filters);
                renderTable(matches);
            } catch (error) {
                console.error('H2H search failed:', error);
                document.getElementById('results').innerHTML = 
                    '<p class="error">Error loading head-to-head matches. Please try again.</p>';
            }
        });

    // Load initial data
    try {
        const initial = await fetchMatches({});
        populateTeamSelects(initial);
        populateSeasons(initial);
        renderTable(initial);
    } catch (error) {
        console.error('Initial load failed:', error);
        document.getElementById('results').innerHTML = 
            '<p class="error">Error loading initial data. Please refresh the page.</p>';
    }
});