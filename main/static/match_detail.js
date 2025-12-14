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

    const comparisonCard = document.querySelector('.season-comparison-card');
    if (comparisonCard) {
        const statBars = comparisonCard.querySelectorAll('.stat-bar[data-target-width]');

        // intersection observer for animation on scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    statBars.forEach((bar, index) => {
                        setTimeout(() => {
                            bar.style.transition = 'width 0.6s ease-out';
                            bar.style.width = bar.dataset.targetWidth;
                        }, index * 80);
                    });
                    observer.disconnect();
                }
            });
        }, { threshold: 0.2 });

        observer.observe(comparisonCard);

        // add counter animation to big stats
        const bigStats = comparisonCard.querySelectorAll('.big-stat');
        bigStats.forEach(stat => {
            const targetValue = parseInt(stat.textContent) || 0;
            if (targetValue > 0) {
                stat.textContent = '0';
                animateCounter(stat, 0, targetValue, 1000);
            }
        });
    }

    // Counter animation helper
    function animateCounter(element, start, end, duration) {
        const range = end - start;
        const startTime = performance.now();
        
        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            const currentValue = Math.floor(start + (range * easeProgress));
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = end;
            }
        }
        
        requestAnimationFrame(updateCounter);
    }
});
