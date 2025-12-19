document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('addPlayerForm');
    const submitBtn = document.getElementById('submitBtn');
    const alertBox = document.getElementById('alertBox');

    if (!form) return;

    const showAlert = (msg, type) => {
        if (!alertBox) return;
        alertBox.classList.remove('hidden', 'error');
        if (type === 'error') alertBox.classList.add('error');
        alertBox.textContent = msg;
        try {
            alertBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (_) { }
    };

    const clearAlert = () => {
        if (!alertBox) return;
        alertBox.classList.add('hidden');
        alertBox.textContent = '';
        alertBox.classList.remove('error');
    };

    const readValue = (id) => {
        const el = document.getElementById(id);
        return el ? el.value : '';
    };

    const toNumberOrNull = (v) => {
        const s = String(v ?? '').trim();
        if (!s) return null;
        const n = Number(s);
        return Number.isFinite(n) ? n : null;
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert();

        const payload = {
            player_name: String(readValue('player_name')).trim(),
            player_id: toNumberOrNull(readValue('player_id')),
            year: toNumberOrNull(readValue('year')),

            team_title: String(readValue('team_title')).trim() || null,
            position: String(readValue('position')).trim() || null,

            games: toNumberOrNull(readValue('games')),
            time: toNumberOrNull(readValue('time')),
            goals: toNumberOrNull(readValue('goals')),
            xG: toNumberOrNull(readValue('xG')),
            assists: toNumberOrNull(readValue('assists')),
            xA: toNumberOrNull(readValue('xA')),
            shots: toNumberOrNull(readValue('shots')),
            key_passes: toNumberOrNull(readValue('key_passes')),

            yellow_cards: toNumberOrNull(readValue('yellow_cards')),
            red_cards: toNumberOrNull(readValue('red_cards')),

            npg: toNumberOrNull(readValue('npg')),
            npxG: toNumberOrNull(readValue('npxG')),
            xGChain: toNumberOrNull(readValue('xGChain')),
            xGBuildup: toNumberOrNull(readValue('xGBuildup')),

            best_shot_id: toNumberOrNull(readValue('best_shot_id')),
        };

        if (!payload.player_name || !payload.year) {
            showAlert('Please fill the required fields: Player Name and Year.', 'error');
            return;
        }

        // Remove nulls to keep request clean
        Object.keys(payload).forEach((k) => {
            if (payload[k] === null || payload[k] === '') delete payload[k];
        });

        submitBtn.disabled = true;
        const oldText = submitBtn.textContent;
        submitBtn.textContent = '⏳ Saving...';

        try {
            const resp = await fetch('/api/players', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || !data.success) {
                const msg = (data && (data.error || data.message)) || 'Failed to add player';
                showAlert(`Error: ${msg}`, 'error');
                return;
            }

            showAlert('Player added successfully. Redirecting to Players page...', 'success');
            setTimeout(() => {
                window.location.href = '/players';
            }, 1200);
        } catch (err) {
            console.error(err);
            showAlert('Network error: could not add player.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = oldText;
        }
    });
});


