// Players Page JavaScript

document.addEventListener('DOMContentLoaded', function () {
    const btnAnalysis = document.getElementById('btn-analysis');
    const resultsDiv = document.getElementById('results');
    const searchInput = document.getElementById('player-search');
    const searchBtn = document.getElementById('search-btn');
    const filterBtn = document.getElementById('filter-btn');
    const filterPanel = document.getElementById('filter-panel');
    const filterApply = document.getElementById('filter-apply');
    const filterClear = document.getElementById('filter-clear');
    const filterYear = document.getElementById('filter-year');
    const filterTeam = document.getElementById('filter-team');
    const filterPosition = document.getElementById('filter-position');
    const searchResultsDiv = document.getElementById('search-results');
    const quoteTextEl = document.getElementById('quote-text');
    const quoteAuthorEl = document.getElementById('quote-author');

    // Load quote on page load
    loadQuote(quoteTextEl, quoteAuthorEl);

    // Load top assists on page load
    loadTopAssists();

    // Load top goals on page load
    loadTopGoals();

    // Add Player box (if present)
    const addBox = document.getElementById('add-player-box');
    if (addBox) {
        addBox.addEventListener('click', (e) => {
            // If it's an anchor, let normal navigation happen
            // but keep this for consistency if markup changes later.
            if (addBox.tagName !== 'A') {
                e.preventDefault();
                window.location.href = '/players/add';
            }
        });
    }

    // Edit Player box (if present)
    const editBox = document.getElementById('edit-player-box');
    if (editBox) {
        editBox.addEventListener('click', (e) => {
            if (editBox.tagName !== 'A') {
                e.preventDefault();
                window.location.href = '/players/edit';
            }
        });
    }

    // Init comparison floating button (every page)
    initComparisonButton();

    // Show All Players button
    if (btnAnalysis) {
        btnAnalysis.addEventListener('click', async function () {
            btnAnalysis.disabled = true;
            btnAnalysis.textContent = 'Loading...';
            resultsDiv.innerHTML = '<div class="loading">Loading players data</div>';

            try {
                const response = await fetch('/api/players/fut23');
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch data');
                }

                displayResults(data);

            } catch (error) {
                console.error('Error:', error);
                resultsDiv.innerHTML = `
                    <div class="error-message">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                btnAnalysis.disabled = false;
                btnAnalysis.textContent = '👥 Show All Players';
            }
        });
    }

    // Search functionality
    if (searchBtn && searchInput) {
        const performSearch = async () => {
            const query = searchInput.value.trim();
            if (!query) {
                searchResultsDiv.innerHTML = '';
                return;
            }

            searchBtn.disabled = true;
            searchResultsDiv.innerHTML = '<div class="loading">Searching players...</div>';

            try {
                const params = new URLSearchParams();
                params.set('q', query);
                const yearVal = filterYear ? filterYear.value.trim() : '';
                const teamVal = filterTeam ? filterTeam.value.trim() : '';
                const posVal = filterPosition ? filterPosition.value.trim() : '';
                if (yearVal) params.set('year', yearVal);
                if (teamVal) params.set('team', teamVal);
                if (posVal) params.set('position', posVal);

                const response = await fetch(`/api/players/search?${params.toString()}`);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to search players');
                }

                displaySearchResults(data);

            } catch (error) {
                console.error('Error:', error);
                searchResultsDiv.innerHTML = `
                    <div class="error-message">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                searchBtn.disabled = false;
            }
        };

        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });

        // Filter panel toggle + actions
        const toggleFilter = (show) => {
            if (!filterPanel) return;
            filterPanel.classList.toggle('hidden', !show);
        };

        if (filterBtn && filterPanel) {
            filterBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const isHidden = filterPanel.classList.contains('hidden');
                toggleFilter(isHidden);
            });

            // Close when clicking outside
            document.addEventListener('click', (e) => {
                if (!filterPanel || !filterBtn) return;
                const target = e.target;
                if (filterPanel.contains(target) || filterBtn.contains(target)) return;
                toggleFilter(false);
            });
        }

        if (filterApply) {
            filterApply.addEventListener('click', () => {
                toggleFilter(false);
                performSearch();
            });
        }

        if (filterClear) {
            filterClear.addEventListener('click', () => {
                if (filterYear) filterYear.value = '';
                if (filterTeam) filterTeam.value = '';
                if (filterPosition) filterPosition.value = '';
                toggleFilter(false);
                performSearch();
            });
        }
    }

    // Complex Query Buttons
    const queryButtons = document.querySelectorAll('.query-btn');
    queryButtons.forEach(btn => {
        btn.addEventListener('click', async function () {
            const endpoint = this.getAttribute('data-endpoint');
            const originalText = this.textContent;

            // Disable all query buttons
            queryButtons.forEach(b => b.disabled = true);
            this.textContent = 'Loading...';
            resultsDiv.innerHTML = '<div class="loading">Executing query and building dashboard</div>';

            try {
                const response = await fetch(endpoint);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to execute query');
                }

                // Use displayAnalysisResults for complex queries
                // Pass endpoint to detect Query 5
                displayAnalysisResults(data, endpoint);

            } catch (error) {
                console.error('Error:', error);
                resultsDiv.innerHTML = `
                    <div class="error-message">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                // Re-enable all query buttons
                queryButtons.forEach(b => b.disabled = false);
                this.textContent = originalText;
            }
        });
    });
});

// --- Comparison helpers ---
const COMPARE_MAIN_STATS = ['goals', 'assists', 'games', 'xG', 'shots', 'key_passes', 'time', 'yellow_cards', 'red_cards'];
const COMPARE_FIFA_STATS = ['Rating', 'Pace', 'Shoot', 'Pass', 'Drible', 'Defense', 'Physical', 'Skill', 'Weak_foot'];
const LOWER_BETTER = new Set(['yellow_cards', 'red_cards']);

async function getCompareList() {
    const resp = await fetch('/api/players/compare/list');
    const data = await resp.json();
    return data.players || [];
}

async function addToCompare(playerId) {
    const resp = await fetch(`/api/players/compare/add/${playerId}`, { method: 'POST' });
    return resp.json();
}

async function removeFromCompare(playerId) {
    const resp = await fetch(`/api/players/compare/remove/${playerId}`, { method: 'POST' });
    return resp.json();
}

function initComparisonButton() {
    if (document.getElementById('compare-float-btn')) return; // already added

    const btn = document.createElement('div');
    btn.id = 'compare-float-btn';
    btn.className = 'compare-float-btn';
    btn.innerHTML = `<span class="compare-count">0</span>`;

    const popup = document.createElement('div');
    popup.id = 'compare-popup';
    popup.className = 'compare-popup hidden';
    popup.innerHTML = `
        <div class="compare-popup-header">
            <span>Comparison List</span>
            <button id="compare-close" class="compare-close">✕</button>
        </div>
        <div class="compare-list" id="compare-list"></div>
        <div class="compare-popup-actions">
            <button id="compare-go" class="btn-compare" disabled>Compare</button>
        </div>
    `;

    document.body.appendChild(btn);
    document.body.appendChild(popup);

    const togglePopup = (show) => {
        popup.classList.toggle('hidden', !show);
    };

    btn.addEventListener('click', () => togglePopup(true));
    popup.querySelector('#compare-close').addEventListener('click', () => togglePopup(false));
    popup.querySelector('#compare-go').addEventListener('click', () => {
        window.location.href = '/players/compare';
    });

    refreshCompareUI();
}

async function refreshCompareUI() {
    const listEl = document.getElementById('compare-list');
    const countEl = document.querySelector('#compare-float-btn .compare-count');
    const goBtn = document.getElementById('compare-go');
    if (!listEl || !countEl || !goBtn) return;

    try {
        const list = await getCompareList();
        countEl.textContent = list.length;
        listEl.innerHTML = list.length === 0 ? '<div class="empty">No players added</div>' : '';

        if (list.length > 0) {
            // Fetch player data to get names
            const dataResp = await fetch('/api/players/compare/data');
            const data = await dataResp.json();
            const players = data.players || [];

            // Create a map of player_id to player_name
            const playerMap = {};
            players.forEach(p => {
                playerMap[p.player_id] = p.player_name || `Player #${p.player_id}`;
            });

            list.forEach(pid => {
                const row = document.createElement('div');
                row.className = 'compare-row';
                const playerName = playerMap[pid] || `Player #${pid}`;
                row.innerHTML = `
                    <span class="compare-name">${playerName}</span>
                    <button class="compare-remove" data-pid="${pid}" title="Remove from comparison">−</button>
                `;
                listEl.appendChild(row);
            });

            listEl.querySelectorAll('.compare-remove').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const pid = e.target.getAttribute('data-pid');
                    await removeFromCompare(pid);
                    refreshCompareUI();
                    updateCompareButtonsState(pid);
                });
            });
        }

        goBtn.disabled = list.length === 0;
    } catch (e) {
        listEl.innerHTML = '<div class="empty">Error loading list</div>';
        console.error(e);
    }
}

