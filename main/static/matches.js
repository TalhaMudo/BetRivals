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

function renderTable(matches, limit = 50) {
    const container = document.getElementById('results');
    if (!matches || matches.length === 0) {
        container.innerHTML = '<div class="no-results">No matches found.</div>';
        return;
    }

    //  build and render results table
    let html = '<div class="results-container">';
    html += '<div class="results-header"><h3>Search Results</h3>';
    html += '<div class="results-controls">';
    html += `<span class="results-count">${matches.length} matches</span>`;
    html += '<select class="limit-selector" onchange="updateLimit(this.value)">';
    html += '<option value="50"' + (limit === 50 ? ' selected' : '') + '>50 Matches</option>';
    html += '<option value="100"' + (limit === 100 ? ' selected' : '') + '>100 Matches</option>';
    html += '<option value="200"' + (limit === 200 ? ' selected' : '') + '>200 Matches</option>';
    html += '<option value="500"' + (limit === 500 ? ' selected' : '') + '>500 Matches</option>';
    html += '</select></div></div>';
    html += '<table class="results-table"><thead><tr>';
    html += ['HOME', 'SCORE', 'AWAY', 'SEASON', 'DATE'].map(h => `<th>${h}</th>`).join('');
    html += '</tr></thead><tbody>';
    html += matches.map(m => {
        const date = m.date ? new Date(m.date).toLocaleDateString() : '';
        const scoreHtml = `<div class="score-badge"><span class="home">${m.h_goals != null ? m.h_goals : '-'}</span><span class="sep">:</span><span class="away">${m.a_goals != null ? m.a_goals : '-'}</span></div>`;
        return `<tr class="result-row" onclick="window.location='/match/${m.match_id}'"><td>${m.team_h ?? ''}</td><td>${scoreHtml}</td><td>${m.team_a ?? ''}</td><td>${m.season ?? ''}</td><td>${date}</td></tr>`;
    }).join('');
    html += '</tbody></table></div>';

    container.innerHTML = html;
}

function collectFilters() {
    const filters = {
        q: document.getElementById('q').value.trim(),
        season: document.getElementById('season').value,
        date_from: document.getElementById('date_from').value || '',
        date_to: document.getElementById('date_to').value || '',
        min_goals: document.getElementById('min_goals').value || '',
        max_goals: document.getElementById('max_goals').value || '',
        min_xg: document.getElementById('min_xg').value || '',
        team_home: document.getElementById('team_home').value,
        team_away: document.getElementById('team_away').value,
        limit: 50
    };
    // remove empty string keys so backend only sees non-empty filters
    // this was working before, but after making the filters a sliding section. it just broke
    return Object.keys(filters).reduce((acc, key) => {
        if (filters[key] !== '' && filters[key] !== null) {
            acc[key] = filters[key];
        }
        return acc;
    }, {});
}

async function updateLimit(newLimit) {
    try {
        const filters = collectFilters();
        filters.limit = parseInt(newLimit);
        const matches = await fetchMatches(filters);
        renderTable(matches, filters.limit);
    } catch (error) {
        console.error('Update limit failed:', error);
    }
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
    
    window.allTeams = arr;
    setupTeamAutocomplete();
}

// custom autocomplete for team search
function setupTeamAutocomplete() {
    const input = document.getElementById('q');
    const list = document.getElementById('teamAutocomplete');
    if (!input || !list) return;
    
    let selectedIndex = -1;
    
    input.addEventListener('input', function() {
        const val = this.value.trim().toLowerCase();
        list.innerHTML = '';
        selectedIndex = -1;
        
        if (val.length < 2) {
            list.style.display = 'none';
            return;
        }
        
        const matches = window.allTeams.filter(t => 
            t.toLowerCase().includes(val)
        ).slice(0, 8);
        
        if (matches.length === 0) {
            list.style.display = 'none';
            return;
        }
        
        matches.forEach((team, idx) => {
            const li = document.createElement('li');
            li.textContent = team;
            li.dataset.index = idx;
            li.addEventListener('click', () => selectTeam(team));
            li.addEventListener('mouseenter', () => {
                selectedIndex = idx;
                updateSelection();
            });
            list.appendChild(li);
        });
        
        list.style.display = 'block';
    });
    
    input.addEventListener('keydown', function(e) {
        const items = list.querySelectorAll('li');
        if (items.length === 0) return;
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            updateSelection();
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            selectTeam(items[selectedIndex].textContent);
        } else if (e.key === 'Escape') {
            list.style.display = 'none';
        }
    });
    
    function updateSelection() {
        const items = list.querySelectorAll('li');
        items.forEach((item, idx) => {
            item.classList.toggle('selected', idx === selectedIndex);
        });
    }
    
    function selectTeam(team) {
        input.value = team;
        list.style.display = 'none';
        // Auto-search when team is selected
        doSearch();
    }
    
    // hide list when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.autocomplete-wrapper')) {
            list.style.display = 'none';
        }
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

// Event listeners
document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('btn_search').addEventListener('click', async e => {
        e.preventDefault();
        await doSearch();
    });

    document.getElementById('btn_reset').addEventListener('click', e => {
        e.preventDefault();
        ['q', 'season', 'date_from', 'date_to', 'min_goals', 'max_goals', 'min_xg', 'team_home', 'team_away']
            .forEach(id => document.getElementById(id).value = '');
        document.getElementById('results').innerHTML = '';
    });

    const advBtn = document.getElementById('btn_toggle_advanced');
    if (advBtn) {
        advBtn.addEventListener('click', e => {
            e.preventDefault();
            const adv = document.getElementById('advancedFilters');
            if (!adv) return;

            adv.style.display = 'grid';
            const opening = !adv.classList.contains('open');
            if (opening) {
                adv.classList.add('open');
                adv.setAttribute('aria-hidden', 'false');
                advBtn.setAttribute('aria-expanded', 'true');
                adv.style.maxHeight = adv.scrollHeight + 'px';
            } else {
                adv.style.maxHeight = adv.scrollHeight + 'px';
                void adv.offsetHeight;
                adv.style.maxHeight = '0px';
                adv.classList.remove('open');
                adv.setAttribute('aria-hidden', 'true');
                advBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    try {
        const initial = await fetchMatches({ limit: 5000 });
        populateTeamSelects(initial);
        populateSeasons(initial);
    } catch (error) {
        console.error('Failed to load team and season options:', error);
    }
});

// flatpickr date pickers
window.addEventListener('load', function() {
    setTimeout(function() {
        if (window.flatpickr) {
            flatpickr('#date_from', {
                mode: 'single',
                dateFormat: 'Y-m-d',
                disableMobile: false
            });
            
            flatpickr('#date_to', {
                mode: 'single',
                dateFormat: 'Y-m-d',
                disableMobile: false
            });
        }
    }, 100);
});