// Players Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const btnTest = document.getElementById('btn-test-fut23');
    const resultsDiv = document.getElementById('results');

    if (btnTest) {
        btnTest.addEventListener('click', async function() {
            // Disable button during request
            btnTest.disabled = true;
            btnTest.textContent = 'Loading...';

            // Clear previous results
            resultsDiv.innerHTML = '<div class="loading">Loading players data</div>';

            try {
                const response = await fetch('/api/players/fut23');
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch data');
                }

                // Display results
                displayResults(data);

            } catch (error) {
                console.error('Error:', error);
                resultsDiv.innerHTML = `
                    <div class="error-message">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                // Re-enable button
                btnTest.disabled = false;
                btnTest.textContent = 'Load All FUT23 Players';
            }
        });
    }
});

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