// --- Quotes ---
async function loadQuote(quoteTextEl, quoteAuthorEl) {
    if (!quoteTextEl || !quoteAuthorEl) return;
    quoteTextEl.textContent = 'Loading quote...';
    quoteAuthorEl.textContent = '';
    try {
        const response = await fetch('/api/quotes/random');
        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to fetch quote');
        }
        quoteTextEl.textContent = data.quote || 'No quote available';
        quoteAuthorEl.textContent = data.author ? `— ${data.author}` : '';
    } catch (err) {
        console.error('Quote fetch error:', err);
        quoteTextEl.textContent = 'Could not load quote right now.';
        quoteAuthorEl.textContent = '';
    }
}

// --- Top Assists ---
async function loadTopAssists() {
    const box = document.getElementById('top-assists-box');
    if (!box) return;

    try {
        const response = await fetch('/api/players/top/assists');
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to fetch top assists');
        }

        const players = data.players || [];
        if (players.length === 0) {
            box.innerHTML = '<h3>Top Assists</h3><div class="empty">No data available</div>';
            return;
        }

        let html = '<h3>Top Assists</h3><div class="top-assists-list">';
        players.forEach((player, index) => {
            html += `
                <div class="top-assist-item" onclick="window.location.href='/players/${player.player_id}'" style="cursor: pointer;">
                    <div class="top-assist-rank">#${index + 1}</div>
                    <div class="top-assist-photo">
                        <div class="player-photo-placeholder" data-player-name="${player.player_name || ''}">
                            <span>📷</span>
                            <small>Loading...</small>
                        </div>
                    </div>
                    <div class="top-assist-info">
                        <div class="top-assist-name">${player.player_name || 'Unknown'}</div>
                        <div class="top-assist-stats">
                            <span class="assists-count">${player.assists || 0} assists</span>
                            ${player.team_title ? `<span class="team-name">${player.team_title}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        box.innerHTML = html;

        // Load player photos
        loadTopAssistsPhotos();
    } catch (err) {
        console.error('Top assists fetch error:', err);
        box.innerHTML = '<h3>Top Assists</h3><div class="empty">Could not load data</div>';
    }
}

async function loadTopAssistsPhotos() {
    const placeholders = document.querySelectorAll('#top-assists-box .player-photo-placeholder');
    if (!placeholders || placeholders.length === 0) return;

    for (const placeholder of placeholders) {
        const playerName = placeholder.getAttribute('data-player-name');
        if (!playerName) continue;

        try {
            const imageUrl = await fetchUnsplashPlayerImageUrl(playerName);
            if (!imageUrl) continue;

            placeholder.style.backgroundImage = `url('${imageUrl}')`;
            placeholder.style.backgroundSize = 'cover';
            placeholder.style.backgroundPosition = 'center';
            placeholder.style.border = 'none';
            placeholder.innerHTML = '';
        } catch (error) {
            console.error('Error loading photo for top assists:', error);
        }
    }
}

// --- Top Goals ---
async function loadTopGoals() {
    const box = document.getElementById('top-goals-box');
    if (!box) return;

    try {
        const response = await fetch('/api/players/top/goals');
        const data = await response.json();

        if (!response.ok || data.error || !data.player) {
            throw new Error(data.error || 'Failed to fetch top goals');
        }

        const player = data.player;
        const html = `
            <h3>Top Goals</h3>
            <div class="top-goals-player" onclick="window.location.href='/players/${player.player_id}'" style="cursor: pointer;">
                <div class="top-goals-photo">
                    <div class="player-photo-placeholder" data-player-name="${player.player_name || ''}">
                        <span>📷</span>
                        <small>Loading...</small>
                    </div>
                </div>
                <div class="top-goals-info">
                    <div class="top-goals-name">${player.player_name || 'Unknown'}</div>
                    <div class="top-goals-count">${player.goals || 0} goals</div>
                    ${player.team_title ? `<div class="top-goals-team">${player.team_title}</div>` : ''}
                </div>
            </div>
        `;
        box.innerHTML = html;

        // Load player photo
        const placeholder = box.querySelector('.player-photo-placeholder');
        if (placeholder && player.player_name) {
            try {
                const imageUrl = await fetchUnsplashPlayerImageUrl(player.player_name);
                if (imageUrl) {
                    placeholder.style.backgroundImage = `url('${imageUrl}')`;
                    placeholder.style.backgroundSize = 'cover';
                    placeholder.style.backgroundPosition = 'center';
                    placeholder.style.border = 'none';
                    placeholder.innerHTML = '';
                }
            } catch (error) {
                console.error('Error loading photo for top goals:', error);
            }
        }
    } catch (err) {
        console.error('Top goals fetch error:', err);
        box.innerHTML = '<h3>Top Goals</h3><div class="empty">Could not load data</div>';
    }
}

function displayAnalysisResults(data, endpoint = '') {
    const resultsDiv = document.getElementById('results');

    if (!data.players || data.players.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No players found in the database.</div>';
        return;
    }

    // Check if this is Query 5 (comprehensive-stats)
    const isQuery5 = endpoint.includes('comprehensive-stats') ||
        (data.players[0] && 'position_avg_goals' in data.players[0] && 'total_shots' in data.players[0]);

    if (isQuery5) {
        displayQuery5Dashboard(data);
        return;
    }

    // Store original data for sorting
    let playersData = data.players.map((player, index) => ({
        ...player,
        originalIndex: index + 1
    }));
    let currentSort = { column: null, direction: null };

    // Column definitions for sorting - dynamically detect columns from data
    const firstPlayer = data.players[0] || {};
    const allKeys = Object.keys(firstPlayer);

    // Define preferred column order
    const preferredOrder = [
        'originalIndex', 'player_name', 'team_title', 'position',
        'goals', 'assists', 'games', 'xG', 'goals_per_game', 'position_avg_goals',
        'fifa_rating', 'Pace', 'Shoot', 'Pass', 'Defense', 'Physical', 'year', 'total_shots'
    ];

    // Map keys to labels
    const keyToLabel = {
        'originalIndex': 'Rank',
        'player_name': 'Player Name',
        'team_title': 'Team',
        'position': 'Position',
        'goals': 'Goals',
        'assists': 'Assists',
        'games': 'Games',
        'xG': 'xG',
        'goals_per_game': 'Goals/Game',
        'position_avg_goals': 'Position Avg Goals',
        'fifa_rating': 'FIFA Rating',
        'Pace': 'Pace',
        'Shoot': 'Shoot',
        'Pass': 'Pass',
        'Defense': 'Defense',
        'Physical': 'Physical',
        'year': 'Year',
        'total_shots': 'Total Shots'
    };

    // Build columns array
    const columns = preferredOrder
        .filter(key => allKeys.includes(key))
        .map(key => ({
            key: key,
            label: keyToLabel[key] || key,
            type: typeof firstPlayer[key] === 'number' ? 'number' : 'string'
        }));

    // Add any remaining columns not in preferred order
    allKeys.forEach(key => {
        if (!preferredOrder.includes(key) && key !== 'originalIndex') {
            columns.push({
                key: key,
                label: keyToLabel[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                type: typeof firstPlayer[key] === 'number' ? 'number' : 'string'
            });
        }
    });

    // Sort function
    function sortTable(columnKey, columnType) {
        if (currentSort.column === columnKey) {
            // Toggle direction
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.column = columnKey;
            currentSort.direction = 'asc';
        }

        playersData.sort((a, b) => {
            let aVal = a[columnKey];
            let bVal = b[columnKey];

            // Handle null/undefined values
            if (aVal === null || aVal === undefined || aVal === '-') aVal = columnType === 'number' ? -Infinity : '';
            if (bVal === null || bVal === undefined || bVal === '-') bVal = columnType === 'number' ? -Infinity : '';

            if (columnType === 'number') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            } else {
                aVal = String(aVal).toLowerCase();
                bVal = String(bVal).toLowerCase();
            }

            if (currentSort.direction === 'asc') {
                return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
            } else {
                return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
            }
        });

        renderTable();
    }

    // Render table function
    function renderTable() {
        const sortIndicator = (colKey) => {
            if (currentSort.column === colKey) {
                return currentSort.direction === 'asc' ? ' ↑' : ' ↓';
            }
            return '';
        };

        const tableHTML = `
            <div class="results-container">
                <div class="results-header">
                    <span>⚽</span>
                    <span>${data.description || 'Player Analysis'}</span>
                </div>
                <div class="results-count">Showing ${data.count} players${currentSort.column ? ` (sorted by: ${columns.find(c => c.key === currentSort.column)?.label} ${currentSort.direction === 'asc' ? '↑' : '↓'})` : ''}</div>
                <div class="players-table">
                    <table>
                        <thead>
                            <tr>
                                ${columns.map(col => `
                                    <th class="sortable" data-column="${col.key}" data-type="${col.type}">
                                        ${col.label}${sortIndicator(col.key)}
                                    </th>
                                `).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${playersData.map((player) => {
            const formatValue = (key, value) => {
                if (value === null || value === undefined) return '-';
                if (key === 'originalIndex') return `<strong>#${value}</strong>`;
                if (key === 'player_name') return `<strong>${value}</strong>`;
                if (key === 'goals') return `<span style="color: #2ecc71; font-weight: 700;">${value}</span>`;
                if (key === 'fifa_rating') return `<span style="color: #e74c3c; font-weight: 700;">${value}</span>`;
                if (key === 'xG' || key === 'goals_per_game' || key === 'position_avg_goals') {
                    return typeof value === 'number' ? value.toFixed(2) : value;
                }
                return value;
            };
            return `
                                    <tr>
                                        ${columns.map(col => `<td>${formatValue(col.key, player[col.key])}</td>`).join('')}
                                    </tr>
                                `;
        }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        resultsDiv.innerHTML = tableHTML;

        // Add click event listeners to sortable headers
        document.querySelectorAll('.sortable').forEach(header => {
            header.addEventListener('click', () => {
                const columnKey = header.getAttribute('data-column');
                const columnType = header.getAttribute('data-type');
                sortTable(columnKey, columnType);
            });
        });
    }

    // Initial render
    renderTable();
}

