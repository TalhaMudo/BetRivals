document.addEventListener('DOMContentLoaded', () => {
    const logos = document.querySelectorAll('.team-logo');

    logos.forEach(img => {
        const team = img.dataset.team;
        if (!team) return;
        fetchLogoForTeam(team).then(url => {
            if (url) {
                img.src = url;
            } else {
                img.classList.add('no-logo');
                img.alt = team;
                img.title = team;
            }
        }).catch(() => {
            img.classList.add('no-logo');
        });
    });

    async function fetchLogoForTeam(teamName) {
        const key = "3df255896f2f4090feb3722421a65c08"; // zaten bedava kalsin burda :D

        const base = 'https://v3.football.api-sports.io/teams';
        const params = `?name=${encodeURIComponent(teamName)}`;

        try {
            const res = await fetch(base + params, {
                method: 'GET',
                headers: {
                    'x-apisports-key': key
                }
            });
            if (!res.ok) {
                console.warn('api-football responded with', res.status);
                return null;
            }
            const data = await res.json();
            if (data && Array.isArray(data.response) && data.response.length > 0) {
                const teamObj = data.response[0].team;
                if (teamObj && teamObj.logo) return teamObj.logo;
            }
        } catch (e) {
            console.warn('api-football logo fetch failed for', teamName, e);
        }

        return null;
    }
});

