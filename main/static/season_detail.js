function safeNumber(val) {
    return val === null || val === undefined ? "-" : val;
}

function formatDate(val) {
    if (!val) return "-";
    try {
        const d = new Date(val);
        if (isNaN(d.getTime())) return val;
        return d.toLocaleDateString();
    } catch {
        return val;
    }
}

async function loadSeasonDetail() {
    const root = document.getElementById("seasonDetailRoot");
    if (!root) return;

    const seasonId = root.dataset.seasonId;
    const loadingEl = document.getElementById("sd-loading");
    const errorEl = document.getElementById("sd-error");
    const contentEl = document.getElementById("sd-content");

    loadingEl.classList.remove("hidden");
    errorEl.classList.add("hidden");
    contentEl.classList.add("hidden");

    try {
        const res = await fetch(`/api/seasons/${seasonId}`);
        if (!res.ok) {
            throw new Error(`Failed to fetch season: ${res.status}`);
        }
        const s = await res.json();

        loadingEl.classList.add("hidden");
        contentEl.classList.remove("hidden");

        const titleEl = document.getElementById("sd-title");
        const subtitleEl = document.getElementById("sd-subtitle");

        const teamName = s.team_name || "Unknown Team";
        const year = s.year ?? "-";
        const dateStr = formatDate(s.date);
        const ha = s.h_a || "-";
        const result = s.result || "-";
        const title = s.title || "No title";

        titleEl.textContent = `${teamName} - ${year}`;
        subtitleEl.textContent = `${title} • ${ha === "H" ? "Home" : ha === "A" ? "Away" : "Home/Away"} • Result: ${result} • ${dateStr}`;

        document.getElementById("sd-xg").textContent = safeNumber(s.xG);
        document.getElementById("sd-xga").textContent = safeNumber(s.xGA);
        document.getElementById("sd-npxg").textContent = safeNumber(s.npxG);
        document.getElementById("sd-npxga").textContent = safeNumber(s.npxGA);
        document.getElementById("sd-npxgd").textContent = safeNumber(s.npxGD);

        document.getElementById("sd-deep").textContent = safeNumber(s.deep);
        document.getElementById("sd-deep-allowed").textContent = safeNumber(s.deep_allowed);
        document.getElementById("sd-scored").textContent = safeNumber(s.scored);
        document.getElementById("sd-missed").textContent = safeNumber(s.missed);
        document.getElementById("sd-xpts").textContent = safeNumber(s.xpts);

        document.getElementById("sd-wins").textContent = safeNumber(s.wins);
        document.getElementById("sd-draws").textContent = safeNumber(s.draws);
        document.getElementById("sd-loses").textContent = safeNumber(s.loses);
        document.getElementById("sd-pts").textContent = safeNumber(s.pts);

        document.getElementById("sd-ppda-att").textContent = safeNumber(s.ppda_att);
        document.getElementById("sd-ppda-def").textContent = safeNumber(s.ppda_def);
        document.getElementById("sd-ppda-allowed-att").textContent = safeNumber(s.ppda_allowed_att);
        document.getElementById("sd-ppda-allowed-def").textContent = safeNumber(s.ppda_allowed_def);

    } catch (err) {
        console.error(err);
        loadingEl.classList.add("hidden");
        errorEl.textContent = "Failed to load season details.";
        errorEl.classList.remove("hidden");
    }
}

document.addEventListener("DOMContentLoaded", loadSeasonDetail);