// Query 5 Dashboard Visualization
function displayQuery5Dashboard(data) {
    const resultsDiv = document.getElementById('results');
    const players = data.players || [];

    if (players.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No players found in the database.</div>';
        return;
    }

    // Prepare data
    const playersData = players.map((p, idx) => ({
        ...p,
        goals: parseFloat(p.goals) || 0,
        assists: parseFloat(p.assists) || 0,
        games: parseFloat(p.games) || 0,
        xG: parseFloat(p.xG) || 0,
        goals_per_game: parseFloat(p.goals_per_game) || 0,
        position_avg_goals: parseFloat(p.position_avg_goals) || 0,
        fifa_rating: parseFloat(p.fifa_rating) || 0,
        Pace: parseFloat(p.Pace) || 0,
        Shoot: parseFloat(p.Shoot) || 0,
        Pass: parseFloat(p.Pass) || 0,
        Defense: parseFloat(p.Defense) || 0,
        Physical: parseFloat(p.Physical) || 0,
        total_shots: parseFloat(p.total_shots) || 0,
        performance_ratio: p.position_avg_goals > 0 ? (p.goals / p.position_avg_goals) : 0
    }));

    // Create dashboard HTML
    const dashboardHTML = `
        <div class="query5-dashboard">
            <div class="dashboard-header">
                <h2>📊 Comprehensive Player Stats Dashboard</h2>
                <p class="dashboard-description">${data.description || 'Top players with stats vs position averages'}</p>
                <div class="dashboard-stats-summary">
                    <span class="stat-badge">${data.count} Players</span>
                    <span class="stat-badge">${new Set(playersData.map(p => p.position)).size} Positions</span>
                    <span class="stat-badge">${new Set(playersData.map(p => p.team_title)).size} Teams</span>
                </div>
            </div>

            <div class="dashboard-controls">
                <div class="control-group">
                    <label>Filter by Position:</label>
                    <select id="position-filter" class="dashboard-select">
                        <option value="">All Positions</option>
                        ${Array.from(new Set(playersData.map(p => p.position).filter(Boolean))).sort().map(pos =>
        `<option value="${pos}">${pos}</option>`
    ).join('')}
                    </select>
                </div>
                <div class="control-group">
                    <label>View:</label>
                    <div class="view-toggle">
                        <button class="view-btn active" data-view="scatter">Scatter</button>
                        <button class="view-btn" data-view="radar">Radar</button>
                        <button class="view-btn" data-view="bar">Bar Chart</button>
                        <button class="view-btn" data-view="cards">Cards</button>
                    </div>
                </div>
            </div>

            <div class="dashboard-content">
                <div class="chart-container active" id="scatter-chart-container">
                    <div class="chart-header">
                        <h3>Performance vs Position Average</h3>
                        <p>Goals vs Position Average Goals (colored by FIFA Rating, sized by Total Shots)</p>
                    </div>
                    <canvas id="scatter-chart"></canvas>
                </div>

                <div class="chart-container" id="radar-chart-container">
                    <div class="chart-header">
                        <h3>FIFA Attributes Comparison</h3>
                        <p>Compare FIFA attributes across top players</p>
                        <div class="radar-controls">
                            <label>Select Players (max 5):</label>
                            <div id="radar-player-selector"></div>
                        </div>
                    </div>
                    <canvas id="radar-chart"></canvas>
                </div>

                <div class="chart-container" id="bar-chart-container">
                    <div class="chart-header">
                        <h3>Top Performers by Goals</h3>
                        <p>Top 20 players with position average reference line</p>
                    </div>
                    <canvas id="bar-chart"></canvas>
                </div>

                <div class="chart-container" id="cards-container">
                    <div class="chart-header">
                        <h3>Player Performance Cards</h3>
                        <p>Detailed view of each player's performance metrics</p>
                    </div>
                    <div id="player-cards-grid" class="player-cards-grid"></div>
                </div>
            </div>
        </div>
    `;

    resultsDiv.innerHTML = dashboardHTML;

    // Initialize charts
    initializeScatterChart(playersData);
    initializeRadarChart(playersData);
    initializeBarChart(playersData);
    renderPlayerCards(playersData);

    // Setup controls
    setupDashboardControls(playersData);
}

