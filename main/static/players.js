// Players Page JavaScript

document.addEventListener('DOMContentLoaded', function () {
    const btnAnalysis = document.getElementById('btn-analysis');
    const btnTest = document.getElementById('btn-test-fut23');
    const resultsDiv = document.getElementById('results');

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

