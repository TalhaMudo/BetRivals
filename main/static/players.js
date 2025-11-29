// Players Page JavaScript

document.addEventListener('DOMContentLoaded', function () {
    const btnAnalysis = document.getElementById('btn-analysis');
    const btnTest = document.getElementById('btn-test-fut23');
    const resultsDiv = document.getElementById('results');
    const searchInput = document.getElementById('player-search');
    const searchBtn = document.getElementById('search-btn');
    const searchResultsDiv = document.getElementById('search-results');

    // Analysis button - shows players with most goals but least FIFA ratings
    if (btnAnalysis) {
        btnAnalysis.addEventListener('click', async function () {
            btnAnalysis.disabled = true;
            btnAnalysis.textContent = 'Loading...';
            resultsDiv.innerHTML = '<div class="loading">Analyzing player data</div>';

            try {
                const response = await fetch('/api/players/analysis');
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch data');
                }

                displayAnalysisResults(data);

            } catch (error) {
                console.error('Error:', error);
                resultsDiv.innerHTML = `
                    <div class="error-message">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                btnAnalysis.disabled = false;
                btnAnalysis.textContent = '🔍 Show Top Goal Scorers (Low FIFA Rating)';
            }
        });
    }

    // Test button - shows all FUT23 players
    if (btnTest) {
        btnTest.addEventListener('click', async function () {
            btnTest.disabled = true;
            btnTest.textContent = 'Loading...';
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
                btnTest.disabled = false;
                btnTest.textContent = 'Load All FUT23 Players';
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
                const response = await fetch(`/api/players/search?q=${encodeURIComponent(query)}`);
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
    }
});

function displayAnalysisResults(data) {
    const resultsDiv = document.getElementById('results');

    if (!data.players || data.players.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No players found in the database.</div>';
        return;
    }

    // Store original data for sorting
    let playersData = data.players.map((player, index) => ({
        ...player,
        originalIndex: index + 1
    }));
    let currentSort = { column: null, direction: null };

    // Column definitions for sorting
    const columns = [
        { key: 'originalIndex', label: 'Rank', type: 'number' },
        { key: 'player_name', label: 'Player Name', type: 'string' },
        { key: 'team_title', label: 'Team', type: 'string' },
        { key: 'position', label: 'Position', type: 'string' },
        { key: 'goals', label: 'Goals', type: 'number' },
        { key: 'assists', label: 'Assists', type: 'number' },
        { key: 'games', label: 'Games', type: 'number' },
        { key: 'xG', label: 'xG', type: 'number' },
        { key: 'fifa_rating', label: 'FIFA Rating', type: 'number' },
        { key: 'Pace', label: 'Pace', type: 'number' },
        { key: 'Shoot', label: 'Shoot', type: 'number' },
        { key: 'Pass', label: 'Pass', type: 'number' },
        { key: 'Defense', label: 'Defense', type: 'number' },
        { key: 'Physical', label: 'Physical', type: 'number' },
        { key: 'year', label: 'Year', type: 'number' }
    ];

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
                            ${playersData.map((player) => `
                                <tr>
                                    <td><strong>#${player.originalIndex}</strong></td>
                                    <td><strong>${player.player_name || '-'}</strong></td>
                                    <td>${player.team_title || '-'}</td>
                                    <td>${player.position || '-'}</td>
                                    <td><span style="color: #2ecc71; font-weight: 700;">${player.goals || 0}</span></td>
                                    <td>${player.assists || 0}</td>
                                    <td>${player.games || 0}</td>
                                    <td>${player.xG ? player.xG.toFixed(2) : '-'}</td>
                                    <td><span style="color: #e74c3c; font-weight: 700;">${player.fifa_rating || '-'}</span></td>
                                    <td>${player.Pace || '-'}</td>
                                    <td>${player.Shoot || '-'}</td>
                                    <td>${player.Pass || '-'}</td>
                                    <td>${player.Defense || '-'}</td>
                                    <td>${player.Physical || '-'}</td>
                                    <td>${player.year || '-'}</td>
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

function displayResults(data) {
    const resultsDiv = document.getElementById('results');

    if (!data.players || data.players.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No players found in the database.</div>';
        return;
    }

    // Get all column names from the first player object
    const columns = Object.keys(data.players[0]);
    
    // Store original data for sorting
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
                    <span>🏆</span>
                    <span>FUT23 Players Data</span>
                </div>
                <div class="results-count">Total players: ${data.count}${currentSort.column ? ` (sorted by: ${currentSort.column} ${currentSort.direction === 'asc' ? '↑' : '↓'})` : ''}</div>
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
                                <tr>
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