// Initialize Scatter Plot
function initializeScatterChart(playersData) {
    const ctx = document.getElementById('scatter-chart');
    if (!ctx) return;

    // Prepare scatter data
    const scatterData = playersData.map(p => ({
        x: p.position_avg_goals,
        y: p.goals,
        label: p.player_name,
        rating: p.fifa_rating,
        shots: p.total_shots,
        team: p.team_title,
        position: p.position,
        goals_per_game: p.goals_per_game
    }));

    // Color scale based on FIFA rating
    const maxRating = Math.max(...scatterData.map(d => d.rating));
    const minRating = Math.min(...scatterData.map(d => d.rating));

    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Players',
                data: scatterData,
                backgroundColor: scatterData.map(d => {
                    const ratio = (d.rating - minRating) / (maxRating - minRating || 1);
                    const hue = ratio * 120; // Green to red
                    return `hsla(${hue}, 70%, 50%, 0.7)`;
                }),
                borderColor: scatterData.map(d => {
                    const ratio = (d.rating - minRating) / (maxRating - minRating || 1);
                    const hue = ratio * 120;
                    return `hsla(${hue}, 80%, 40%, 1)`;
                }),
                borderWidth: 2,
                pointRadius: scatterData.map(d => Math.max(5, Math.min(15, d.shots / 10))),
                pointHoverRadius: scatterData.map(d => Math.max(8, Math.min(20, d.shots / 8)))
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const point = context.raw;
                            return [
                                `Player: ${point.label}`,
                                `Team: ${point.team || 'N/A'}`,
                                `Position: ${point.position || 'N/A'}`,
                                `Goals: ${point.y}`,
                                `Position Avg: ${point.x.toFixed(2)}`,
                                `FIFA Rating: ${point.rating}`,
                                `Goals/Game: ${point.goals_per_game.toFixed(2)}`,
                                `Total Shots: ${point.shots}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Position Average Goals',
                        color: '#2ecc71',
                        font: { size: 14, weight: 'bold' }
                    },
                    ticks: { color: '#b8b8b8' },
                    grid: { color: 'rgba(46, 204, 113, 0.1)' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Player Goals',
                        color: '#2ecc71',
                        font: { size: 14, weight: 'bold' }
                    },
                    ticks: { color: '#b8b8b8' },
                    grid: { color: 'rgba(46, 204, 113, 0.1)' }
                }
            }
        }
    });
}

// Initialize Radar Chart
function initializeRadarChart(playersData) {
    const ctx = document.getElementById('radar-chart');
    if (!ctx) return;

    // Select top 5 players by goals for default display
    const topPlayers = [...playersData]
        .sort((a, b) => b.goals - a.goals)
        .slice(0, 5)
        .filter(p => p.fifa_rating > 0);

    if (topPlayers.length === 0) {
        ctx.parentElement.innerHTML = '<p class="no-data">No FIFA rating data available</p>';
        return;
    }

    const radarData = {
        labels: ['Pace', 'Shoot', 'Pass', 'Defense', 'Physical', 'Rating'],
        datasets: topPlayers.map((player, idx) => {
            const colors = [
                'rgba(46, 204, 113, 0.6)',
                'rgba(52, 152, 219, 0.6)',
                'rgba(155, 89, 182, 0.6)',
                'rgba(241, 196, 15, 0.6)',
                'rgba(231, 76, 60, 0.6)'
            ];
            return {
                label: player.player_name,
                data: [
                    player.Pace || 0,
                    player.Shoot || 0,
                    player.Pass || 0,
                    player.Defense || 0,
                    player.Physical || 0,
                    player.fifa_rating || 0
                ],
                backgroundColor: colors[idx % colors.length],
                borderColor: colors[idx % colors.length].replace('0.6', '1'),
                borderWidth: 2,
                pointBackgroundColor: colors[idx % colors.length],
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: colors[idx % colors.length]
            };
        })
    };

    // Create player selector
    const selector = document.getElementById('radar-player-selector');
    if (selector) {
        selector.innerHTML = playersData
            .filter(p => p.fifa_rating > 0)
            .slice(0, 10)
            .map((p, idx) => `
                <label class="radar-checkbox-label">
                    <input type="checkbox" class="radar-player-check" 
                           value="${idx}" data-player-idx="${idx}" 
                           ${idx < 5 ? 'checked' : ''}>
                    <span>${p.player_name}</span>
                </label>
            `).join('');
    }

    const radarChart = new Chart(ctx, {
        type: 'radar',
        data: radarData,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#b8b8b8',
                        font: { size: 12 },
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: ${context.parsed.r}`;
                        }
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: '#b8b8b8',
                        backdropColor: 'transparent'
                    },
                    grid: {
                        color: 'rgba(46, 204, 113, 0.2)'
                    },
                    pointLabels: {
                        color: '#2ecc71',
                        font: { size: 12, weight: 'bold' }
                    }
                }
            }
        }
    });

    // Update radar chart when checkboxes change
    if (selector) {
        selector.addEventListener('change', (e) => {
            if (e.target.classList.contains('radar-player-check')) {
                updateRadarChart(radarChart, playersData, e);
            }
        });
    }
}

// Update Radar Chart based on selected players
function updateRadarChart(chart, playersData, event = null) {
    const checkboxes = document.querySelectorAll('.radar-player-check:checked');
    if (checkboxes.length === 0 || checkboxes.length > 5) {
        if (checkboxes.length > 5 && event) {
            alert('Maximum 5 players can be compared at once');
            event.target.checked = false;
        }
        return;
    }

    const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.playerIdx));
    const selectedPlayers = playersData
        .filter(p => p.fifa_rating > 0)
        .filter((p, idx) => selectedIndices.includes(idx))
        .slice(0, 5);

    const colors = [
        'rgba(46, 204, 113, 0.6)',
        'rgba(52, 152, 219, 0.6)',
        'rgba(155, 89, 182, 0.6)',
        'rgba(241, 196, 15, 0.6)',
        'rgba(231, 76, 60, 0.6)'
    ];

    chart.data.datasets = selectedPlayers.map((player, idx) => ({
        label: player.player_name,
        data: [
            player.Pace || 0,
            player.Shoot || 0,
            player.Pass || 0,
            player.Defense || 0,
            player.Physical || 0,
            player.fifa_rating || 0
        ],
        backgroundColor: colors[idx % colors.length],
        borderColor: colors[idx % colors.length].replace('0.6', '1'),
        borderWidth: 2,
        pointBackgroundColor: colors[idx % colors.length],
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: colors[idx % colors.length]
    }));

    chart.update();
}

