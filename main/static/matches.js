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
    // Rendering the matches into the results table
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

// Event Listeners will be added below

// bunun gibi

// document.getElementById('search_button').addEventListener('click', doSearch);