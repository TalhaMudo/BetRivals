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

    const html = `
        <div class="player-detail-header">
            <div class="player-photo-large">
                <img id="player-photo-img" src="" alt="${player.player_name || 'Player'}" style="display: none;" />
                <div id="player-photo-placeholder" class="photo-placeholder-large">
                    <span>📷</span>
                    <small>Photo placeholder</small>
                </div>
            </div>
            <div class="player-header-info">
                <h1 class="player-detail-name">${player.player_name || 'Unknown Player'}</h1>
                <div class="player-header-details">
                    <div class="header-detail-item">
                        <span class="header-label">Team:</span>
                        <span class="header-value">${player.team_title || player.fut23_team || '-'}</span>
                    </div>
                    <div class="header-detail-item">
                        <span class="header-label">Position:</span>
                        <span class="header-value">${player.position || player.fut23_position || '-'}</span>
                    </div>
                    <div class="header-detail-item">
                        <span class="header-label">Country:</span>
                        <span class="header-value">${player.Country || '-'}</span>
                    </div>
                    <div class="header-detail-item">
                        <span class="header-label">League:</span>
                        <span class="header-value">${player.League || '-'}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="player-detail-grid">
            <div class="detail-box performance-box">
                <h3 class="box-title">⚽ Performance Stats</h3>
                <div class="box-content">
                    <div class="stat-row">
                        <span class="stat-name">Games:</span>
                        <span class="stat-number">${player.games || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Goals:</span>
                        <span class="stat-number goals-highlight">${player.goals || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Assists:</span>
                        <span class="stat-number">${player.assists || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">xG:</span>
                        <span class="stat-number">${player.xG ? player.xG.toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">xA:</span>
                        <span class="stat-number">${player.xA ? player.xA.toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Shots:</span>
                        <span class="stat-number">${player.shots || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Key Passes:</span>
                        <span class="stat-number">${player.key_passes || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Time Played:</span>
                        <span class="stat-number">${player.time ? Math.floor(player.time / 60) + ' min' : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Yellow Cards:</span>
                        <span class="stat-number">${player.yellow_cards || 0}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Red Cards:</span>
                        <span class="stat-number">${player.red_cards || 0}</span>
                    </div>
                </div>
            </div>

            <div class="detail-box fifa-box">
                <h3 class="box-title">🎮 FIFA 23 Ratings</h3>
                <div class="box-content">
                    <div class="stat-row">
                        <span class="stat-name">Overall Rating:</span>
                        <span class="stat-number rating-highlight">${player.Rating || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Pace:</span>
                        <span class="stat-number">${player.Pace || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Shooting:</span>
                        <span class="stat-number">${player.Shoot || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Passing:</span>
                        <span class="stat-number">${player.Pass || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Dribbling:</span>
                        <span class="stat-number">${player.Drible || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Defending:</span>
                        <span class="stat-number">${player.Defense || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Physical:</span>
                        <span class="stat-number">${player.Physical || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Skill Moves:</span>
                        <span class="stat-number">${player.Skill || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Weak Foot:</span>
                        <span class="stat-number">${player.Weak_foot || '-'}</span>
                    </div>
                </div>
            </div>

            <div class="detail-box advanced-box">
                <h3 class="box-title">📊 Advanced Stats</h3>
                <div class="box-content">
                    <div class="stat-row">
                        <span class="stat-name">Non-Penalty Goals:</span>
                        <span class="stat-number">${player.npg || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">npxG:</span>
                        <span class="stat-number">${player.npxG ? player.npxG.toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">xG Chain:</span>
                        <span class="stat-number">${player.xGChain ? player.xGChain.toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">xG Buildup:</span>
                        <span class="stat-number">${player.xGBuildup ? player.xGBuildup.toFixed(2) : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Base Stats:</span>
                        <span class="stat-number">${player.Base_Stats || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">In-Game Stats:</span>
                        <span class="stat-number">${player.In_Game_Stats || '-'}</span>
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
                        <span class="stat-name">Other Positions:</span>
                        <span class="stat-number">${player.Other_Positions || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Run Type:</span>
                        <span class="stat-number">${player.Run_type || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Price:</span>
                        <span class="stat-number">${player.Price || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Attack Rate:</span>
                        <span class="stat-number">${player.Attack_rate || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Defense Rate:</span>
                        <span class="stat-number">${player.Defense_rate || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Body Type:</span>
                        <span class="stat-number">${player.Body_type || '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Height:</span>
                        <span class="stat-number">${player.Height_cm ? player.Height_cm + ' cm' : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Weight:</span>
                        <span class="stat-number">${player.Weight ? player.Weight + ' kg' : '-'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-name">Popularity:</span>
                        <span class="stat-number">${player.Popularity || '-'}</span>
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