// Initialize Bar Chart
function initializeBarChart(playersData) {
    const ctx = document.getElementById('bar-chart');
    if (!ctx) return;

    // Top 20 players by goals
    const top20 = [...playersData]
        .sort((a, b) => b.goals - a.goals)
        .slice(0, 20);

    const avgGoals = top20.reduce((sum, p) => sum + p.position_avg_goals, 0) / top20.length;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top20.map(p => p.player_name),
            datasets: [
                {
                    label: 'Player Goals',
                    data: top20.map(p => p.goals),
                    backgroundColor: top20.map(p => {
                        const ratio = p.goals_per_game / Math.max(...top20.map(t => t.goals_per_game));
                        return `rgba(46, 204, 113, ${0.5 + ratio * 0.5})`;
                    }),
                    borderColor: '#2ecc71',
                    borderWidth: 2
                },
                {
                    label: 'Position Average Goals',
                    data: top20.map(p => p.position_avg_goals),
                    type: 'line',
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#b8b8b8',
                        font: { size: 12 },
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const player = top20[context.dataIndex];
                            if (context.datasetIndex === 0) {
                                return [
                                    `Goals: ${context.parsed.x}`,
                                    `Goals/Game: ${player.goals_per_game.toFixed(2)}`,
                                    `Team: ${player.team_title || 'N/A'}`,
                                    `Position: ${player.position || 'N/A'}`
                                ];
                            } else {
                                return `Position Avg: ${context.parsed.x.toFixed(2)}`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Goals',
                        color: '#2ecc71',
                        font: { size: 14, weight: 'bold' }
                    },
                    ticks: { color: '#b8b8b8' },
                    grid: { color: 'rgba(46, 204, 113, 0.1)' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Players',
                        color: '#2ecc71',
                        font: { size: 14, weight: 'bold' }
                    },
                    ticks: { color: '#b8b8b8' },
                    grid: { color: 'rgba(46, 204, 113, 0.1)' }
                }
            }
        }
    });
}

