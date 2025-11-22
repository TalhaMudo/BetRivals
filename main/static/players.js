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
        searchInput.addEventListener('keypress', function(e) {
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

    // Create analysis table with key metrics
    let tableHTML = `
        <div class="results-container">
            <div class="results-header">
                <span>⚽</span>
                <span>${data.description || 'Player Analysis'}</span>
            </div>
            <div class="results-count">Showing top ${data.count} players (sorted by: Most Goals ↓, Lowest FIFA Rating ↑)</div>
            <div class="players-table">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Player Name</th>
                            <th>Team</th>
                            <th>Position</th>
                            <th>Goals ⚽</th>
                            <th>Assists</th>
                            <th>Games</th>
                            <th>xG</th>
                            <th>FIFA Rating</th>
                            <th>Pace</th>
                            <th>Shoot</th>
                            <th>Pass</th>
                            <th>Defense</th>
                            <th>Physical</th>
                            <th>Year</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.players.map((player, index) => `
                            <tr>
                                <td><strong>#${index + 1}</strong></td>
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
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');

    if (!data.players || data.players.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No players found in the database.</div>';
        return;
    }

    // Get all column names from the first player object
    const columns = Object.keys(data.players[0]);

    // Create table HTML
    let tableHTML = `
        <div class="results-container">
            <div class="results-header">
                <span>🏆</span>
                <span>FUT23 Players Data</span>
            </div>
            <div class="results-count">Total players: ${data.count}</div>
            <div class="players-table">
                <table>
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.players.map(player => `
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
                <div class="player-card" onclick="window.location.href='/talha/${player.player_id}'">
                    <div class="player-photo-placeholder">
                        <span>📷</span>
                        <small>Photo placeholder</small>
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
}

