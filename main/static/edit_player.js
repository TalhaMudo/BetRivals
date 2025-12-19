document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('edit-search');
    const resultsEl = document.getElementById('edit-results');
    const form = document.getElementById('editPlayerForm');
    const submitBtn = document.getElementById('submitBtn');
    const alertBox = document.getElementById('alertBox');

    if (!searchInput || !resultsEl || !form) return;

    const showAlert = (msg, type) => {
        if (!alertBox) return;
        alertBox.classList.remove('hidden', 'error');
        if (type === 'error') alertBox.classList.add('error');
        alertBox.textContent = msg;
    };

    const clearAlert = () => {
        if (!alertBox) return;
        alertBox.classList.add('hidden');
        alertBox.textContent = '';
        alertBox.classList.remove('error');
    };

    const setValue = (id, value, fallback = '') => {
        const el = document.getElementById(id);
        if (!el) return;
        el.value = (value === null || value === undefined) ? fallback : value;
    };

    const toNumberOrNull = (v) => {
        const s = String(v ?? '').trim();
        if (!s) return null;
        const n = Number(s);
        return Number.isFinite(n) ? n : null;
    };

    let debounceTimer = null;

    const renderResults = (players) => {
        if (!players || players.length === 0) {
            resultsEl.innerHTML = '<div class="form-alert error">No results.</div>';
            return;
        }

        const items = players.slice(0, 12).map(p => {
            const label = `${p.player_name || 'Unknown'} · ${p.team_title || '-'} · ${p.position || '-'} · ${p.year || '-'}`;
            return `
                <button type="button" class="edit-result-item" data-spid="${p.season_player_id}">
                    <div class="edit-result-title">${label}</div>
                    <div class="edit-result-sub">season_player_id: ${p.season_player_id} · player_id: ${p.player_id}</div>
                </button>
            `;
        }).join('');

        resultsEl.innerHTML = `<div class="edit-results-list">${items}</div>`;
        resultsEl.querySelectorAll('.edit-result-item').forEach(btn => {
            btn.addEventListener('click', async () => {
                const spid = btn.getAttribute('data-spid');
                if (!spid) return;
                await loadPlayerSeason(spid);
            });
        });
    };

    const loadPlayerSeason = async (seasonPlayerId) => {
        clearAlert();
        resultsEl.innerHTML = '';
        try {
            const resp = await fetch(`/api/players/season/${encodeURIComponent(seasonPlayerId)}`);
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || !data.success || !data.player) {
                throw new Error((data && data.error) || 'Failed to load player');
            }

            const p = data.player;
            setValue('season_player_id', p.season_player_id);
            setValue('player_id', p.player_id);
            setValue('player_name', p.player_name);
            setValue('year', p.year);
            setValue('team_title', p.team_title);
            setValue('position', p.position);
            setValue('games', p.games);
            setValue('time', p.time);
            setValue('goals', p.goals);
            setValue('xG', p.xG);
            setValue('assists', p.assists);
            setValue('xA', p.xA);
            setValue('shots', p.shots);
            setValue('key_passes', p.key_passes);
            setValue('yellow_cards', p.yellow_cards);
            setValue('red_cards', p.red_cards);
            setValue('npg', p.npg);
            setValue('npxG', p.npxG);
            setValue('xGChain', p.xGChain);
            setValue('xGBuildup', p.xGBuildup);
            setValue('best_shot_id', p.best_shot_id);

            form.classList.remove('hidden');
            showAlert('Loaded. You can now edit and save changes.', 'success');
            try {
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } catch (_) { }
        } catch (e) {
            console.error(e);
            showAlert(`Error: ${e.message}`, 'error');
        }
    };

    const performSearch = async () => {
        const q = String(searchInput.value || '').trim();
        if (q.length < 2) {
            resultsEl.innerHTML = '';
            return;
        }
        resultsEl.innerHTML = '<div class="form-alert">Searching...</div>';
        try {
            const resp = await fetch(`/api/players/search?q=${encodeURIComponent(q)}`);
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok) throw new Error((data && data.error) || 'Search failed');
            renderResults(data.players || []);
        } catch (e) {
            console.error(e);
            resultsEl.innerHTML = `<div class="form-alert error">Error: ${e.message}</div>`;
        }
    };

    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(performSearch, 250);
    });

    // Check for season_player_id in URL query parameter (from admin page)
    const urlParams = new URLSearchParams(window.location.search);
    const seasonPlayerIdFromUrl = urlParams.get('season_player_id');
    if (seasonPlayerIdFromUrl) {
        // Automatically load the player if season_player_id is in URL
        loadPlayerSeason(seasonPlayerIdFromUrl);
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert();

        const seasonPlayerId = document.getElementById('season_player_id')?.value;
        if (!seasonPlayerId) {
            showAlert('Please select a player first.', 'error');
            return;
        }

        const payload = {
            player_name: String(document.getElementById('player_name')?.value || '').trim(),
            year: toNumberOrNull(document.getElementById('year')?.value),
            team_title: String(document.getElementById('team_title')?.value || '').trim() || null,
            position: String(document.getElementById('position')?.value || '').trim() || null,
            games: toNumberOrNull(document.getElementById('games')?.value),
            time: toNumberOrNull(document.getElementById('time')?.value),
            goals: toNumberOrNull(document.getElementById('goals')?.value),
            xG: toNumberOrNull(document.getElementById('xG')?.value),
            assists: toNumberOrNull(document.getElementById('assists')?.value),
            xA: toNumberOrNull(document.getElementById('xA')?.value),
            shots: toNumberOrNull(document.getElementById('shots')?.value),
            key_passes: toNumberOrNull(document.getElementById('key_passes')?.value),
            yellow_cards: toNumberOrNull(document.getElementById('yellow_cards')?.value),
            red_cards: toNumberOrNull(document.getElementById('red_cards')?.value),
            npg: toNumberOrNull(document.getElementById('npg')?.value),
            npxG: toNumberOrNull(document.getElementById('npxG')?.value),
            xGChain: toNumberOrNull(document.getElementById('xGChain')?.value),
            xGBuildup: toNumberOrNull(document.getElementById('xGBuildup')?.value),
            best_shot_id: toNumberOrNull(document.getElementById('best_shot_id')?.value),
        };

        if (!payload.player_name || !payload.year) {
            showAlert('Player Name and Year are required.', 'error');
            return;
        }

        Object.keys(payload).forEach(k => {
            if (payload[k] === null || payload[k] === '') delete payload[k];
        });

        submitBtn.disabled = true;
        const oldText = submitBtn.textContent;
        submitBtn.textContent = '⏳ Saving...';

        try {
            const resp = await fetch(`/api/players/season/${encodeURIComponent(seasonPlayerId)}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || !data.success) {
                throw new Error((data && data.error) || 'Update failed');
            }
            showAlert('Saved successfully.', 'success');
        } catch (e2) {
            console.error(e2);
            showAlert(`Error: ${e2.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = oldText;
        }
    });
});