// Render Player Cards
function renderPlayerCards(playersData) {
    const container = document.getElementById('player-cards-grid');
    if (!container) return;

    const cardsHTML = playersData.map(player => {
        const overPerformer = player.goals > player.position_avg_goals;
        const performanceDiff = ((player.goals - player.position_avg_goals) / (player.position_avg_goals || 1) * 100).toFixed(1);

        return `
            <div class="player-performance-card" onclick="window.location.href='/players/${player.player_id || '#'}'">
                <div class="card-header">
                    <h4 class="card-player-name">${player.player_name || 'Unknown'}</h4>
                    ${player.fifa_rating ? `<span class="card-rating-badge">${player.fifa_rating}</span>` : ''}
                </div>
                <div class="card-team-position">
                    <span class="card-team">${player.team_title || 'N/A'}</span>
                    <span class="card-position">${player.position || 'N/A'}</span>
                </div>
                <div class="card-stats-grid">
                    <div class="card-stat">
                        <span class="stat-label">Goals</span>
                        <span class="stat-value goals-value">${player.goals}</span>
                    </div>
                    <div class="card-stat">
                        <span class="stat-label">Assists</span>
                        <span class="stat-value">${player.assists}</span>
                    </div>
                    <div class="card-stat">
                        <span class="stat-label">Games</span>
                        <span class="stat-value">${player.games}</span>
                    </div>
                    <div class="card-stat">
                        <span class="stat-label">Goals/Game</span>
                        <span class="stat-value">${player.goals_per_game.toFixed(2)}</span>
                    </div>
                </div>
                <div class="card-position-comparison">
                    <div class="comparison-label">
                        <span>Position Avg: ${player.position_avg_goals.toFixed(2)}</span>
                        <span class="comparison-indicator ${overPerformer ? 'over' : 'under'}">
                            ${overPerformer ? '↑' : '↓'} ${Math.abs(performanceDiff)}%
                        </span>
                    </div>
                    <div class="comparison-bar">
                        <div class="comparison-bar-fill" style="width: ${Math.min(100, (player.goals / Math.max(player.position_avg_goals, player.goals) * 100))}%"></div>
                    </div>
                </div>
                ${player.total_shots > 0 ? `
                    <div class="card-shots">
                        <span>Total Shots: ${player.total_shots}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');

    container.innerHTML = cardsHTML;
}

// Setup Dashboard Controls
function setupDashboardControls(playersData) {
    // View toggle
    const viewButtons = document.querySelectorAll('.view-btn');
    const chartContainers = document.querySelectorAll('.chart-container');

    viewButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;

            // Update active button
            viewButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Show/hide containers
            chartContainers.forEach(container => {
                container.classList.remove('active');
            });

            const targetContainer = document.getElementById(`${view}-chart-container`) ||
                document.getElementById(`${view}-container`);
            if (targetContainer) {
                targetContainer.classList.add('active');
            }
        });
    });

    // Position filter
    const positionFilter = document.getElementById('position-filter');
    if (positionFilter) {
        positionFilter.addEventListener('change', (e) => {
            const selectedPosition = e.target.value;
            const filtered = selectedPosition
                ? playersData.filter(p => p.position === selectedPosition)
                : playersData;

            // Re-render charts with filtered data
            initializeScatterChart(filtered);
            initializeBarChart(filtered);
            renderPlayerCards(filtered);
        });
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');

    if (!data.players || data.players.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No players found in the database.</div>';
        return;
    }

    // Define preferred column order (most important first)
    const preferredOrder = [
        'Name', 'player_id', 'Rating', 'Position', 'Team', 'League', 'Country',
        'Pace', 'Shoot', 'Pass', 'Drible', 'Defense', 'Physical',
        'Skill', 'Weak_foot', 'Other_Positions', 'Run_type',
        'Height_cm', 'Weight', 'Body_type',
        'Attack_rate', 'Defense_rate', 'Price', 'Popularity',
        'Base_Stats', 'In_Game_Stats', 'team_id'
    ];

    // Get all column names from the first player object
    const allColumns = Object.keys(data.players[0]);

    // Reorder columns: preferred first, then any remaining columns
    const columns = [
        ...preferredOrder.filter(col => allColumns.includes(col)),
        ...allColumns.filter(col => !preferredOrder.includes(col))
    ];

    // Store original data for sorting and reset
    const originalData = [...data.players];
    let playersData = [...data.players];
    let currentSort = { column: null, direction: null };

    // Detect column type (number or string)
    function detectColumnType(columnKey) {
        const sampleValue = playersData[0]?.[columnKey];
        if (sampleValue === null || sampleValue === undefined || sampleValue === '-') {
            // Check other rows
            for (let i = 1; i < Math.min(10, playersData.length); i++) {
                const val = playersData[i]?.[columnKey];
                if (val !== null && val !== undefined && val !== '-') {
                    return !isNaN(parseFloat(val)) ? 'number' : 'string';
                }
            }
            return 'string'; // default
        }
        return !isNaN(parseFloat(sampleValue)) ? 'number' : 'string';
    }

    // Sort function with reset option (third click resets)
    function sortTable(columnKey, columnType) {
        if (currentSort.column === columnKey) {
            if (currentSort.direction === 'asc') {
                // Second click: change to desc
                currentSort.direction = 'desc';
            } else {
                // Third click: reset to original order
                currentSort.column = null;
                currentSort.direction = null;
                playersData = [...originalData];
                renderTable();
                return;
            }
        } else {
            currentSort.column = columnKey;
            currentSort.direction = 'asc';
        }

        playersData.sort((a, b) => {
            let aVal = a[columnKey];
            let bVal = b[columnKey];

            // Handle null/undefined values
            if (aVal === null || aVal === undefined || aVal === '-') aVal = columnType === 'number' ? -Infinity : '';
            if (bVal === null || bVal === undefined || bVal === '-') bVal = columnType === 'number' ? -Infinity : '';

            if (columnType === 'number') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            } else {
                aVal = String(aVal).toLowerCase();
                bVal = String(bVal).toLowerCase();
            }

            if (currentSort.direction === 'asc') {
                return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
            } else {
                return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
            }
        });

        renderTable();
    }

    // Render table function
    function renderTable() {
        const sortIndicator = (colKey) => {
            if (currentSort.column === colKey) {
                return currentSort.direction === 'asc' ? ' ↑' : ' ↓';
            }
            return '';
        };

        const tableHTML = `
            <div class="results-container">
                <div class="results-header">
                    <span>👥</span>
                    <span>All Players</span>
                </div>
                <div class="results-count">Total players: ${data.count}${currentSort.column ? ` (sorted by: ${currentSort.column} ${currentSort.direction === 'asc' ? '↑' : '↓'})` : ' (unsorted)'}</div>
                <div class="players-table">
                    <table>
                        <thead>
                            <tr>
                                ${columns.map(col => {
            const colType = detectColumnType(col);
            return `<th class="sortable" data-column="${col}" data-type="${colType}">${col}${sortIndicator(col)}</th>`;
        }).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${playersData.map(player => `
                                <tr class="player-row" data-player-id="${player.player_id || ''}" style="cursor: pointer;">
                                    ${columns.map(col => `<td>${player[col] !== null && player[col] !== undefined ? player[col] : '-'}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        resultsDiv.innerHTML = tableHTML;

        // Add click event listeners to sortable headers
        document.querySelectorAll('.sortable').forEach(header => {
            header.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent row click when clicking header
                const columnKey = header.getAttribute('data-column');
                const columnType = header.getAttribute('data-type');
                sortTable(columnKey, columnType);
            });
        });

        // Add click event listeners to player rows
        document.querySelectorAll('.player-row').forEach(row => {
            row.addEventListener('click', () => {
                const playerId = row.getAttribute('data-player-id');
                if (playerId) {
                    window.location.href = `/players/${playerId}`;
                }
            });
        });
    }

    // Initial render
    renderTable();
}

function displaySearchResults(data) {
    const searchResultsDiv = document.getElementById('search-results');

    if (!data.players || data.players.length === 0) {
        searchResultsDiv.innerHTML = '<div class="error-message">No players found matching your search.</div>';
        return;
    }

    let resultsHTML = `
        <div class="search-results-header">
            <span>🔍</span>
            <span>Search Results (${data.count} found)</span>
        </div>
        <div class="player-cards-grid">
            ${data.players.map(player => `
                <div class="player-card" data-player-name="${player.player_name || ''}" onclick="window.location.href='/players/${player.player_id}'">
                    <div class="player-photo-placeholder">
                        <span>📷</span>
                        <small>Loading photo...</small>
                    </div>
                    <div class="player-card-info">
                        <h3 class="player-card-name">${player.player_name || 'Unknown'}</h3>
                        <div class="player-card-details">
                            <div class="player-card-detail-item">
                                <span class="detail-label">Team:</span>
                                <span class="detail-value">${player.team_title || '-'}</span>
                            </div>
                            <div class="player-card-detail-item">
                                <span class="detail-label">Position:</span>
                                <span class="detail-value">${player.position || '-'}</span>
                            </div>
                            <div class="player-card-stats">
                                <div class="stat-item">
                                    <span class="stat-label">Goals</span>
                                    <span class="stat-value goals">${player.goals || 0}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Assists</span>
                                    <span class="stat-value assists">${player.assists || 0}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">FIFA Rating</span>
                                    <span class="stat-value rating">${player.fifa_rating || '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    searchResultsDiv.innerHTML = resultsHTML;

    // After rendering the cards, try to load Unsplash photos for visible players
    try {
        loadPlayerImagesForSearchResults();
    } catch (e) {
        console.error('Error loading player images for search results:', e);
    }
}

async function loadPlayerDetail(playerId) {
    const container = document.getElementById('player-detail-container');

    try {
        const response = await fetch(`/api/players/${playerId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load player details');
        }

        displayPlayerDetail(data.player);

    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="error-message">
                <strong>Error:</strong> ${error.message}
            </div>
        `;
    }
}

function displayPlayerDetail(player) {
    const container = document.getElementById('player-detail-container');

    if (!player) {
        container.innerHTML = '<div class="error-message">Player not found.</div>';
        return;
    }

    const preferredTeam = player.team_title || player.fut23_team || '-';
    const preferredPositionText = player.fut23_position || player.position || '-';
    const primaryPosition = getPrimaryPosition(player);
    const pitchPos = getPitchCoordinatesForPosition(primaryPosition);

    const hasFifa = !!(player && (player.Rating || player.Pace || player.Shoot || player.Pass || player.Drible || player.Defense || player.Physical));

    const html = `
        <div class="player-detail-header">
            <div class="player-left-col">
                <div class="fifa-frame">
                    <img id="player-photo-img" class="frame-photo" src="" alt="${player.player_name || 'Player'}" style="display: none;" />
                    <div id="player-photo-placeholder" class="photo-placeholder-large">
                        <span>📷</span>
                        <small>Photo placeholder</small>
                    </div>
                </div>
                <div class="photo-kpis">
                    <div class="kpi">
                        <div class="kpi-label">Goals</div>
                        <div class="kpi-value">${player.goals || 0}</div>
                    </div>
                    <div class="kpi">
                        <div class="kpi-label">Assists</div>
                        <div class="kpi-value">${player.assists || 0}</div>
                    </div>
                    <div class="kpi">
                        <div class="kpi-label">Games</div>
                        <div class="kpi-value">${player.games || 0}</div>
                    </div>
                    <div class="kpi">
                        <div class="kpi-label">Shots</div>
                        <div class="kpi-value">${player.shots || 0}</div>
                    </div>
                </div>
                ${player.best_shot_id ? `<a class="btn-best-shot" href="/shot/${player.best_shot_id}">Best Shot</a>` : ''}
            </div>
            <div class="player-right-col">
                <h1 class="player-detail-name">${player.player_name || 'Unknown Player'}</h1>
                <div class="compare-actions">
                    <button id="compare-add-btn" class="btn-test btn-secondary" data-player-id="${player.player_id}">Add to Comparison</button>
                </div>
                <div class="tabs">
                    <button class="tab active" data-tab="player">Player</button>
                    ${hasFifa ? `<button class="tab" data-tab="fifa">FIFA 23</button>` : ''}
                </div>
                <div class="tab-panels">
                    <div id="tab-player" class="tab-panel active">
                        <div class="main-stats-grid">
                            <div class="stat-tile">
                                <div class="tile-label">Team</div>
                                <div class="tile-value">${preferredTeam}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Position</div>
                                <div class="tile-value"><span class="pos-chip">${preferredPositionText}</span></div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Games</div>
                                <div class="tile-value">${player.games || 0}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Goals</div>
                                <div class="tile-value goals-highlight">${player.goals || 0}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Assists</div>
                                <div class="tile-value">${player.assists || 0}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">xG</div>
                                <div class="tile-value">${player.xG ? Number(player.xG).toFixed(2) : '-'}</div>
                            </div>
                        </div>
                        <div class="mini-pitch">
                            <div class="position-marker" style="left: ${pitchPos.left}%; top: ${pitchPos.top}%;">
                                <span>${primaryPosition}</span>
                            </div>
                        </div>
                    </div>
                    ${hasFifa ? `
                    <div id="tab-fifa" class="tab-panel">
                        <div class="main-stats-grid">
                            <div class="stat-tile">
                                <div class="tile-label">Overall</div>
                                <div class="tile-value rating-highlight">${player.Rating || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Pace</div>
                                <div class="tile-value">${player.Pace || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Shooting</div>
                                <div class="tile-value">${player.Shoot || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Passing</div>
                                <div class="tile-value">${player.Pass || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Dribbling</div>
                                <div class="tile-value">${player.Drible || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Defense</div>
                                <div class="tile-value">${player.Defense || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Physical</div>
                                <div class="tile-value">${player.Physical || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Skill</div>
                                <div class="tile-value">${player.Skill || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Weak Foot</div>
                                <div class="tile-value">${player.Weak_foot || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Other Positions</div>
                                <div class="tile-value">${player.Other_Positions || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Attack Rate</div>
                                <div class="tile-value">${player.Attack_rate || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Defense Rate</div>
                                <div class="tile-value">${player.Defense_rate || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">Base Stats</div>
                                <div class="tile-value">${player.Base_Stats || '-'}</div>
                            </div>
                            <div class="stat-tile">
                                <div class="tile-label">In-Game Stats</div>
                                <div class="tile-value">${player.In_Game_Stats || '-'}</div>
                            </div>
                        </div>
                    </div>` : ''}
                </div>
            </div>
        </div>

        <div class="detail-sections">
            <div class="detail-box advanced-box">
                <h3 class="box-title">📊 Advanced Stats</h3>
                <div class="box-content">
                    <div class="stat-row">
                        <span class="stat-name">Non-Penalty Goals:</span>
                        <span class="stat-number">${player.npg || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">npxG:</span>
                        <span class="stat-number">${player.npxG ? Number(player.npxG).toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">xG Chain:</span>
                        <span class="stat-number">${player.xGChain ? Number(player.xGChain).toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">xG Buildup:</span>
                        <span class="stat-number">${player.xGBuildup ? Number(player.xGBuildup).toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Year:</span>
                        <span class="stat-number">${player.year || '-'}</span>
                    </div>
                </div>
            </div>

            <div class="detail-box additional-box">
                <h3 class="box-title">ℹ️ Additional Information</h3>
                <div class="box-content">
                    <div class="stat-row">
                        <span class="stat-name">Shots:</span>
                        <span class="stat-number">${player.shots || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Key Passes:</span>
                        <span class="stat-number">${player.key_passes || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Yellow Cards:</span>
                        <span class="stat-number">${player.yellow_cards || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Red Cards:</span>
                        <span class="stat-number">${player.red_cards || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Time Played:</span>
                        <span class="stat-number">${player.time ? Math.floor(player.time / 60) + ' min' : '-'}</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // After rendering the detail view, try to load a real player photo from Unsplash
    if (player && player.player_name) {
        loadPlayerImageFromUnsplash(player.player_name);
    }

    // Initialize tabs
    initTabs();

    // Enable mask automatically if mask asset exists
    enableFifaMaskIfAvailable();

    // Init comparison button state for detail page
    initCompareButtonForDetail(player.player_id);
}

// Tabs init
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.tab-panel');
    if (!tabs || tabs.length === 0) return;
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const panel = document.getElementById(`tab-${target}`);
            if (panel) panel.classList.add('active');
        });
    });
}

// Comparison detail button
async function initCompareButtonForDetail(playerId) {
    const btn = document.getElementById('compare-add-btn');
    if (!btn) return;
    const state = await getCompareList();
    updateCompareButtonState(btn, state, playerId);
    btn.addEventListener('click', async () => {
        const list = await getCompareList();
        if (list.includes(playerId)) {
            await removeFromCompare(playerId);
        } else {
            const res = await addToCompare(playerId);
            if (res.error) {
                alert(res.error);
            }
        }
        const newList = await getCompareList();
        updateCompareButtonState(btn, newList, playerId);
        refreshCompareUI();
    });
}

function updateCompareButtonState(btn, list, playerId) {
    const inList = list.includes(playerId);
    const limit = list.length >= 4 && !inList;
    btn.disabled = limit;
    if (inList) {
        btn.textContent = 'Added to Comparison';
        btn.classList.add('btn-disabled');
    } else if (limit) {
        btn.textContent = 'Limit Reached';
        btn.classList.add('btn-disabled');
    } else {
        btn.textContent = 'Add to Comparison';
        btn.classList.remove('btn-disabled');
    }
}

async function updateCompareButtonsState(playerId) {
    const btn = document.getElementById('compare-add-btn');
    if (btn && playerId) {
        const list = await getCompareList();
        updateCompareButtonState(btn, list, Number(playerId));
    }
}

// Position helpers
function getPrimaryPosition(player) {
    if (player && player.fut23_position) {
        return String(player.fut23_position).toUpperCase();
    }
    const raw = (player && player.position ? String(player.position) : '').toUpperCase();
    if (!raw) return 'CM';
    if (raw.includes('GK')) return 'GK';
    if (raw.includes('F') || raw.includes('S')) return 'ST';
    if (raw.includes('M')) return 'CM';
    if (raw.includes('D')) return 'CB';
    return 'CM';
}

function getPitchCoordinatesForPosition(pos) {
    const P = String(pos || '').toUpperCase();
    const map = {
        'GK': { left: 50, top: 92 },
        'CB': { left: 50, top: 75 },
        'LB': { left: 20, top: 75 },
        'RB': { left: 80, top: 75 },
        'LWB': { left: 25, top: 68 },
        'RWB': { left: 75, top: 68 },
        'CDM': { left: 50, top: 65 },
        'CM': { left: 50, top: 55 },
        'LM': { left: 20, top: 55 },
        'RM': { left: 80, top: 55 },
        'CAM': { left: 50, top: 45 },
        'LW': { left: 15, top: 35 },
        'RW': { left: 85, top: 35 },
        'CF': { left: 50, top: 30 },
        'ST': { left: 50, top: 25 }
    };
    if (map[P]) return map[P];
    // heuristic
    if (P.includes('WB')) return { left: 25, top: 68 };
    if (P.includes('B')) return { left: 50, top: 75 };
    if (P.includes('W')) return { left: P.includes('L') ? 20 : 80, top: 40 };
    if (P.includes('F')) return { left: 50, top: 25 };
    if (P.includes('M')) return { left: 50, top: 55 };
    if (P.includes('D')) return { left: 50, top: 75 };
    return { left: 50, top: 55 };
}

// Try enabling CSS mask if the mask asset exists
function enableFifaMaskIfAvailable() {
    try {
        const frame = document.querySelector('.fifa-frame');
        if (!frame) return;
        const img = new Image();
        img.onload = () => {
            frame.classList.add('mask');
        };
        img.onerror = () => { };
        img.src = '/static/fifaframe-mask.png';
    } catch (e) {
        // ignore
    }
}

// Comparison page loader
async function loadComparisonPage() {
    const container = document.getElementById('compare-container');
    if (!container) return;
    try {
        const listResp = await fetch('/api/players/compare/list');
        const listData = await listResp.json();
        const ids = listData.players || [];
        if (!ids.length) {
            container.innerHTML = '<div class="error-message">No players in comparison. Add players to compare.</div>';
            return;
        }
        const dataResp = await fetch('/api/players/compare/data');
        const data = await dataResp.json();
        const players = data.players || [];
        if (!players.length) {
            container.innerHTML = '<div class="error-message">No player data available for comparison.</div>';
            return;
        }
        renderComparison(container, players);
    } catch (e) {
        console.error(e);
        container.innerHTML = '<div class="error-message">Failed to load comparison.</div>';
    }
}

function renderComparison(container, players) {
    const mainStats = COMPARE_MAIN_STATS;
    const fifaStats = COMPARE_FIFA_STATS;

    const makeSection = (title, stats) => {
        const rows = stats.map(stat => renderStatRow(stat, players)).join('');
        return `
            <div class="compare-section">
                <div class="compare-section-title">${title}</div>
                <div class="compare-section-body">
                    ${rows}
                </div>
            </div>
        `;
    };

    const headerCols = players.map(p => `
        <div class="compare-col">
            <div class="compare-card">
                <div class="compare-name">${p.player_name || 'Unknown'}</div>
                <div class="compare-meta">${p.team_title || '-'} · ${p.position || '-'}</div>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="compare-grid">
            <div class="compare-header">
                <div class="compare-col compare-label"></div>
                ${headerCols}
            </div>
            ${makeSection('Main Stats', mainStats)}
            ${makeSection('FIFA Data', fifaStats)}
        </div>
    `;
}

function renderStatRow(statKey, players) {
    const displayName = statKeyDisplay(statKey);
    const values = players.map(p => p[statKey]);
    const classes = classifyValues(statKey, values);
    const cells = values.map((v, idx) => `
        <div class="compare-cell ${classes[idx]}">${formatStatValue(statKey, v)}</div>
    `).join('');
    return `
        <div class="compare-row">
            <div class="compare-label">${displayName}</div>
            ${cells}
        </div>
    `;
}

function statKeyDisplay(key) {
    const map = {
        goals: 'Goals',
        assists: 'Assists',
        games: 'Games',
        xG: 'xG',
        shots: 'Shots',
        key_passes: 'Key Passes',
        time: 'Time Played (min)',
        yellow_cards: 'Yellow Cards',
        red_cards: 'Red Cards',
        Rating: 'Overall',
        Pace: 'Pace',
        Shoot: 'Shooting',
        Pass: 'Passing',
        Drible: 'Dribbling',
        Defense: 'Defense',
        Physical: 'Physical',
        Skill: 'Skill Moves',
        Weak_foot: 'Weak Foot'
    };
    return map[key] || key;
}

function classifyValues(statKey, values) {
    const nums = values.map(v => (v === null || v === undefined || v === '-') ? null : Number(v));
    const valid = nums.filter(v => v !== null && !isNaN(v));
    if (!valid.length) return values.map(() => '');
    const betterIfLower = LOWER_BETTER.has(statKey);
    const bestVal = betterIfLower ? Math.min(...valid) : Math.max(...valid);
    const worstVal = betterIfLower ? Math.max(...valid) : Math.min(...valid);
    return nums.map(v => {
        if (v === null || isNaN(v)) return '';
        if (v === bestVal && v === worstVal) return ''; // all equal
        if (v === bestVal) return 'best';
        if (v === worstVal) return 'worst';
        return '';
    });
}

function formatStatValue(statKey, value) {
    if (value === null || value === undefined || value === '-') return '-';
    if (statKey === 'time') {
        const num = Number(value);
        return isNaN(num) ? value : `${Math.round(num / 60)}`;
    }
    if (typeof value === 'number') return value;
    const num = Number(value);
    if (!isNaN(num)) return num;
    return value;
}

// Shared Unsplash helper: fetch a player image URL
async function fetchUnsplashPlayerImageUrl(playerName) {
    if (!playerName) return null;

    // Build a query similar to the shots page logic
    const query = playerName.split(' ').join('_') + '_football_player';

    const response = await fetch(
        `https://api.unsplash.com/search/photos?page=1&per_page=1&orientation=portrait&query=${query}`,
        {
            method: 'GET',
            headers: {
                Authorization: 'Client-ID ThT--ohlHF51lLMYmNIbwbexClSxQuUqFtjRzKwrcKE',
                // NOTE: Replace this with your own Unsplash access key if needed.
            },
        }
    );

    if (!response.ok) {
        throw new Error('Failed to fetch image');
    }

    const data = await response.json();

    if (data.results && data.results.length > 0) {
        return data.results[0].urls.small || data.results[0].urls.regular;
    }

    return null;
}

// Load player image from Unsplash API for the detail page
async function loadPlayerImageFromUnsplash(playerName) {
    const imgEl = document.getElementById('player-photo-img');
    const placeholderEl = document.getElementById('player-photo-placeholder');

    if (!imgEl || !playerName) {
        return;
    }

    try {
        const imageUrl = await fetchUnsplashPlayerImageUrl(playerName);
        if (!imageUrl) {
            console.log('No images found for player on Unsplash');
            return;
        }

        imgEl.src = imageUrl;

        imgEl.onload = () => {
            imgEl.style.display = 'block';
            if (placeholderEl) {
                placeholderEl.style.display = 'none';
            }
        };

        imgEl.onerror = () => {
            console.log('Failed to load player image from URL');
            imgEl.style.display = 'none';
            if (placeholderEl) {
                placeholderEl.style.display = 'flex';
            }
        };
    } catch (error) {
        console.error('Error fetching player image from Unsplash:', error);
        // On error, keep the placeholder visible
    }
}

// Load Unsplash images for players in the search results grid
async function loadPlayerImagesForSearchResults() {
    const cards = document.querySelectorAll('.player-card');
    if (!cards || cards.length === 0) return;

    // Limit the number of API calls to avoid hitting Unsplash rate limits
    const maxImages = 12;
    let loadedCount = 0;

    for (const card of cards) {
        if (loadedCount >= maxImages) break;

        const playerName = card.getAttribute('data-player-name');
        const placeholder = card.querySelector('.player-photo-placeholder');

        if (!playerName || !placeholder) continue;

        try {
            const imageUrl = await fetchUnsplashPlayerImageUrl(playerName);
            if (!imageUrl) continue;

            placeholder.style.backgroundImage = `url('${imageUrl}')`;
            placeholder.style.backgroundSize = 'cover';
            placeholder.style.backgroundPosition = 'center';
            placeholder.style.border = 'none';
            placeholder.innerHTML = '';

            loadedCount += 1;
        } catch (error) {
            console.error('Error loading Unsplash image for player card:', error);
        }
    }
}
