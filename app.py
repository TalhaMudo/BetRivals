from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import logging
import requests
from dotenv import load_dotenv
from utils import DatabaseConnector
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
logger = logging.getLogger(__name__)
SECRET_KEY = os.getenv("secret_key", "bet-rivals-bostanXXX")

app = Flask(__name__, template_folder='main/templates', static_folder='main/static')

app.config["SECRET_KEY"] = SECRET_KEY

# Bridge between Flask and Database
db = DatabaseConnector()

@app.route("/")
def home():
    """Ana sayfa rotası"""
    return render_template("index.html", title="BetRivals - Football Analytics")


@app.route("/about")
def about():
    """Hakkında sayfası"""
    return render_template("about.html", title="About Us")

# --- Authentication Middleware --- #
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # Check if it's an API request
            if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                return jsonify({
                    "success": False,
                    "message": "Authentication required",
                    "error": "unauthorized"
                }), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


#--------------BILGE-START------------------------------

# ========= BILGE: Teams & Seasons pages =========

@app.route("/teams")
def teams_page():
    return render_template("teams.html", title="Teams")

@app.route("/seasons")
def seasons_page():
    return render_template("seasons_user.html", title="Seasons")

# ========= BILGE: Teams API =========

@app.route("/api/teams", methods=["GET"])
def api_teams_list():
    """
    GET /api/teams?q=Ar&page=1&per_page=20
    """
    q = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = int(request.args.get("per_page", 20))
    if per_page < 1:
         per_page = 1

    offset = (page - 1) * per_page

    sql_base = "FROM teams WHERE 1=1"
    params = []

    if q:
        sql_base += " AND team_name LIKE %s"
        params.append(f"%{q}%")

    try:
        # COUNT
        count_rows = db.execute_query(f"SELECT COUNT(*) AS total {sql_base}", params)
        total = count_rows[0]["total"]

        # DATA
        rows = db.execute_query(
            f"""
            SELECT 
                team_id AS team_id,
                team_name AS team_name
            {sql_base}
            ORDER BY team_name ASC
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset]
        )

        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": rows
        })

    except Exception as e:
        logger.exception("Error listing teams: %s", e)
        return jsonify({"error": "Database error", "items": []}), 500


@app.route("/api/teams", methods=["POST"])
def api_team_create():
    data = request.get_json(silent=True) or {}
    name = (data.get("team_name") or "").strip()
    
    if not name:
        return jsonify({"error": "team_name is required"}), 400

    try:
        db.execute_query(
            "INSERT INTO teams (team_name) VALUES (%s)",
            [name],
            fetch_all=False
        )
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error creating team: %s", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/api/teams/<int:team_id>/update", methods=["POST"])
def api_team_update(team_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("team_name") or "").strip()

    if not name:
        return jsonify({"error": "team_name is required"}), 400
    
    try:
        db.execute_query(
            "UPDATE teams SET team_name=%s WHERE team_id=%s",
            [name, team_id],
            fetch_all=False
        )
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error updating team: %s", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/api/teams/<int:team_id>/delete", methods=["POST"])
def api_team_delete(team_id):
    try:
        db.execute_query(
            "DELETE FROM teams WHERE team_id=%s",
            [team_id],
            fetch_all=False
        )
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error deleting team: %s", e)
        return jsonify({"error": "Cannot delete team (FK in use?)"}), 400




# ========= BILGE: Seasons API =========

@app.route("/api/seasons", methods=["GET"])
def api_seasons_list():
    """
    GET /api/seasons?team_id=1&year=2022&h_a=H&result=W
    """
    team_id = request.args.get("team_id")
    year = request.args.get("year")
    title = request.args.get("title", "").strip()
    h_a = request.args.get("h_a")
    result = request.args.get("result")

    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 20)), 1), 200)
    offset = (page - 1) * per_page

    sql_where = "WHERE 1=1"
    params = []

    if team_id:
        sql_where += " AND s.team_id = %s"
        params.append(team_id)
    if year:
        sql_where += " AND s.year = %s"
        params.append(year)
    if title:
        sql_where += " AND s.title LIKE %s"
        params.append(f"%{title}%")
    if h_a in ("H", "A"):
        sql_where += " AND s.h_a = %s"
        params.append(h_a)
    if result in ("W", "D", "L"):
        sql_where += " AND s.result = %s"
        params.append(result)

    try:
        # COUNT
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM season s
            LEFT JOIN teams t ON t.team_id = s.team_id
            {sql_where}
        """
        count_rows = db.execute_query(count_sql, params)
        total = count_rows[0]["total"]

        # DATA
        sql = f"""
            SELECT
                s.seasonentryid AS seasonentryid,
                s.team_id       AS team_id,
                t.team_name     AS team_name,
                s.title         AS title,
                s.year          AS year,
                s.h_a           AS h_a,
                s.xG            AS xG,
                s.xGA           AS xGA,
                s.npxG          AS npxG,
                s.npxGA         AS npxGA,
                s.deep          AS deep,
                s.deep_allowed  AS deep_allowed,
                s.scored        AS scored,
                s.missed        AS missed,
                s.xpts          AS xpts,
                s.result        AS result,
                s.date          AS date,
                s.wins          AS wins,
                s.draws         AS draws,
                s.loses         AS loses,
                s.pts           AS pts,
                s.npxGD         AS npxGD,
                s.ppda_att      AS ppda_att,
                s.ppda_def      AS ppda_def,
                s.ppda_allowed_att AS ppda_allowed_att,
                s.ppda_allowed_def AS ppda_allowed_def
            FROM season s
            LEFT JOIN teams t ON t.team_id = s.team_id
            {sql_where}
            ORDER BY s.year DESC, t.team_name ASC
            LIMIT %s OFFSET %s
        """

        rows = db.execute_query(sql, params + [per_page, offset])

        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": rows
        })

    except Exception as e:
        logger.exception("Error listing seasons: %s", e)
        return jsonify({"error": "Database error", "items": []}), 500
    

@app.route("/api/seasons/years", methods=["GET"])
def api_seasons_years():
    """
    Returns distinct season years for dropdown.
    """
    try:
        rows = db.execute_query(
            """
            SELECT DISTINCT year
            FROM season
            WHERE year IS NOT NULL
            ORDER BY year DESC
            """,
            fetch_all=True
        ) or []

        years = [r["year"] for r in rows if r.get("year") is not None]
        return jsonify({"success": True, "years": years})

    except Exception as e:
        logger.exception("Error fetching season years: %s", e)
        return jsonify({"success": False, "years": []}), 500


@app.route("/api/seasons", methods=["POST"])
def api_season_create():
    data = request.get_json(silent=True) or {}

    if not data.get("team_id") or not data.get("year"):
        return jsonify({"error": "team_id and year are required"}), 400

    fields = []
    values = []
    params = []

    for k, v in data.items():
        if v not in (None, ""):
            fields.append(k)
            values.append("%s")
            params.append(v)

    sql = f"INSERT INTO season ({', '.join(fields)}) VALUES ({', '.join(values)})"

    try:
        db.execute_query(sql, params, fetch_all=False)
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error creating season: %s", e)
        return jsonify({"error": "Database error"}), 500

# Yeni Eklenen Seasons Detay Rotası (Season Detay Sayfası)
@app.route("/seasons/<int:seasonentryid>")
def season_detail(seasonentryid):
    """Bireysel sezon girişi detay sayfası"""
    return render_template(
        "season_detail.html",
        title="Season Details",
        seasonentryid=seasonentryid
    )


# Yeni Eklenen Seasons Detay API'si
@app.route("/api/seasons/<int:seasonentryid>", methods=["GET"])
def api_season_detail(seasonentryid):
    """
    GET /api/seasons/<int:seasonentryid>
    Tek bir sezon girişinin detaylarını döndürür.
    """
    try:
        sql = f"""
            SELECT
                s.seasonentryid AS seasonentryid,
                s.team_id AS team_id,
                t.team_name AS team_name,
                s.title AS title,
                s.year AS year,
                s.h_a AS h_a,
                s.xG AS xG,
                s.xGA AS xGA,
                s.npxG AS npxG,
                s.npxGA AS npxGA,
                s.deep AS deep,
                s.deep_allowed AS deep_allowed,
                s.scored AS scored,
                s.missed AS missed,
                s.xpts AS xpts,
                s.result AS result,
                s.date AS date,
                s.wins AS wins,
                s.draws AS draws,
                s.loses AS loses,
                s.pts AS pts,
                s.npxGD AS npxGD,
                s.ppda_att AS ppda_att,
                s.ppda_def AS ppda_def,
                s.ppda_allowed_att AS ppda_allowed_att,
                s.ppda_allowed_def AS ppda_allowed_def
            FROM season s
            LEFT JOIN teams t ON t.team_id = s.team_id
            WHERE s.seasonentryid = %s
            LIMIT 1
        """

        rows = db.execute_query(sql, [seasonentryid])

        if not rows:
            return jsonify({"error": "Season entry not found"}), 404

        return jsonify(rows[0])

    except Exception as e:
        logger.exception("Error fetching season detail: %s", e)
        return jsonify({"error": "Database error"}), 500

@app.route("/api/seasons/<int:seasonentryid>/update", methods=["POST"])
def api_season_update(seasonentryid):
    data = request.get_json(silent=True) or {}

    fields = []
    params = []

    for k, v in data.items():
        fields.append(f"{k}=%s")
        params.append(v)

    if not fields:
        return jsonify({"error": "no fields to update"}), 400

    params.append(seasonentryid)

    sql = f"UPDATE season SET {', '.join(fields)} WHERE seasonentryid=%s"

    try:
        db.execute_query(sql, params, fetch_all=False)
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error updating season: %s", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/api/seasons/<int:seasonentryid>/delete", methods=["POST"])
def api_season_delete(seasonentryid):
    try:
        db.execute_query(
            "DELETE FROM season WHERE seasonentryid=%s",
            [seasonentryid],
            fetch_all=False
        )
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error deleting season: %s", e)
        return jsonify({"error": "Cannot delete season"}), 400
    

    
# ============================================
# USER INSIGHTS (PUBLIC) - TOP 2 COMPLEX QUERIES
# ============================================

@app.route("/api/seasons/top", methods=["GET"])
def api_seasons_top():
    """
    Returns top season entries for a given year (JOIN + ORDER BY).
    Used in user seasons page as "Season Insights".
    GET /api/seasons/top?year=2023&limit=10
    """
    year = request.args.get("year")
    limit = int(request.args.get("limit", 10))
    limit = min(max(limit, 1), 50)

    try:
        # If year is not provided, default to latest year in season table
        if not year:
            y = db.execute_query("SELECT MAX(year) AS y FROM season", fetch_all=True)
            year = y[0]["y"] if y and y[0].get("y") is not None else 2023

        sql = """
            SELECT
                s.seasonentryid AS seasonentryid,
                s.year          AS year,
                t.team_id       AS team_id,
                t.team_name     AS team_name,
                s.title         AS title,
                s.pts           AS pts,
                s.xG            AS xG,
                s.xGA           AS xGA,
                (s.xG - s.xGA)  AS xg_diff
            FROM season s
            INNER JOIN teams t ON s.team_id = t.team_id
            WHERE s.year = %s
            ORDER BY s.pts DESC, (s.xG - s.xGA) DESC, t.team_name ASC
            LIMIT %s
        """
        rows = db.execute_query(sql, params=[year, limit]) or []

        return jsonify({
            "success": True,
            "year": int(year),
            "limit": limit,
            "items": rows
        })
    except Exception as e:
        logger.exception("Error in /api/seasons/top: %s", e)
        return jsonify({"success": False, "error": "Database error", "items": []}), 500


@app.route("/api/teams/summary", methods=["GET"])
def api_teams_summary():
    """
    Returns team summary (GROUP BY + HAVING + ORDER BY).
    Used in user teams page as "Team Summary".
    GET /api/teams/summary?min_seasons=3&limit=20
    """
    min_seasons = int(request.args.get("min_seasons", 3))
    limit = int(request.args.get("limit", 20))
    min_seasons = max(min_seasons, 1)
    limit = min(max(limit, 1), 50)

    try:
        sql = """
            SELECT
                t.team_id                           AS team_id,
                t.team_name                         AS team_name,
                COUNT(s.seasonentryid)              AS total_seasons,
                ROUND(AVG(s.xG), 2)                 AS avg_xG,
                ROUND(AVG(s.xGA), 2)                AS avg_xGA,
                ROUND(AVG(s.xG - s.xGA), 2)         AS avg_xg_diff,
                COALESCE(SUM(s.pts), 0)             AS total_points,
                ROUND(AVG(s.pts), 2)                AS avg_points
            FROM teams t
            LEFT JOIN season s ON t.team_id = s.team_id
            GROUP BY t.team_id, t.team_name
            HAVING total_seasons >= %s
            ORDER BY total_points DESC, avg_xg_diff DESC, t.team_name ASC
            LIMIT %s
        """
        rows = db.execute_query(sql, params=[min_seasons, limit]) or []

        return jsonify({
            "success": True,
            "min_seasons": min_seasons,
            "limit": limit,
            "items": rows
        })
    except Exception as e:
        logger.exception("Error in /api/teams/summary: %s", e)
        return jsonify({"success": False, "error": "Database error", "items": []}), 500
@app.route("/api/seasons/advanced_analysis", methods=["GET"])
def api_seasons_advanced_analysis():
    """
    Simplified but still complex query:
    - Nested Query
    - 4+ Table Join
    - Group By
    - Outer Join
    GET /api/seasons/advanced_analysis?year=2024
    """
    year = request.args.get("year")
    limit = int(request.args.get("limit", 20))
    limit = min(max(limit, 1), 50)
    params = []

    where_clause = ""
    if year:
        where_clause = "AND s.year = %s"
        params.append(year)

    sql = f"""
        SELECT
            t.team_id,
            t.team_name,
            s.year,

            -- SEASON stats (aggregated)
            MAX(s.pts) AS total_points,
            MAX(s.wins) AS wins,
            MAX(s.draws) AS draws,
            MAX(s.loses) AS loses,
            ROUND(AVG(s.xG), 2) AS avg_xG,
            ROUND(AVG(s.xGA), 2) AS avg_xGA,

            -- MATCH + SHOT summary
            SUM(CASE WHEN sd.result='Goal' THEN 1 ELSE 0 END) AS total_goals,
            COUNT(sd.shot_id) AS total_shots,
            ROUND(SUM(sd.xG), 2) AS total_xg,

            -- Conversion Rate
            ROUND(
                SUM(CASE WHEN sd.result='Goal' THEN 1 ELSE 0 END)
                / NULLIF(COUNT(sd.shot_id), 0), 3
            ) AS conv_rate,

            -- Nested subquery: top scorer name
            (
                SELECT p2.player_name
                FROM player p2
                WHERE p2.team_title = t.team_name
                  AND p2.year = s.year
                ORDER BY p2.goals DESC
                LIMIT 1
            ) AS top_scorer,

            -- Nested subquery: league average xG for that season
            (
                SELECT ROUND(AVG(sd2.xG), 3)
                FROM shot_data sd2
                INNER JOIN match_info mi2 ON mi2.match_id = sd2.match_id
                WHERE mi2.season = s.year
            ) AS league_avg_xg

        FROM teams t
        LEFT JOIN season s ON s.team_id = t.team_id
        LEFT JOIN match_info mi ON mi.team_h = t.team_name OR mi.team_a = t.team_name
        LEFT JOIN shot_data sd ON sd.match_id = mi.match_id

        WHERE s.year IS NOT NULL
        {where_clause}

        GROUP BY t.team_id, t.team_name, s.year
        ORDER BY total_points DESC, avg_xG DESC
        LIMIT %s
    """

    try:
        rows = db.execute_query(sql, params + [limit]) or []
        return jsonify({"success": True, "items": rows})
    except Exception as e:
        logger.exception("Error in /api/seasons/advanced_analysis: %s", e)
        return jsonify({"success": False, "error": "Database error", "items": []}), 500
@app.route("/seasons/advanced-analysis")
def seasons_advanced_analysis_page():
    return render_template("seasons_advanced_analysis.html", title="Seasons Advanced Analysis")

#--------------BILGE-END-------------------------------


#--------------TALHA-START-----------------------------

# --- TALHA: Authentication Middleware --- #
def talha_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            # Check if it's an API request
            if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                return jsonify({
                    "success": False,
                    "message": "Authentication required",
                    "error": "unauthorized"
                }), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

@app.route("/players")
def players():
    """Players sayfası"""
    return render_template("players.html", title="Players")

@app.route("/players/add")
@talha_login_required
def players_add_page():
    """Add player form page (requires login)"""
    return render_template("add_player.html", title="Add Player")

@app.route("/players/edit")
@talha_login_required
def players_edit_page():
    """Edit player form page (requires login)"""
    return render_template("edit_player.html", title="Edit Players")
    
@app.route("/api/players/fut23", methods=['GET'])
def api_fut23_all():
    """Get all rows from fut23 table"""
    try:
        query = "SELECT * FROM fut23"
        results = db.execute_query(query)
        return jsonify({"players": results or [], "count": len(results) if results else 0})
    except Exception as e:
        logger.exception("Error fetching fut23 data: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/top/assists", methods=['GET'])
def api_top_assists():
    """Get top 3 players by assists"""
    try:
        query = """
            SELECT 
                player_id, 
                player_name, 
                assists, 
                team_title, 
                position
            FROM player 
            WHERE assists IS NOT NULL 
            ORDER BY assists DESC 
            LIMIT 3
        """
        results = db.execute_query(query)
        return jsonify({"players": results or []})
    except Exception as e:
        logger.exception("Error fetching top assists: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/top/goals", methods=['GET'])
def api_top_goals():
    """Get top 1 player by goals"""
    try:
        query = """
            SELECT 
                player_id, 
                player_name, 
                goals, 
                team_title, 
                position
            FROM player 
            WHERE goals IS NOT NULL 
            ORDER BY goals DESC 
            LIMIT 1
        """
        results = db.execute_query(query)
        return jsonify({"player": results[0] if results else None})
    except Exception as e:
        logger.exception("Error fetching top goals: %s", e)
        return jsonify({"error": "Database error", "player": None}), 500

# Comparison helpers
def _ensure_compare_list():
    if "compare_list" not in session or not isinstance(session.get("compare_list"), list):
        session["compare_list"] = []
    # Enforce limit of 4
    session["compare_list"] = session["compare_list"][:4]

@app.route("/api/players/compare/list", methods=['GET'])
def api_compare_list():
    """Return current comparison list (player_ids)"""
    _ensure_compare_list()
    return jsonify({"players": session["compare_list"]})

@app.route("/api/players/compare/add/<int:player_id>", methods=['POST'])
def api_compare_add(player_id):
    """Add a player to comparison list (max 4)"""
    _ensure_compare_list()
    compare = session["compare_list"]
    if player_id in compare:
        return jsonify({"players": compare, "message": "Already added"})
    if len(compare) >= 4:
        return jsonify({"players": compare, "error": "Limit reached"}), 400
    compare.append(player_id)
    session["compare_list"] = compare
    session.modified = True
    return jsonify({"players": compare})

@app.route("/api/players/compare/remove/<int:player_id>", methods=['POST'])
def api_compare_remove(player_id):
    """Remove a player from comparison list"""
    _ensure_compare_list()
    compare = session["compare_list"]
    compare = [pid for pid in compare if pid != player_id]
    session["compare_list"] = compare
    session.modified = True
    return jsonify({"players": compare})

@app.route("/api/players/compare/data", methods=['GET'])
def api_compare_data():
    """Return detailed data for players in comparison list"""
    _ensure_compare_list()
    compare = session["compare_list"]
    if not compare:
        return jsonify({"players": []})

    placeholders = ", ".join(["%s"] * len(compare))
    query = f"""
        SELECT 
            p.player_id,
            p.player_name,
            p.team_title,
            p.position,
            p.games,
            p.goals,
            p.assists,
            p.xG,
            p.shots,
            p.key_passes,
            p.time,
            p.yellow_cards,
            p.red_cards,
            f.Rating,
            f.Pace,
            f.Shoot,
            f.Pass,
            f.Drible,
            f.Defense,
            f.Physical,
            f.Skill,
            f.Weak_foot
        FROM player p
        LEFT JOIN fut23 f ON p.player_id = f.player_id
        WHERE p.player_id IN ({placeholders})
    """
    try:
        results = db.execute_query(query, params=compare)
        # preserve order as in session
        result_map = {r["player_id"]: r for r in results or []}
        ordered = [result_map[pid] for pid in compare if pid in result_map]
        return jsonify({"players": ordered})
    except Exception as e:
        logger.exception("Error fetching comparison data: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/players/compare")
def players_compare_page():
    """Render comparison page"""
    return render_template("player_compare.html", title="Compare Players")

@app.route("/api/quotes/random", methods=['GET'])
def api_random_quote():
    """Fetch a random quote filtered by selected categories from api-ninjas"""
    api_key = os.getenv("API_NINJAS_KEY")
    if not api_key:
        return jsonify({"error": "API key missing"}), 500

    categories = "wisdom,success,inspirational,courage,leadership"
    url = f"https://api.api-ninjas.com/v2/randomquotes?categories={categories}"

    try:
        resp = requests.get(
            url,
            headers={"X-Api-Key": api_key},
            timeout=8
        )
        if resp.status_code != 200:
            return jsonify({"error": "Quote service error"}), resp.status_code

        payload = resp.json()
        if isinstance(payload, list) and payload:
            item = payload[0]
            return jsonify({
                "quote": item.get("quote"),
                "author": item.get("author"),
                "work": item.get("work"),
                "categories": item.get("categories")
            })
        return jsonify({"error": "No quote found"}), 502
    except requests.RequestException as e:
        logger.exception("Quote fetch failed: %s", e)
        return jsonify({"error": "Quote fetch failed"}), 500

@app.route("/api/players/analysis", methods=['GET'])
def api_players_analysis():
    """Get players with most goals but least FIFA ratings (joined player + fut23 tables)"""
    try:
        query = """
        SELECT 
            p.player_id,
            p.player_name,
            p.goals,
            p.assists,
            p.games,
            p.xG,
            p.position,
            p.team_title,
            p.year,
            f.Rating AS fifa_rating,
            f.Pace,
            f.Shoot,
            f.Pass,
            f.Drible,
            f.Defense,
            f.Physical,
            f.Base_Stats,
            f.In_Game_Stats,
            f.Country,
            f.League
        FROM player p
        INNER JOIN fut23 f ON p.player_id = f.player_id
        WHERE p.goals IS NOT NULL AND f.Rating IS NOT NULL
        ORDER BY p.goals DESC, f.Rating ASC
        LIMIT 50
        """
        results = db.execute_query(query)
        return jsonify({
            "players": results or [], 
            "count": len(results) if results else 0,
            "description": "Players with most goals and least FIFA ratings"
        })
    except Exception as e:
        logger.exception("Error fetching player analysis data: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/search", methods=['GET'])
def api_players_search():
    """Search players by name, team, or position"""
    try:
        search_query = request.args.get('q', '').strip()
        if not search_query:
            return jsonify({"players": [], "count": 0})

        # Optional filters
        year = request.args.get('year', '').strip()
        team = request.args.get('team', '').strip()
        position = request.args.get('position', '').strip()
        
        # Use LIKE for partial matching
        search_pattern = f"%{search_query}%"

        where = ["(p.player_name LIKE %s OR p.team_title LIKE %s OR p.position LIKE %s)"]
        params = [search_pattern, search_pattern, search_pattern]

        if year:
            try:
                year_i = int(year)
                where.append("p.year = %s")
                params.append(year_i)
            except Exception:
                return jsonify({"error": "year must be a number", "players": []}), 400

        if team:
            where.append("p.team_title LIKE %s")
            params.append(f"%{team}%")

        if position:
            where.append("p.position LIKE %s")
            params.append(f"%{position}%")

        query = f"""
            SELECT DISTINCT
                p.season_player_id,
                p.player_id,
                p.player_name,
                p.goals,
                p.assists,
                p.games,
                p.xG,
                p.position,
                p.team_title,
                p.year,
                f.Rating AS fifa_rating,
                f.Pace,
                f.Shoot,
                f.Pass,
                f.Drible,
                f.Defense,
                f.Physical,
                f.Country,
                f.League
            FROM player p
            LEFT JOIN fut23 f ON p.player_id = f.player_id
            WHERE {" AND ".join(where)}
            ORDER BY p.player_name
            LIMIT 50
        """

        results = db.execute_query(query, params=params)
        return jsonify({
            "players": results or [], 
            "count": len(results) if results else 0
        })
    except Exception as e:
        logger.exception("Error searching players: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500


@app.route("/api/players/season/<int:season_player_id>", methods=["GET"])
def api_player_by_season_id(season_player_id):
    """Fetch a single player row by season_player_id (primary key)."""
    try:
        query = """
            SELECT
                season_player_id, player_id, player_name, games, time,
                goals, xG, assists, xA, shots, key_passes,
                yellow_cards, red_cards, position, team_title,
                npg, npxG, xGChain, xGBuildup, year, best_shot_id
            FROM player
            WHERE season_player_id = %s
            LIMIT 1
        """
        rows = db.execute_query(query, [season_player_id])
        if not rows:
            return jsonify({"success": False, "error": "Player season row not found"}), 404
        return jsonify({"success": True, "player": rows[0]})
    except Exception as e:
        logger.exception("Error fetching player season row: %s", e)
        return jsonify({"success": False, "error": "Database error"}), 500


@app.route("/api/players/season/<int:season_player_id>/update", methods=["POST"])
@talha_login_required
def api_player_season_update(season_player_id):
    """Update a player row (by season_player_id)."""
    data = request.get_json(silent=True) or {}

    def _to_int(v):
        if v in (None, ""):
            return None
        try:
            return int(v)
        except Exception:
            return None

    def _to_float(v):
        if v in (None, ""):
            return None
        try:
            return float(v)
        except Exception:
            return None

    # Updatable fields (exclude season_player_id primary key)
    player_name = (data.get("player_name") or "").strip()
    year_i = _to_int(data.get("year"))
    if not player_name or year_i is None:
        return jsonify({"success": False, "error": "player_name and year are required"}), 400

    update = {
        "player_name": player_name,
        "year": year_i,
        "team_title": (data.get("team_title") or "").strip() or None,
        "position": (data.get("position") or "").strip() or None,
        "games": _to_int(data.get("games")),
        "time": _to_int(data.get("time")),
        "goals": _to_int(data.get("goals")),
        "xG": _to_float(data.get("xG")),
        "assists": _to_int(data.get("assists")),
        "xA": _to_float(data.get("xA")),
        "shots": _to_int(data.get("shots")),
        "key_passes": _to_int(data.get("key_passes")),
        "yellow_cards": _to_int(data.get("yellow_cards")),
        "red_cards": _to_int(data.get("red_cards")),
        "npg": _to_int(data.get("npg")),
        "npxG": _to_float(data.get("npxG")),
        "xGChain": _to_float(data.get("xGChain")),
        "xGBuildup": _to_float(data.get("xGBuildup")),
        "best_shot_id": _to_int(data.get("best_shot_id")),
    }

    try:
        # Fetch existing row (need player_id for uniqueness checks)
        existing_rows = db.execute_query(
            "SELECT season_player_id, player_id, year FROM player WHERE season_player_id=%s LIMIT 1",
            [season_player_id],
        )
        if not existing_rows:
            return jsonify({"success": False, "error": "Player season row not found"}), 404

        existing = existing_rows[0]
        player_id_i = existing.get("player_id")

        # Validate best_shot_id FK if provided
        if update["best_shot_id"] is not None:
            shot_exists = db.execute_query(
                "SELECT shot_id FROM shot_data WHERE shot_id=%s LIMIT 1",
                [update["best_shot_id"]],
            )
            if not shot_exists:
                return jsonify({"success": False, "error": "best_shot_id does not exist"}), 400

        # Prevent duplicates: same player_id + year for a different season_player_id
        if player_id_i is not None:
            dup = db.execute_query(
                "SELECT season_player_id FROM player WHERE player_id=%s AND year=%s AND season_player_id<>%s LIMIT 1",
                [player_id_i, update["year"], season_player_id],
            )
            if dup:
                return jsonify({"success": False, "error": "Another row already exists for this player_id and year"}), 409

        set_parts = []
        params = []
        for k, v in update.items():
            set_parts.append(f"{k}=%s")
            params.append(v)
        params.append(season_player_id)

        sql = f"UPDATE player SET {', '.join(set_parts)} WHERE season_player_id=%s"
        db.execute_query(sql, params, fetch_all=False)
        return jsonify({"success": True, "message": "Player updated successfully"})
    except Exception as e:
        logger.exception("Error updating player season row: %s", e)
        return jsonify({"success": False, "error": "Database error"}), 500


@app.route("/api/players", methods=["POST"])
@talha_login_required
def api_player_create():
    """
    Create a player row in `player` table.
    Required: player_name, year
    Optional: any other `player` columns
    """
    data = request.get_json(silent=True) or {}

    # Required fields
    player_name = (data.get("player_name") or "").strip()
    player_id = data.get("player_id")
    year = data.get("year")

    if not player_name or year in (None, ""):
        return jsonify({"success": False, "error": "player_name and year are required"}), 400

    # Normalize numeric types (best effort)
    def _to_int(v):
        if v in (None, ""):
            return None
        try:
            return int(v)
        except Exception:
            return None

    def _to_float(v):
        if v in (None, ""):
            return None
        try:
            return float(v)
        except Exception:
            return None

    year_i = _to_int(year)
    if year_i is None:
        return jsonify({"success": False, "error": "year must be a number"}), 400

    player_id_i = _to_int(player_id)
    if player_id not in (None, "") and player_id_i is None:
        return jsonify({"success": False, "error": "player_id must be a number"}), 400

    # Optional fields
    season_player_id = _to_int(data.get("season_player_id"))
    best_shot_id = _to_int(data.get("best_shot_id"))

    row = {
        "season_player_id": season_player_id,  # may be None -> auto-generate
        "player_id": player_id_i,
        "player_name": player_name,
        "games": _to_int(data.get("games")),
        "time": _to_int(data.get("time")),
        "goals": _to_int(data.get("goals")),
        "xG": _to_float(data.get("xG")),
        "assists": _to_int(data.get("assists")),
        "xA": _to_float(data.get("xA")),
        "shots": _to_int(data.get("shots")),
        "key_passes": _to_int(data.get("key_passes")),
        "yellow_cards": _to_int(data.get("yellow_cards")),
        "red_cards": _to_int(data.get("red_cards")),
        "position": (data.get("position") or "").strip() or None,
        "team_title": (data.get("team_title") or "").strip() or None,
        "npg": _to_int(data.get("npg")),
        "npxG": _to_float(data.get("npxG")),
        "xGChain": _to_float(data.get("xGChain")),
        "xGBuildup": _to_float(data.get("xGBuildup")),
        "year": year_i,
        "best_shot_id": best_shot_id,
    }

    try:
        # Duplicate protection:
        # - If player_id is provided: enforce uniqueness of (player_id, year)
        # - If player_id is missing: prevent duplicates of (player_name, year [, team_title])
        if player_id_i is not None:
            exists = db.execute_query(
                "SELECT season_player_id FROM player WHERE player_id=%s AND year=%s LIMIT 1",
                [player_id_i, year_i],
            )
            if exists:
                return jsonify({"success": False, "error": "Player already exists for this year (same player_id)"}), 409
        else:
            if row.get("team_title"):
                exists = db.execute_query(
                    "SELECT season_player_id FROM player WHERE player_name=%s AND year=%s AND team_title=%s LIMIT 1",
                    [player_name, year_i, row.get("team_title")],
                )
            else:
                exists = db.execute_query(
                    "SELECT season_player_id FROM player WHERE player_name=%s AND year=%s LIMIT 1",
                    [player_name, year_i],
                )
            if exists:
                return jsonify({"success": False, "error": "Player already exists for this year (same name)"}), 409

        # Validate best_shot_id FK if provided
        if best_shot_id is not None:
            shot_exists = db.execute_query(
                "SELECT shot_id FROM shot_data WHERE shot_id=%s LIMIT 1",
                [best_shot_id],
            )
            if not shot_exists:
                return jsonify({"success": False, "error": "best_shot_id does not exist"}), 400

        # Auto-generate player_id if missing
        if player_id_i is None:
            r = db.execute_query(
                """
                SELECT
                    GREATEST(
                        (SELECT COALESCE(MAX(player_id), 0) FROM player),
                        (SELECT COALESCE(MAX(player_id), 0) FROM fut23)
                    ) + 1 AS next_player_id
                """
            )
            player_id_i = int((r or [{}])[0].get("next_player_id") or 1)
            row["player_id"] = player_id_i

        # Auto-generate season_player_id if missing
        if row["season_player_id"] is None:
            r = db.execute_query("SELECT COALESCE(MAX(season_player_id), 0) + 1 AS next_id FROM player")
            row["season_player_id"] = int((r or [{}])[0].get("next_id") or 1)

        sql = """
            INSERT INTO player (
                season_player_id, player_id, player_name, games, time,
                goals, xG, assists, xA, shots, key_passes,
                yellow_cards, red_cards, position, team_title,
                npg, npxG, xGChain, xGBuildup, year, best_shot_id
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """

        params = (
            row["season_player_id"], row["player_id"], row["player_name"], row["games"], row["time"],
            row["goals"], row["xG"], row["assists"], row["xA"], row["shots"], row["key_passes"],
            row["yellow_cards"], row["red_cards"], row["position"], row["team_title"],
            row["npg"], row["npxG"], row["xGChain"], row["xGBuildup"], row["year"], row["best_shot_id"]
        )

        db.execute_query(sql, params, fetch_all=False)
        return jsonify({
            "success": True,
            "message": "Player added successfully",
            "season_player_id": row["season_player_id"],
            "player_id": row["player_id"],
        }), 201
    except Exception as e:
        logger.exception("Error creating player: %s", e)
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/players/<int:player_id>", methods=['GET'])
def api_player_detail(player_id):
    """Get full player details by player_id"""
    try:
        query = """
        SELECT 
            p.best_shot_id,
            p.season_player_id,
            p.player_id,
            p.player_name,
            p.games,
            p.time,
            p.goals,
            p.xG,
            p.assists,
            p.xA,
            p.shots,
            p.key_passes,
            p.yellow_cards,
            p.red_cards,
            p.position,
            p.team_title,
            p.npg,
            p.npxG,
            p.xGChain,
            p.xGBuildup,
            p.year,
            f.Name AS fut23_name,
            f.Team AS fut23_team,
            f.team_id,
            f.Country,
            f.League,
            f.Rating,
            f.Position AS fut23_position,
            f.Other_Positions,
            f.Run_type,
            f.Price,
            f.Skill,
            f.Weak_foot,
            f.Attack_rate,
            f.Defense_rate,
            f.Pace,
            f.Shoot,
            f.Pass,
            f.Drible,
            f.Defense,
            f.Physical,
            f.Body_type,
            f.Height_cm,
            f.Weight,
            f.Popularity,
            f.Base_Stats,
            f.In_Game_Stats
        FROM player p
        LEFT JOIN fut23 f ON p.player_id = f.player_id
        WHERE p.player_id = %s
        LIMIT 1
        """
        results = db.execute_query(query, params=[player_id])
        if not results or len(results) == 0:
            return jsonify({"error": "Player not found"}), 404
        player = results[0]

        # Fallback: if best_shot_id is missing, pick the highest xG shot for this player
        if not player.get("best_shot_id"):
            try:
                best_shot_query = """
                    SELECT shot_id
                    FROM shot_data
                    WHERE player_id = %s
                    ORDER BY xG DESC
                    LIMIT 1
                """
                best_results = db.execute_query(best_shot_query, (player_id,), fetch_all=True)
                if best_results and len(best_results) > 0:
                    player["best_shot_id"] = best_results[0]["shot_id"]
            except Exception as _:
                # Swallow fallback errors silently; API still returns player data
                pass

        return jsonify({"player": player})
    except Exception as e:
        logger.exception("Error fetching player detail: %s", e)
        return jsonify({"error": "Database error"}), 500

@app.route("/players/<int:player_id>")
def player_detail(player_id):
    """Individual player detail page"""
    return render_template("player_detail.html", title="Player Details", player_id=player_id)

# ========= COMPLEX QUERIES  =========

@app.route("/api/players/complex/goals-per-match", methods=['GET'])
def api_players_complex_goals_per_match():
    """
    COMPLEX QUERY 1: Complex Join of 4+ tables with GROUP BY and HAVING
    
    This query demonstrates:
    - Complex Join: Joins 4 tables (player, fut23, match_data, match_info)
    - GROUP BY: Groups by player_name and Rating
    - HAVING: Filters groups with goals_per_match > 0.5
    - Aggregate functions: SUM and COUNT with DISTINCT
    
    Returns players with their FIFA ratings and calculated goals per match,
    filtered to only show players with more than 0.5 goals per match.
    """
    try:
        query = """
            SELECT 
                p.player_name,
                f.Rating,
                SUM(p.goals) / COUNT(DISTINCT mi.match_id) AS goals_per_match
            FROM player p
            JOIN fut23 f ON p.player_id = f.player_id
            JOIN match_data md ON md.h_id = f.team_id OR md.a_id = f.team_id
            JOIN match_info mi ON mi.match_id = md.match_id
            GROUP BY p.player_name, f.Rating
            HAVING goals_per_match > 0.5
            ORDER BY goals_per_match DESC
        """
        results = db.execute_query(query)
        return jsonify({
            "players": results or [],
            "count": len(results) if results else 0,
            "description": "Players with goals per match > 0.5 (Complex Join of 4+ tables, GROUP BY, HAVING)"
        })
    except Exception as e:
        logger.exception("Error fetching goals per match: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/complex/above-average-goals", methods=['GET'])
def api_players_complex_above_average_goals():
    """
    COMPLEX QUERY 2: Nested Query (Correlated Subquery)
    
    This query demonstrates:
    - Nested Query: Uses a correlated subquery in the WHERE clause
    - Subquery calculates AVG(goals) for each year
    - Main query filters players whose goals exceed the year's average
    
    Returns players who scored more goals than the average for their year.
    """
    try:
        query = """
            SELECT 
                p.player_name,
                p.goals,
                p.year
            FROM player p
            WHERE p.goals > (
                SELECT AVG(goals)
                FROM player
                WHERE year = p.year
            )
            ORDER BY p.goals DESC
        """
        results = db.execute_query(query)
        return jsonify({
            "players": results or [],
            "count": len(results) if results else 0,
            "description": "Players with goals above year average (Nested Query)"
        })
    except Exception as e:
        logger.exception("Error fetching above average goals: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/complex/low-games-best-rating", methods=['GET'])
def api_players_complex_low_games_best_rating():
    """
    COMPLEX QUERY 3: LEFT JOIN (Outer Join) with GROUP BY and HAVING
    
    This query demonstrates:
    - LEFT JOIN: Outer join between fut23 and player tables
    - GROUP BY: Groups by player name and rating
    - HAVING: Filters groups with total_games < 5
    - Aggregate functions: SUM and COALESCE
    
    Returns players who have played less than 5 games, ordered by best FIFA rating.
    """
    try:
        query = """
            SELECT 
                f.Name AS player_name,
                f.Rating,
                COALESCE(SUM(p.games), 0) AS total_games
            FROM fut23 f
            LEFT JOIN player p ON f.player_id = p.player_id
            GROUP BY f.Name, f.Rating
            HAVING total_games < 5
            ORDER BY f.Rating DESC
        """
        results = db.execute_query(query)
        return jsonify({
            "players": results or [],
            "count": len(results) if results else 0,
            "description": "Players with less than 5 games and best FIFA rating (Outer Join with GROUP BY and HAVING)"
        })
    except Exception as e:
        logger.exception("Error fetching players with less than 5 games and best FIFA rating: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/complex/top-goals-with-rating", methods=['GET'])
def api_players_complex_top_goals_with_rating():
    """
    COMPLEX QUERY 4: JOIN with GROUP BY
    
    This query demonstrates:
    - JOIN: Inner join between player and fut23 tables
    - GROUP BY: Groups by player_name and Rating
    - Aggregate functions: SUM to calculate total goals
    - ORDER BY and LIMIT: Orders by total goals descending, limits to top 10
    
    Returns the top 10 players by total goals who have FIFA ratings.
    """
    try:
        query = """
            SELECT 
                p.player_name,
                SUM(p.goals) AS total_goals,
                f.Rating
            FROM player p
            JOIN fut23 f ON p.player_id = f.player_id
            GROUP BY p.player_name, f.Rating
            ORDER BY total_goals DESC
            LIMIT 10
        """
        results = db.execute_query(query)
        return jsonify({
            "players": results or [],
            "count": len(results) if results else 0,
            "description": "Top 10 players by goals with FIFA ratings (JOIN with GROUP BY)"
        })
    except Exception as e:
        logger.exception("Error fetching top goals with rating: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/complex/comprehensive-stats", methods=['GET'])
def api_players_complex_comprehensive_stats():
    """
    COMPLEX QUERY 5: All Features Combined - Nested Query, Complex Join (4+ tables), GROUP BY, Outer Join
    
    This query demonstrates:
    - Nested Query: Uses a correlated subquery to calculate average goals for players in the same position and year
    - Complex Join (4+ tables): Joins player, fut23, teams, match_info, match_data, and shot_data (6 tables)
    - GROUP BY: Groups by player attributes to aggregate statistics and calculate goals per game
    - Outer Join (LEFT JOIN): Uses LEFT JOINs to include players even without FIFA ratings, team info, matches, or shot data
    
    Returns top players with their performance metrics and position average goals for comparison.
    """
    try:
        query = """
            SELECT 
                p.player_name,
                t.team_name AS team_title,
                f.Position AS position,
                p.goals,
                p.assists,
                p.games,
                p.xG,
                CASE WHEN p.games > 0 THEN p.goals / p.games ELSE 0 END AS goals_per_game,
                (
                    SELECT AVG(p2.goals)
                    FROM player p2
                    LEFT JOIN fut23 f2 ON p2.player_id = f2.player_id
                    WHERE f2.Position = f.Position 
                    AND p2.year = p.year
                    AND p2.games > 0
                    AND f2.Position IS NOT NULL
                    AND p2.goals IS NOT NULL
                ) AS position_avg_goals,
                f.Rating AS fifa_rating,
                f.Pace,
                f.Shoot,
                f.Pass,
                f.Defense,
                f.Physical,
                p.year,
                (
                    SELECT COUNT(DISTINCT sd2.shot_id)
                    FROM shot_data sd2
                    WHERE sd2.player_id = p.player_id
                ) AS total_shots
            FROM player p
            LEFT JOIN fut23 f ON p.player_id = f.player_id
            LEFT JOIN teams t ON f.team_id = t.team_id
            LEFT JOIN match_info mi ON (mi.h = f.team_id OR mi.a = f.team_id) AND mi.season = p.year
            LEFT JOIN match_data md ON md.match_id = mi.match_id
            WHERE p.games > 0 AND p.goals > 0 AND f.Position IS NOT NULL
            GROUP BY p.season_player_id, p.player_id, p.player_name, p.games, p.goals, p.assists, p.xG, 
                     f.Rating, f.Position, t.team_name, f.Pace, f.Shoot, f.Pass, f.Defense, f.Physical, p.year
            ORDER BY p.goals DESC, f.Rating DESC
            LIMIT 50
        """
        results = db.execute_query(query)
        return jsonify({
            "players": results or [],
            "count": len(results) if results else 0,
            "description": "Top players with stats vs position averages (Nested Query, 4+ Table Joins, GROUP BY, Outer Join)"
        })
    except Exception as e:
        logger.exception("Error fetching comprehensive player stats: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

#--------------TALHA-END-------------------------------



@app.route("/osman")
def osman():
    """Osman sayfası"""
    return render_template("osman.html", title="Osman")
#--------------OSMAN-START-----------------------------
#2sr -------------------------------------------------------------------------------------------------------------------------------


@app.route('/shots')
def index():
    """Homepage with search interface"""
    return render_template('shot_search.html')

@app.route('/shot/<int:shot_id>')
def shot_detail(shot_id):
    """Display detailed shot information"""
    try:
        # Get shot details with match information
        shot_query = """
            SELECT 
                s.shot_id,
                s.minute,
                s.result,
                s.X,
                s.Y,
                s.xG,
                s.player,
                s.h_a,
                s.player_id,
                s.situation,
                s.season,
                s.shotType,
                s.match_id,
                s.h_team,
                s.a_team,
                s.h_goals,
                s.a_goals,
                s.date,
                s.player_assisted,
                s.lastAction,
                m.league,
                m.h_xg,
                m.a_xg
            FROM shot_data s
            LEFT JOIN match_info m ON s.match_id = m.match_id
            WHERE s.shot_id = %s
        """
        
        shot_results = db.execute_query(shot_query, (shot_id,), fetch_all=True)
        
        if not shot_results:
            return render_template('error.html', 
                                 error="Shot not found", 
                                 message=f"No shot found with ID {shot_id}"), 404
        
        shot = shot_results[0]
        
        # Get player information from player table
        player_query = """
            SELECT 
                p.season_player_id,
                p.player_id,
                p.player_name,
                p.games,
                p.time,
                p.goals,
                p.xG,
                p.assists,
                p.xA,
                p.shots,
                p.key_passes,
                p.yellow_cards,
                p.red_cards,
                p.position,
                p.team_title,
                p.npg,
                p.npxG,
                p.xGChain,
                p.xGBuildup,
                p.year
            FROM player p
            WHERE p.player_id = %s AND p.year = %s
        """
        
        player_results = db.execute_query(
            player_query, 
            (shot['player_id'], shot['season']), 
            fetch_all=True
        )
        
        player = player_results[0] if player_results else None
        
        # Get other shots by this player in the same match
        other_shots_query = """
            SELECT 
                shot_id,
                minute,
                result,
                xG,
                situation,
                shotType
            FROM shot_data
            WHERE player_id = %s 
            AND match_id = %s 
            AND shot_id != %s
            ORDER BY minute ASC
        """
        
        other_shots = db.execute_query(
            other_shots_query,
            (shot['player_id'], shot['match_id'], shot_id),
            fetch_all=True
        )
        
        # Get player's season statistics for comparison
        season_stats_query = """
            SELECT 
                COUNT(*) as total_shots,
                SUM(CASE WHEN result = 'Goal' THEN 1 ELSE 0 END) as goals_scored,
                AVG(xG) as avg_xg,
                SUM(xG) as total_xg
            FROM shot_data
            WHERE player_id = %s AND season = %s
        """
        
        season_stats_results = db.execute_query(
            season_stats_query,
            (shot['player_id'], shot['season']),
            fetch_all=True
        )
        
        season_stats = season_stats_results[0] if season_stats_results else None
        
        # NEW: Get contextual statistics - complex query with 4 joins
        context_stats_query = """
            SELECT 
                -- Player's performance in similar situations
                COUNT(DISTINCT s.shot_id) as similar_shots_count,
                SUM(CASE WHEN s.result = 'Goal' THEN 1 ELSE 0 END) as similar_goals,
                AVG(s.xG) as avg_similar_xg,
                
                -- Team performance comparison
                AVG(CASE WHEN s.h_a = 'h' THEN m.h_xg ELSE m.a_xg END) as team_avg_match_xg,
                AVG(CASE WHEN s.h_a = 'h' THEN m.h_goals ELSE m.a_goals END) as team_avg_goals,
                
                -- Opposition defensive stats
                AVG(CASE WHEN s.h_a = 'h' THEN m.a_ppda ELSE m.h_ppda END) as opp_avg_ppda,
                AVG(CASE WHEN s.h_a = 'h' THEN sea.deep_allowed ELSE sea.deep END) as opp_deep_allowed,
                
                -- Player season form
                p.goals as player_season_goals,
                p.xG as player_season_xg,
                p.shots as player_season_shots,
                p.npg as player_non_penalty_goals,
                p.xGChain as player_xg_chain,
                
                -- League context
                COUNT(DISTINCT CASE WHEN league_shots.result = 'Goal' THEN league_shots.shot_id END) as league_similar_goals,
                COUNT(DISTINCT league_shots.shot_id) as league_similar_shots,
                AVG(league_shots.xG) as league_avg_similar_xg
                
            FROM shot_data s
            
            -- Join 1: Get match information
            INNER JOIN match_info m ON s.match_id = m.match_id
            
            -- Join 2: Get player season stats
            LEFT JOIN player p ON s.player_id = p.player_id AND s.season = p.year
            
            -- Join 3: Get team season defensive stats (opponent)
            LEFT JOIN season sea ON 
                CASE 
                    WHEN s.h_a = 'h' THEN m.a = sea.team_id
                    ELSE m.h = sea.team_id
                END
                AND m.season = sea.year
                AND m.date = sea.date
            
            -- Join 4: Self join to get league-wide similar shots
            LEFT JOIN shot_data league_shots ON 
                league_shots.season = s.season
                AND league_shots.situation = s.situation
                AND league_shots.shotType = s.shotType
                AND ABS(league_shots.xG - s.xG) < 0.1
                AND league_shots.shot_id != s.shot_id
            
            WHERE s.shot_id = %s
                AND s.player_id = %s
                AND s.situation = (SELECT situation FROM shot_data WHERE shot_id = %s)
                AND s.shotType = (SELECT shotType FROM shot_data WHERE shot_id = %s)
                AND s.season = (SELECT season FROM shot_data WHERE shot_id = %s)
                AND ABS(s.xG - (SELECT xG FROM shot_data WHERE shot_id = %s)) < 0.15
            
            GROUP BY 
                p.goals, p.xG, p.shots, p.npg, p.xGChain
        """
        
        context_stats_results = db.execute_query(
            context_stats_query,
            (shot_id, shot['player_id'], shot_id, shot_id, shot_id, shot_id),
            fetch_all=True
        )
        
        context_stats = context_stats_results[0] if context_stats_results else None
        
        return render_template('shot_detail.html',
                             shot=shot,
                             player=player,
                             other_shots=other_shots,
                             season_stats=season_stats,
                             context_stats=context_stats)
        
    except Exception as e:
        logger.exception(f"Error fetching shot {shot_id}: {e}")
        return render_template('error.html',
                             error="Database Error",
                             message=str(e)), 500
    
    
@app.route('/api/search/shots/advanced')
def search_shots_advanced():
    """Advanced API endpoint with complex filtering"""
    try:
        # Extract all filter parameters
        player_name = request.args.get('player', '').strip()
        team = request.args.get('team', '').strip()
        season = request.args.get('season', '').strip()
        league = request.args.get('league', '').strip()
        
        # Range filters
        xg_min = request.args.get('xg_min', '0')
        xg_max = request.args.get('xg_max', '1')
        minute_min = request.args.get('minute_min', '0')
        minute_max = request.args.get('minute_max', '120')
        
        # Multiple select filters
        results = request.args.getlist('results')
        shot_types = request.args.getlist('shot_types')
        situations = request.args.getlist('situations')
        positions = request.args.getlist('positions')
        assist_status = request.args.getlist('assist_status')
        
        limit = int(request.args.get('limit', 50))
        
        # Build dynamic query
        query = """
            SELECT 
                s.shot_id,
                s.player,
                s.h_team,
                s.a_team,
                s.minute,
                s.result,
                s.xG,
                s.situation,
                s.season,
                s.date,
                s.h_a,
                s.shotType,
                s.player_assisted,
                m.league
            FROM shot_data s
            LEFT JOIN match_info m ON s.match_id = m.match_id
            WHERE 1=1
        """
        
        params = []
        
        # Player filter
        if player_name:
            query += " AND s.player LIKE %s"
            params.append(f"%{player_name}%")
        
        # Team filter (both home and away)
        if team:
            query += " AND (s.h_team LIKE %s OR s.a_team LIKE %s)"
            params.append(f"%{team}%")
            params.append(f"%{team}%")
        
        # Season filter
        if season:
            query += " AND s.season = %s"
            params.append(int(season))
        
        # League filter
        if league:
            query += " AND m.league = %s"
            params.append(league)
        
        # xG range filter
        try:
            xg_min = float(xg_min)
            xg_max = float(xg_max)
            query += " AND s.xG BETWEEN %s AND %s"
            params.extend([xg_min, xg_max])
        except ValueError:
            pass
        
        # Minute range filter
        try:
            minute_min = int(minute_min)
            minute_max = int(minute_max)
            query += " AND s.minute BETWEEN %s AND %s"
            params.extend([minute_min, minute_max])
        except ValueError:
            pass
        
        # Shot result filter (multiple selections)
        if results:
            placeholders = ','.join(['%s'] * len(results))
            query += f" AND s.result IN ({placeholders})"
            params.extend(results)
        
        # Shot type filter
        if shot_types:
            placeholders = ','.join(['%s'] * len(shot_types))
            query += f" AND s.shotType IN ({placeholders})"
            params.extend(shot_types)
        
        # Situation filter
        if situations:
            placeholders = ','.join(['%s'] * len(situations))
            query += f" AND s.situation IN ({placeholders})"
            params.extend(situations)
        
        # Home/Away position filter
        if positions:
            placeholders = ','.join(['%s'] * len(positions))
            query += f" AND s.h_a IN ({placeholders})"
            params.extend(positions)
        
        # Assist status filter
        if assist_status:
            if 'assisted' in assist_status and 'unassisted' in assist_status:
                pass  # Both selected, no filter needed
            elif 'assisted' in assist_status:
                query += " AND s.player_assisted IS NOT NULL AND s.player_assisted != ''"
            elif 'unassisted' in assist_status:
                query += " AND (s.player_assisted IS NULL OR s.player_assisted = '')"
        
        # Order and limit
        query += " ORDER BY s.date DESC, s.minute DESC LIMIT %s"
        params.append(limit)
        
        results_data = db.execute_query(query, tuple(params), fetch_all=True)
        
        return jsonify({
            'success': True,
            'count': len(results_data),
            'shots': results_data,
            'applied_filters': {
                'player': player_name,
                'team': team,
                'season': season,
                'league': league,
                'xg_range': f"{xg_min}-{xg_max}",
                'minute_range': f"{minute_min}-{minute_max}",
                'results': results,
                'shot_types': shot_types,
                'situations': situations,
                'positions': positions,
                'assist_status': assist_status
            }
        })
        
    except Exception as e:
        logger.exception(f"Error in advanced search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/filters/options')
def get_filter_options():
    """Get available filter options for dropdown/select elements"""
    try:
        # Get unique seasons
        seasons_query = "SELECT DISTINCT season FROM shot_data ORDER BY season DESC"
        seasons = db.execute_query(seasons_query, fetch_all=True)
        
        # Get unique leagues
        leagues_query = "SELECT DISTINCT league FROM match_info WHERE league IS NOT NULL ORDER BY league"
        leagues = db.execute_query(leagues_query, fetch_all=True)
        
        # Get unique shot types
        shot_types_query = "SELECT DISTINCT shotType FROM shot_data WHERE shotType IS NOT NULL ORDER BY shotType"
        shot_types = db.execute_query(shot_types_query, fetch_all=True)
        
        # Get unique situations
        situations_query = "SELECT DISTINCT situation FROM shot_data WHERE situation IS NOT NULL ORDER BY situation"
        situations = db.execute_query(situations_query, fetch_all=True)
        
        return jsonify({
            'success': True,
            'seasons': [row['season'] for row in seasons],
            'leagues': [row['league'] for row in leagues],
            'shot_types': [row['shotType'] for row in shot_types],
            'situations': [row['situation'] for row in situations]
        })
        
    except Exception as e:
        logger.exception(f"Error fetching filter options: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
@app.route('/api/search/shots')
def search_shots():
    """API endpoint to search for shots"""
    try:
        player_name = request.args.get('player', '').strip()
        team = request.args.get('team', '').strip()
        season = request.args.get('season', '').strip()
        result = request.args.get('result', '').strip()
        limit = int(request.args.get('limit', 50))
        
        query = """
            SELECT 
                s.shot_id,
                s.player,
                s.h_team,
                s.a_team,
                s.minute,
                s.result,
                s.xG,
                s.situation,
                s.season,
                s.date,
                s.h_a
            FROM shot_data s
            WHERE 1=1
        """
        
        params = []
        
        if player_name:
            query += " AND s.player LIKE %s"
            params.append(f"%{player_name}%")
        
        if team:
            query += " AND (s.h_team LIKE %s OR s.a_team LIKE %s)"
            params.append(f"%{team}%")
            params.append(f"%{team}%")
        
        if season:
            query += " AND s.season = %s"
            params.append(int(season))
        
        if result:
            query += " AND s.result = %s"
            params.append(result)
        
        query += " ORDER BY s.date DESC, s.minute DESC LIMIT %s"
        params.append(limit)
        
        results = db.execute_query(query, tuple(params), fetch_all=True)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'shots': results
        })
        
    except Exception as e:
        logger.exception(f"Error searching shots: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/players/autocomplete')
def players_autocomplete():
    """API endpoint for player name autocomplete"""
    try:
        query_str = request.args.get('q', '').strip()
        
        if len(query_str) < 2:
            return jsonify([])
        
        query = """
            SELECT DISTINCT player, player_id
            FROM shot_data
            WHERE player LIKE %s
            ORDER BY player
            LIMIT 20
        """
        
        results = db.execute_query(query, (f"%{query_str}%",), fetch_all=True)
        
        return jsonify(results)
        
    except Exception as e:
        logger.exception(f"Error in autocomplete: {e}")
        return jsonify([]), 500


@app.route('/api/stats/player/<int:player_id>')
def player_stats_api(player_id):
    """API endpoint for player statistics"""
    try:
        query = """
            SELECT 
                p.*,
                COUNT(DISTINCT s.match_id) as matches_with_shots,
                COUNT(s.shot_id) as total_shots_taken,
                SUM(CASE WHEN s.result = 'Goal' THEN 1 ELSE 0 END) as goals_from_shots
            FROM player p
            LEFT JOIN shot_data s ON p.player_id = s.player_id AND p.year = s.season
            WHERE p.player_id = %s
            GROUP BY p.season_player_id
            ORDER BY p.year DESC
        """
        
        results = db.execute_query(query, (player_id,), fetch_all=True)
        
        return jsonify({
            'success': True,
            'player_stats': results
        })
        
    except Exception as e:
        logger.exception(f"Error fetching player stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# - - - - - - - - - - - - - - - - - - below is for admin page : 
# ==============================
# ADMIN TEAMS CRUD 
# ==============================

@app.route("/admin/teams", methods=["GET"])
@login_required
def admin_teams_page():
    # Shots gibi: sayfa render, veriyi JS çeker
    return render_template("admin_teams.html", username=session.get("username"))

@app.route("/api/admin/teams", methods=["GET", "POST"])
@login_required
def admin_teams_list_or_add():
    if request.method == "GET":
        # Pagination + search
        try:
            page = max(int(request.args.get("page", 1)), 1)
            limit = min(max(int(request.args.get("limit", 20)), 1), 200)
            q = (request.args.get("q", "") or "").strip()
            offset = (page - 1) * limit

            where = "WHERE 1=1"
            params = []
            if q:
                where += " AND team_name LIKE %s"
                params.append(f"%{q}%")

            total_row = db.execute_query(
                f"SELECT COUNT(*) AS total FROM teams {where}",
                tuple(params),
                fetch_all=True
            )
            total = total_row[0]["total"] if total_row else 0

            teams = db.execute_query(
                f"""
                SELECT team_id, team_name
                FROM teams
                {where}
                ORDER BY team_name ASC
                LIMIT %s OFFSET %s
                """,
                tuple(params + [limit, offset]),
                fetch_all=True
            ) or []

            return jsonify({"success": True, "teams": teams, "total": total, "page": page, "limit": limit})
        except Exception as e:
            logger.exception("Error listing teams: %s", e)
            return jsonify({"success": False, "error": "Database error"}), 500

    # POST: add
    data = request.get_json(silent=True) or {}
    name = (data.get("team_name") or "").strip()
    team_id = data.get("team_id", None)  

    if not name:
        return jsonify({"success": False, "error": "team_name is required"}), 400

    # validate team_id
    if team_id is not None and str(team_id).strip() != "":
        try:
            team_id = int(team_id)
        except Exception:
            return jsonify({"success": False, "error": "team_id must be an integer"}), 400
        if team_id <= 0:
            return jsonify({"success": False, "error": "team_id must be positive"}), 400

    try:
        if team_id is None or str(team_id).strip() == "":
            db.execute_query(
                "INSERT INTO teams (team_name) VALUES (%s)",
                (name,),
                fetch_all=False
            )
        else:
            db.execute_query(
                "INSERT INTO teams (team_id, team_name) VALUES (%s, %s)",
                (team_id, name),
                fetch_all=False
            )

        return jsonify({"success": True, "message": "Team added successfully"})
    except Exception as e:
        msg = str(e).lower()
        # MySQL duplicate key (1062) gibi durumlar
        if "1062" in msg or "duplicate" in msg:
            return jsonify({"success": False, "error": "Team id or team name already exists"}), 409

        logger.exception("Error adding team: %s", e)
        return jsonify({"success": False, "error": "Database error"}), 500


@app.route("/api/admin/teams/options", methods=["GET"])
@login_required
def admin_teams_options():
    # Seasons modal dropdown için
    try:
        teams = db.execute_query(
            "SELECT team_id, team_name FROM teams ORDER BY team_name ASC",
            fetch_all=True
        ) or []
        return jsonify({"success": True, "teams": teams})
    except Exception as e:
        logger.exception("Error loading team options: %s", e)
        return jsonify({"success": False, "teams": []}), 500


@app.route("/api/admin/teams/<int:team_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def admin_team_get_update_delete(team_id):
    if request.method == "GET":
        try:
            rows = db.execute_query(
                "SELECT team_id, team_name FROM teams WHERE team_id=%s LIMIT 1",
                (team_id,),
                fetch_all=True
            )
            if not rows:
                return jsonify({"success": False, "error": "Team not found"}), 404
            return jsonify({"success": True, "team": rows[0]})
        except Exception as e:
            logger.exception("Error getting team: %s", e)
            return jsonify({"success": False, "error": "Database error"}), 500

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        name = (data.get("team_name") or "").strip()
        if not name:
            return jsonify({"success": False, "error": "team_name required"}), 400
        try:
            db.execute_query(
                "UPDATE teams SET team_name=%s WHERE team_id=%s",
                (name, team_id),
                fetch_all=False
            )
            return jsonify({"success": True, "message": "Team updated"})
        except Exception as e:
            logger.exception("Error updating team: %s", e)
            return jsonify({"success": False, "error": "Database error"}), 500

    # DELETE
    try:
        db.execute_query("DELETE FROM teams WHERE team_id=%s", (team_id,), fetch_all=False)
        return jsonify({"success": True, "message": "Team deleted"})
    except Exception as e:
        logger.exception("Error deleting team: %s", e)
        return jsonify({"success": False, "error": "Cannot delete (FK in use?)"}), 400


# ==============================
# ADMIN SEASONS CRUD 
# ==============================

@app.route("/admin/seasons", methods=["GET"])
@login_required
def admin_seasons_page():
    # Shots gibi: sayfa render, veriyi JS çeker
    return render_template("admin_seasons.html", username=session.get("username"))

@app.route("/api/admin/seasons", methods=["GET", "POST"])
@login_required
def admin_seasons_list_or_add():
    if request.method == "GET":
        try:
            page = max(int(request.args.get("page", 1)), 1)
            limit = min(max(int(request.args.get("limit", 20)), 1), 200)
            offset = (page - 1) * limit

            team_id = (request.args.get("team_id") or "").strip()
            year = (request.args.get("year") or "").strip()
            title = (request.args.get("title") or "").strip()

            where = "WHERE 1=1"
            params = []

            if team_id:
                where += " AND s.team_id = %s"
                params.append(team_id)
            if year:
                where += " AND s.year = %s"
                params.append(year)
            if title:
                where += " AND s.title LIKE %s"
                params.append(f"%{title}%")

            total_row = db.execute_query(
                f"SELECT COUNT(*) AS total FROM season s {where}",
                tuple(params),
                fetch_all=True
            )
            total = total_row[0]["total"] if total_row else 0

            seasons = db.execute_query(
                f"""
                SELECT s.seasonentryid, s.team_id, t.team_name, s.title, s.year
                FROM season s
                LEFT JOIN teams t ON s.team_id = t.team_id
                {where}
                ORDER BY s.year DESC, t.team_name ASC
                LIMIT %s OFFSET %s
                """,
                tuple(params + [limit, offset]),
                fetch_all=True
            ) or []

            return jsonify({"success": True, "seasons": seasons, "total": total, "page": page, "limit": limit})
        except Exception as e:
            logger.exception("Error listing seasons: %s", e)
            return jsonify({"success": False, "error": "Database error"}), 500

    # POST: add season (MANUAL seasonentryid)
    data = request.get_json(silent=True) or {}

    seasonentryid = data.get("seasonentryid")
    team_id = data.get("team_id")
    title = (data.get("title") or "").strip()
    year = data.get("year")

    # ✅ seasonentryid/team_id/year zorunlu
    if seasonentryid is None or team_id is None or year is None:
        return jsonify({"success": False, "error": "seasonentryid, team_id and year required"}), 400

    # ✅ int cast + validasyon
    try:
        seasonentryid = int(seasonentryid)
        team_id = int(team_id)
        year = int(year)
    except Exception:
        return jsonify({"success": False, "error": "seasonentryid, team_id and year must be integers"}), 400

    try:
        db.execute_query(
            "INSERT INTO season (seasonentryid, team_id, title, year) VALUES (%s,%s,%s,%s)",
            (seasonentryid, team_id, title, year),
            fetch_all=False
        )
        return jsonify({"success": True, "message": "Season added successfully"})
    except Exception as e:
        logger.exception("Error adding season: %s", e)
        return jsonify({"success": False, "error": "Database error"}), 500


@app.route("/api/admin/seasons/<int:seasonentryid>", methods=["GET", "PUT", "DELETE"])
@login_required
def admin_season_get_update_delete(seasonentryid):
    if request.method == "GET":
        try:
            rows = db.execute_query(
                """
                SELECT s.seasonentryid, s.team_id, t.team_name, s.title, s.year
                FROM season s
                LEFT JOIN teams t ON s.team_id = t.team_id
                WHERE s.seasonentryid=%s
                LIMIT 1
                """,
                (seasonentryid,),
                fetch_all=True
            )
            if not rows:
                return jsonify({"success": False, "error": "Season not found"}), 404
            return jsonify({"success": True, "season": rows[0]})
        except Exception as e:
            logger.exception("Error getting season: %s", e)
            return jsonify({"success": False, "error": "Database error"}), 500

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        title = data.get("title")
        year = data.get("year")
        team_id = data.get("team_id")

        fields, params = [], []
        # burada bilinçli: title boş string gelirse update etme; istersen boş da set edebiliriz
        if title is not None and str(title).strip() != "":
            fields.append("title=%s")
            params.append(title)
        if year:
            fields.append("year=%s")
            params.append(year)
        if team_id:
            fields.append("team_id=%s")
            params.append(team_id)

        if not fields:
            return jsonify({"success": False, "error": "No fields to update"}), 400

        params.append(seasonentryid)

        try:
            db.execute_query(
                f"UPDATE season SET {', '.join(fields)} WHERE seasonentryid=%s",
                tuple(params),
                fetch_all=False
            )
            return jsonify({"success": True, "message": "Season updated"})
        except Exception as e:
            logger.exception("Error updating season: %s", e)
            return jsonify({"success": False, "error": "Database error"}), 500

    # DELETE
    try:
        db.execute_query("DELETE FROM season WHERE seasonentryid=%s", (seasonentryid,), fetch_all=False)
        return jsonify({"success": True, "message": "Season deleted"})
    except Exception as e:
        logger.exception("Error deleting season: %s", e)
        return jsonify({"success": False, "error": "Cannot delete"}), 400


# --- Authentication Routes --- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Validation
        if not all([username, email, password]):
            return render_template("register.html", error="All fields are required"), 400
        
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters"), 400
        
        password_hash = generate_password_hash(password)
        
        # Safe SQL with parameterized queries
        sql = """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """
        try:
            db.execute_query(sql, (username, email, password_hash), fetch_all=False)
            return redirect("/login?registered=true")
        except Exception as e:
            # Check for duplicate username/email
            if "duplicate" in str(e).lower():
                error = "Username or email already exists"
            else:
                error = "An error occurred during registration"
            return render_template("register.html", error=error), 400
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Validation
        if not username or not password:
            return render_template("login.html", error="Username and password are required"), 400
        
        # Safe SQL with parameterized queries
        sql = "SELECT * FROM users WHERE username = %s"
        users = db.execute_query(sql, (username,))
        
        if not users:
            return render_template("login.html", error="Invalid username or password"), 401
        
        user = users[0]
        
        if not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid username or password"), 401
        
        # Set session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        
        return redirect("/admin")
    
    error = request.args.get("error")
    registered = request.args.get("registered")
    return render_template("login.html", error=error, registered=registered)

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", username=session.get("username"))

"""
@app.route("/admin/shots")
@login_required
def admin_shots():
    # Fetch shots data
    sql = "SELECT * FROM shots ORDER BY date DESC LIMIT 100"
    shots = db.execute_query(sql)
    return render_template("admin_shots.html", shots=shots, username=session.get("username"))"""

@app.route("/admin/players")
@login_required
def admin_players():
    """Admin players management page"""
    return render_template("admin_players.html", username=session.get("username"))

@app.route("/api/admin/players", methods=['GET'])
@login_required
def api_admin_players_list():
    """List players with pagination and filtering for admin"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        name = request.args.get('name', '').strip()
        team = request.args.get('team', '').strip()
        year = request.args.get('year', '').strip()

        offset = (page - 1) * limit

        count_sql = "SELECT COUNT(*) as total FROM player WHERE 1=1"
        base_sql = """
            SELECT 
                season_player_id, player_id, player_name, team_title, position, year,
                goals, assists, games, time, xG, shots, key_passes,
                yellow_cards, red_cards, npg, npxG, xGChain, xGBuildup
            FROM player WHERE 1=1
        """
        params = []
        count_params = []

        if name:
            base_sql += " AND player_name LIKE %s"
            count_sql += " AND player_name LIKE %s"
            name_pattern = f"%{name}%"
            params.append(name_pattern)
            count_params.append(name_pattern)

        if team:
            base_sql += " AND team_title LIKE %s"
            count_sql += " AND team_title LIKE %s"
            team_pattern = f"%{team}%"
            params.append(team_pattern)
            count_params.append(team_pattern)

        if year:
            base_sql += " AND year = %s"
            count_sql += " AND year = %s"
            params.append(year)
            count_params.append(year)

        count_result = db.execute_query(count_sql, tuple(count_params), fetch_all=True)
        total = count_result[0]['total'] if count_result else 0

        base_sql += " ORDER BY year DESC, player_name ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        players = db.execute_query(base_sql, tuple(params), fetch_all=True)

        return jsonify({
            'success': True,
            'players': players,
            'total': total,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.exception(f"Error fetching admin players: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/admin/players/season/<int:season_player_id>", methods=['DELETE'])
@login_required
def api_admin_players_delete(season_player_id):
    """Delete a player row by season_player_id"""
    try:
        # Check if player exists
        check_sql = "SELECT season_player_id FROM player WHERE season_player_id = %s"
        result = db.execute_query(check_sql, (season_player_id,), fetch_all=True)
        
        if not result:
            return jsonify({'success': False, 'error': 'Player not found'}), 404
        
        # Delete the player
        delete_sql = "DELETE FROM player WHERE season_player_id = %s"
        db.execute_query(delete_sql, (season_player_id,), fetch_all=False)
        
        return jsonify({
            'success': True,
            'message': 'Player deleted successfully'
        })
    except Exception as e:
        logger.exception(f"Error deleting player {season_player_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/admin/settings")
@login_required
def admin_settings():
    return render_template("admin_settings.html", username=session.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login?logged_out=true")




@app.route("/admin/shots")
@login_required
def admin_shots():
    """Display shots management page"""
    try:
        sql = "SELECT * FROM shot_data ORDER BY date DESC LIMIT 100"
        shots = db.execute_query(sql, fetch_all=True)
        return render_template("admin_shots.html", 
                             shots=shots, 
                             username=session.get("username"))
    except Exception as e:
        logger.exception(f"Error fetching shots: {e}")
        return render_template("admin_shots.html", 
                             shots=[], 
                             error="Failed to load shots",
                             username=session.get("username"))

@app.route("/api/admin/shots", methods=['GET'])
@login_required
def api_get_shots():
    """API endpoint to fetch shots with pagination and filtering"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        player = request.args.get('player', '').strip()
        result = request.args.get('result', '').strip()
        
        offset = (page - 1) * limit
        
        # Count total records
        count_sql = "SELECT COUNT(*) as total FROM shot_data WHERE 1=1"
        count_params = []
        
        base_sql = "SELECT * FROM shot_data WHERE 1=1"
        params = []
        
        if player:
            base_sql += " AND player LIKE %s"
            count_sql += " AND player LIKE %s"
            params.append(f"%{player}%")
            count_params.append(f"%{player}%")
        
        if result:
            base_sql += " AND result = %s"
            count_sql += " AND result = %s"
            params.append(result)
            count_params.append(result)
        
        count_result = db.execute_query(count_sql, tuple(count_params), fetch_all=True)
        total = count_result[0]['total'] if count_result else 0
        
        base_sql += " ORDER BY date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        shots = db.execute_query(base_sql, tuple(params), fetch_all=True)
        
        return jsonify({
            'success': True,
            'shots': shots,
            'total': total,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.exception(f"Error fetching shots API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/admin/shots", methods=['POST'])
@login_required
def api_create_shot():
    """API endpoint to create a new shot"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['player', 'player_id', 'match_id', 'minute', 'result', 'xG', 'h_team', 'a_team', 'season']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        sql = """
            INSERT INTO shot_data 
            (player, player_id, match_id, minute, result, xG, X, Y, 
             shotType, situation, h_a, h_team, a_team, season, date, 
             h_goals, a_goals, player_assisted, lastAction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            data.get('player'),
            data.get('player_id'),
            data.get('match_id'),
            data.get('minute'),
            data.get('result'),
            data.get('xG'),
            data.get('X'),
            data.get('Y'),
            data.get('shotType', 'Open Play'),
            data.get('situation', 'Regular'),
            data.get('h_a', 'h'),
            data.get('h_team'),
            data.get('a_team'),
            data.get('season'),
            data.get('date'),
            data.get('h_goals', 0),
            data.get('a_goals', 0),
            data.get('player_assisted'),
            data.get('lastAction')
        )
        
        db.execute_query(sql, params, fetch_all=False)
        
        return jsonify({
            'success': True,
            'message': 'Shot created successfully'
        }), 201
        
    except Exception as e:
        logger.exception(f"Error creating shot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/admin/shots/<int:shot_id>", methods=['GET'])
@login_required
def api_get_shot(shot_id):
    """API endpoint to fetch a specific shot"""
    try:
        sql = "SELECT * FROM shot_data WHERE shot_id = %s"
        result = db.execute_query(sql, (shot_id,), fetch_all=True)
        
        if not result:
            return jsonify({'success': False, 'error': 'Shot not found'}), 404
        
        return jsonify({
            'success': True,
            'shot': result[0]
        })
        
    except Exception as e:
        logger.exception(f"Error fetching shot {shot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/admin/shots/<int:shot_id>", methods=['PUT'])
@login_required
def api_update_shot(shot_id):
    """API endpoint to update a shot"""
    try:
        data = request.get_json()
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        updatable_fields = [
            'player', 'minute', 'result', 'X', 'Y', 'xG', 
            'shotType', 'situation', 'h_a', 'h_goals', 'a_goals',
            'player_assisted', 'lastAction'
        ]
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        params.append(shot_id)
        
        sql = f"UPDATE shot_data SET {', '.join(update_fields)} WHERE shot_id = %s"
        db.execute_query(sql, tuple(params), fetch_all=False)
        
        return jsonify({
            'success': True,
            'message': 'Shot updated successfully'
        })
        
    except Exception as e:
        logger.exception(f"Error updating shot {shot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/admin/shots/<int:shot_id>", methods=['DELETE'])
@login_required
def api_delete_shot(shot_id):
    """API endpoint to delete a shot"""
    try:
        # Check if shot exists
        check_sql = "SELECT shot_id FROM shot_data WHERE shot_id = %s"
        result = db.execute_query(check_sql, (shot_id,), fetch_all=True)
        
        if not result:
            return jsonify({'success': False, 'error': 'Shot not found'}), 404
        
        sql = "DELETE FROM shot_data WHERE shot_id = %s"
        db.execute_query(sql, (shot_id,), fetch_all=False)
        
        return jsonify({
            'success': True,
            'message': 'Shot deleted successfully'
        })
        
    except Exception as e:
        logger.exception(f"Error deleting shot {shot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#3srg below is for add shot:
# Add these routes in the OSMAN section of app.py
# Add this route in the OSMAN section of app.py

@app.route('/api/match/<int:match_id>')
@login_required
def api_get_match_info(match_id):
    """API endpoint to fetch match details by match_id"""
    try:
        # Query match_info table for match details
        query = """
            SELECT 
                match_id,
                date,
                season,
                team_h,
                team_a,
                h_goals,
                a_goals,
                league
            FROM match_info
            WHERE match_id = %s
            LIMIT 1
        """
        
        results = db.execute_query(query, (match_id,), fetch_all=True)
        
        if not results or len(results) == 0:
            return jsonify({
                'success': False,
                'error': 'Match not found'
            }), 404
        
        match = results[0]
        
        return jsonify({
            'success': True,
            'match': match
        })
        
    except Exception as e:
        logger.exception(f"Error fetching match {match_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    
@app.route("/admin/shots/add")
@login_required
def admin_add_shot():
    """Display add shot form"""
    return render_template("admin_add_shot.html", username=session.get("username"))

@app.route('/api/autocomplete/players')
def autocomplete_players():
    """API endpoint for player name autocomplete"""
    try:
        query_str = request.args.get('q', '').strip()
        
        if len(query_str) < 2:
            return jsonify([])
        
        # Search in both player and shot_data tables for MySQL
        query = """
            SELECT player_id, player_name FROM (
                SELECT DISTINCT player_id, player_name 
                FROM player 
                WHERE player_name LIKE %s
                UNION
                SELECT DISTINCT player_id, player 
                FROM shot_data 
                WHERE player LIKE %s
            ) AS combined
            ORDER BY player_name
            LIMIT 20
        """
        
        results = db.execute_query(query, (f"%{query_str}%", f"%{query_str}%"), fetch_all=True)
        
        return jsonify(results)
        
    except Exception as e:
        logger.exception(f"Error in player autocomplete: {e}")
        return jsonify([]), 500

@app.route('/api/autocomplete/teams')
def autocomplete_teams():
    """API endpoint for team name autocomplete"""
    try:
        query_str = request.args.get('q', '').strip()
        
        if len(query_str) < 1:
            return jsonify([])
        
        # Search in teams table
        query = """
            SELECT DISTINCT team_name
            FROM teams
            WHERE team_name LIKE %s
            ORDER BY team_name
            LIMIT 20
        """
        
        results = db.execute_query(query, (f"%{query_str}%",), fetch_all=True)
        
        return jsonify(results)
        
    except Exception as e:
        logger.exception(f"Error in team autocomplete: {e}")
        return jsonify([]), 500

#2sr -------------------------------------------------------------------------------------------------------------------------------
#--------------OSMAN-END-------------------------------

@app.route("/matches")
def matches():
    """Matches sayfası"""
    return render_template("matches.html", title="matches")
#--------------ABDULLAH-START-----------------------------




#--------------ABDULLAH-END-------------------------------

@app.route("/api")
def api_data():
    """API verileri sayfası"""
    return jsonify({"message": "API endpoint", "status": "ok"})


@app.route('/match/<int:match_id>')
def match_page(match_id):
    """Detailed match page with matches between two teams and their recent matches"""
    try:
        query = """
            SELECT mi.*, md.isResult, md.xG_h, md.xG_a, md.forecast_w, md.forecast_d, md.forecast_l
            FROM match_info mi
            LEFT JOIN match_data md ON mi.match_id = md.match_id
            WHERE mi.match_id = %s
            LIMIT 1
        """
        results = db.execute_query(query, params=[match_id])
        if not results:
            return render_template('error.html', error='Match not found', message=f'No match with id {match_id}'), 404

        match = results[0]

        home_name = match.get('team_h')
        away_name = match.get('team_a')

        recent_q = """
            SELECT match_id, date, team_h, team_a, h_goals, a_goals, season
            FROM match_info
            WHERE team_h = %s OR team_a = %s
            ORDER BY date DESC
            LIMIT 5
        """
        home_recent = db.execute_query(recent_q, params=[home_name, home_name]) if home_name else []
        away_recent = db.execute_query(recent_q, params=[away_name, away_name]) if away_name else []

        h2h_recent = []
        h2h_stats = {'home_wins': 0, 'draws': 0, 'away_wins': 0, 'total': 0}
        if home_name and away_name:
            h2h_q = """
                SELECT match_id, date, team_h, team_a, h_goals, a_goals, season
                FROM match_info
                WHERE (team_h = %s AND team_a = %s) OR (team_h = %s AND team_a = %s)
                ORDER BY date DESC
                LIMIT 10
            """
            h2h_recent = db.execute_query(h2h_q, params=[home_name, away_name, away_name, home_name]) or []

            for m in h2h_recent:
                try:
                    hg = m.get('h_goals')
                    ag = m.get('a_goals')
                    if hg is None or ag is None:
                        continue
                    h2h_stats['total'] += 1
                    if hg == ag:
                        h2h_stats['draws'] += 1
                    elif (hg > ag and m.get('team_h') == home_name) or (ag > hg and m.get('team_a') == home_name):
                        h2h_stats['home_wins'] += 1
                    else:
                        h2h_stats['away_wins'] += 1
                except Exception:
                    continue

        # compute percentages
        if h2h_stats['total'] > 0:
            total = h2h_stats['total']
            h2h_stats['home_pct'] = round(h2h_stats['home_wins'] / total * 100, 1)
            h2h_stats['draw_pct'] = round(h2h_stats['draws'] / total * 100, 1)
            h2h_stats['away_pct'] = round(h2h_stats['away_wins'] / total * 100, 1)
        else:
            h2h_stats['home_pct'] = h2h_stats['draw_pct'] = h2h_stats['away_pct'] = 0

        h2h_stats['home_width'] = f"{h2h_stats['home_pct']}%"
        h2h_stats['draw_width'] = f"{h2h_stats['draw_pct']}%"
        h2h_stats['away_width'] = f"{h2h_stats['away_pct']}%"

        h_xg = match.get('h_xg') if match.get('h_xg') is not None else match.get('xG_h', 0)
        a_xg = match.get('a_xg') if match.get('a_xg') is not None else match.get('xG_a', 0)
        total_xg = (h_xg + a_xg) if (h_xg + a_xg) > 0 else 1
        h_xg_pct = round((h_xg / total_xg) * 100, 1)
        a_xg_pct = round((a_xg / total_xg) * 100, 1)

        match['h_xg_computed'] = round(h_xg, 2)
        match['a_xg_computed'] = round(a_xg, 2)
        match['h_xg_width'] = f"{h_xg_pct}%"
        match['a_xg_width'] = f"{a_xg_pct}%"

        # shots in this match
        shots_q = """
            SELECT s.shot_id, s.minute, s.result, s.xG, s.player, s.player_id,
                   COALESCE(p.player_name, s.player) AS player_name,
                   s.h_team, s.a_team
            FROM shot_data s
            LEFT JOIN player p ON s.player_id = p.player_id
            WHERE s.match_id = %s
            ORDER BY s.minute ASC
        """
        shots = db.execute_query(shots_q, (match_id,), fetch_all=True) or []

        # Top performers in this match
        # 4 table join: match_info, shot_data, player, teams
        top_performers_q = """
            SELECT 
                p.player_id,
                p.player_name,
                p.position,
                CASE 
                    WHEN s.h_a = 'h' THEN th.team_name
                    WHEN s.h_a = 'a' THEN ta.team_name
                END AS team,
                COUNT(s.shot_id) AS shots_taken,
                SUM(s.xG) AS total_xg,
                SUM(CASE WHEN s.result = 'Goal' THEN 1 ELSE 0 END) AS goals_scored,
                AVG(s.xG) AS avg_xg_per_shot,
                p.goals AS season_goals,
                p.assists AS season_assists,
                p.year AS season_year,
                (SELECT ROUND(SUM(CASE WHEN sd2.result = 'Goal' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1)
                 FROM shot_data sd2 
                 WHERE sd2.player_id = p.player_id AND sd2.season = mi.season) AS season_conversion_rate
            FROM match_info mi
            INNER JOIN shot_data s ON mi.match_id = s.match_id -- inner join to filter only shots in this match
            LEFT JOIN player p ON s.player_id = p.player_id AND p.year = mi.season
            LEFT JOIN teams th ON mi.h = th.team_id
            LEFT JOIN teams ta ON mi.a = ta.team_id
            WHERE mi.match_id = %s
            GROUP BY p.player_id, p.player_name, p.position, s.h_a, p.goals, p.assists, p.year, th.team_name, ta.team_name
            HAVING shots_taken > 0
            ORDER BY total_xg DESC, shots_taken DESC
            LIMIT 10
        """
        top_performers = db.execute_query(top_performers_q, (match_id,), fetch_all=True) or []

        # season comparison for both teams
        # subqueries on FROM section for home and away teams
        ## ("goals conceded" o takimin kac gol yedigi oluyor daha once gormediniz muhtemelen)
        season_comparison_q = """
            SELECT 
                mi.team_h, mi.team_a, mi.season, mi.h as h_team_id, mi.a as a_team_id,

                -- home and away team season stats
                home.games_played AS h_games_played, home.goals_scored AS h_goals_scored,
                home.goals_conceded AS h_goals_conceded, home.total_xg AS h_total_xg,
                home.total_xga AS h_total_xga, home.points AS h_points,
                home.wins AS h_wins, home.draws AS h_draws, home.losses AS h_losses,

                away.games_played AS a_games_played, away.goals_scored AS a_goals_scored,
                away.goals_conceded AS a_goals_conceded, away.total_xg AS a_total_xg,
                away.total_xga AS a_total_xga, away.points AS a_points,
                away.wins AS a_wins, away.draws AS a_draws, away.losses AS a_losses,

                -- top scorers and assisters for both teams
                h_scorer.player_name AS h_top_scorer, h_scorer.player_id AS h_top_scorer_id,
                h_scorer.goals AS h_top_scorer_goals, a_scorer.player_name AS a_top_scorer,
                a_scorer.player_id AS a_top_scorer_id, a_scorer.goals AS a_top_scorer_goals,
                h_assist.player_name AS h_top_assister, h_assist.player_id AS h_top_assister_id,
                h_assist.assists AS h_top_assister_assists, a_assist.player_name AS a_top_assister,
                a_assist.player_id AS a_top_assister_id, a_assist.assists AS a_top_assister_assists,
                
                -- shot conversion rates for home and away teams -- this means goals/shots 
                h_shots.conversion AS h_shot_conversion, a_shots.conversion AS a_shot_conversion

            FROM match_info mi

            -- home team season stat subqueries
            LEFT JOIN (
                SELECT title, year, COUNT(*) AS games_played, SUM(scored) AS goals_scored,
                    SUM(missed) AS goals_conceded, SUM(xG) AS total_xg, SUM(xGA) AS total_xga,
                    MAX(pts) AS points, MAX(wins) AS wins, MAX(draws) AS draws, MAX(loses) AS losses
                FROM season GROUP BY title, year
            ) home ON home.title = mi.team_h AND home.year = mi.season
            LEFT JOIN (
                SELECT title, year, COUNT(*) AS games_played, SUM(scored) AS goals_scored,
                    SUM(missed) AS goals_conceded, SUM(xG) AS total_xg, SUM(xGA) AS total_xga,
                    MAX(pts) AS points, MAX(wins) AS wins, MAX(draws) AS draws, MAX(loses) AS losses
                FROM season GROUP BY title, year
            ) away ON away.title = mi.team_a AND away.year = mi.season
            
            LEFT JOIN player h_scorer ON h_scorer.player_id = (
                SELECT player_id FROM player WHERE team_title = mi.team_h AND year = mi.season ORDER BY goals DESC LIMIT 1
            )
            LEFT JOIN player a_scorer ON a_scorer.player_id = (
                SELECT player_id FROM player WHERE team_title = mi.team_a AND year = mi.season ORDER BY goals DESC LIMIT 1
            )
            LEFT JOIN player h_assist ON h_assist.player_id = (
                SELECT player_id FROM player WHERE team_title = mi.team_h AND year = mi.season ORDER BY assists DESC LIMIT 1
            )
            LEFT JOIN player a_assist ON a_assist.player_id = (
                SELECT player_id FROM player WHERE team_title = mi.team_a AND year = mi.season ORDER BY assists DESC LIMIT 1
            )
            
            -- shot conversion rates for home and away teams
            LEFT JOIN (
                SELECT m.team_h, m.team_a, m.season,
                    ROUND(SUM(CASE WHEN sd.result = 'Goal' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS conversion
                FROM shot_data sd JOIN match_info m ON sd.match_id = m.match_id
                WHERE sd.h_a = 'h' GROUP BY m.team_h, m.team_a, m.season
            ) h_shots ON (h_shots.team_h = mi.team_h OR h_shots.team_a = mi.team_h) AND h_shots.season = mi.season
            LEFT JOIN (
                SELECT m.team_h, m.team_a, m.season,
                    ROUND(SUM(CASE WHEN sd.result = 'Goal' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS conversion
                FROM shot_data sd JOIN match_info m ON sd.match_id = m.match_id
                WHERE sd.h_a = 'a' GROUP BY m.team_h, m.team_a, m.season
            ) a_shots ON (a_shots.team_h = mi.team_a OR a_shots.team_a = mi.team_a) AND a_shots.season = mi.season
            
            WHERE mi.match_id = %s
        """
        season_comparison_raw = db.execute_query(season_comparison_q, (match_id,), fetch_all=True)
        season_comparison = season_comparison_raw[0] if season_comparison_raw else {}
        
        # calculate derived metrics
        if season_comparison:
            # convert decimal types to float for calculations
            h_goals_scored = float(season_comparison.get('h_goals_scored') or 0)
            a_goals_scored = float(season_comparison.get('a_goals_scored') or 0)
            h_goals_conceded = float(season_comparison.get('h_goals_conceded') or 0)
            a_goals_conceded = float(season_comparison.get('a_goals_conceded') or 0)
            h_total_xg = float(season_comparison.get('h_total_xg') or 0)
            a_total_xg = float(season_comparison.get('a_total_xg') or 0)
            h_games_played = float(season_comparison.get('h_games_played') or 1) or 1
            a_games_played = float(season_comparison.get('a_games_played') or 1) or 1
            
            # goal difference (not between these two teams, but for each team in the season)
            season_comparison['h_goal_diff'] = int(h_goals_scored - h_goals_conceded)
            season_comparison['a_goal_diff'] = int(a_goals_scored - a_goals_conceded)
            
            # xG performance (actual goals - xG, positive = overperforming)
            # (takimlarin bitiriciligi gibi dusunebiliriz. bu deger negatifse guzel sut atıyolar ama gol olmuyor demek)
            h_xg_perf = h_goals_scored - h_total_xg
            a_xg_perf = a_goals_scored - a_total_xg
            season_comparison['h_xg_performance'] = round(h_xg_perf, 1)
            season_comparison['a_xg_performance'] = round(a_xg_perf, 1)
            
            # average goals per game
            season_comparison['h_goals_per_game'] = round(h_goals_scored / h_games_played, 2)
            season_comparison['a_goals_per_game'] = round(a_goals_scored / a_games_played, 2)
            
            # average xG per game
            season_comparison['h_xg_per_game'] = round(h_total_xg / h_games_played, 2)
            season_comparison['a_xg_per_game'] = round(a_total_xg / a_games_played, 2)

        return render_template('match_detail.html', match=match, home_recent=home_recent, away_recent=away_recent, h2h_recent=h2h_recent, h2h_stats=h2h_stats, shots=shots, top_performers=top_performers, season_comparison=season_comparison)
    except Exception as e:
        logger.exception(f"Error fetching match {match_id}: %s", e)
        return render_template('error.html', error='Database Error', message=str(e)), 500

@app.route('/admin/matches')
@login_required
def admin_matches():
    """Render admin page for matches"""
    try:
        sql = "SELECT mi.match_id, mi.date, mi.season, mi.league, mi.team_h, mi.team_a, mi.h_goals, mi.a_goals FROM match_info mi ORDER BY date DESC LIMIT 200"
        matches = db.execute_query(sql, fetch_all=True)
        return render_template('admin_matches.html', matches=matches, username=session.get('username'))
    except Exception as e:
        logger.exception(f"Error fetching matches: {e}")
        return render_template('admin_matches.html', matches=[], error='Failed to load matches', username=session.get('username'))


@app.route('/api/admin/matches', methods=['GET'])
@login_required
def api_get_matches():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        team = request.args.get('team', '').strip()
        season = request.args.get('season', '').strip()

        offset = (page - 1) * limit

        count_sql = "SELECT COUNT(*) as total FROM match_info WHERE 1=1"
        base_sql = "SELECT match_id, date, season, league, team_h, team_a, h_goals, a_goals, h_xg, a_xg FROM match_info WHERE 1=1"
        params = []
        count_params = []

        if team:
            base_sql += " AND (team_h LIKE %s OR team_a LIKE %s)"
            count_sql += " AND (team_h LIKE %s OR team_a LIKE %s)"
            params.extend([f"%{team}%", f"%{team}%"])
            count_params.extend([f"%{team}%", f"%{team}%"])

        if season:
            base_sql += " AND season = %s"
            count_sql += " AND season = %s"
            params.append(season)
            count_params.append(season)

        count_result = db.execute_query(count_sql, tuple(count_params), fetch_all=True)
        total = count_result[0]['total'] if count_result else 0

        base_sql += " ORDER BY date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        matches = db.execute_query(base_sql, tuple(params), fetch_all=True)

        return jsonify({'success': True, 'matches': matches, 'total': total, 'page': page, 'limit': limit})
    except Exception as e:
        logger.exception(f"Error fetching matches API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/matches', methods=['POST'])
@login_required
def api_create_match():
    try:
        data = request.get_json() or {}
        required = ['match_id', 'team_h', 'team_a']
        if not all(k in data and data[k] for k in required):
            return jsonify({'success': False, 'error': 'Missing required fields (match_id, team_h, team_a)'}), 400

        sql = """INSERT INTO match_info 
                 (match_id, date, season, league, league_id, team_h, team_a, h_goals, a_goals, h_xg, a_xg,
                  h_shot, a_shot, h_shotOnTarget, a_shotOnTarget, h_deep, a_deep, h_ppda, a_ppda, h_w, h_d, h_l) 
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        params = (
            data.get('match_id'), data.get('date'), data.get('season'), data.get('league'), data.get('league_id'),
            data.get('team_h'), data.get('team_a'), data.get('h_goals'), data.get('a_goals'),
            data.get('h_xg'), data.get('a_xg'), data.get('h_shot'), data.get('a_shot'),
            data.get('h_shotOnTarget'), data.get('a_shotOnTarget'), data.get('h_deep'), data.get('a_deep'),
            data.get('h_ppda'), data.get('a_ppda'), data.get('h_w'), data.get('h_d'), data.get('h_l')
        )

        db.execute_query(sql, params, fetch_all=False)
        return jsonify({'success': True, 'message': 'Match created successfully'}), 201
    except Exception as e:
        logger.exception(f"Error creating match: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/matches/<int:match_id>', methods=['GET'])
@login_required
def api_get_match(match_id):
    try:
        sql = "SELECT * FROM match_info WHERE match_id = %s"
        result = db.execute_query(sql, (match_id,), fetch_all=True)
        if not result:
            return jsonify({'success': False, 'error': 'Match not found'}), 404
        return jsonify({'success': True, 'match': result[0]})
    except Exception as e:
        logger.exception(f"Error fetching match {match_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/matches/<int:match_id>', methods=['PUT'])
@login_required
def api_update_match(match_id):
    try:
        data = request.get_json() or {}
        updatable = ['date','season','league','league_id','team_h','team_a','h_goals','a_goals','h_xg','a_xg',
                     'h_shot','a_shot','h_shotOnTarget','a_shotOnTarget','h_deep','a_deep','h_ppda','a_ppda',
                     'h_w','h_d','h_l']
        fields = []
        params = []
        for f in updatable:
            if f in data:
                fields.append(f + ' = %s')
                params.append(data[f])

        if not fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        params.append(match_id)
        sql = f"UPDATE match_info SET {', '.join(fields)} WHERE match_id = %s"
        db.execute_query(sql, tuple(params), fetch_all=False)
        return jsonify({'success': True, 'message': 'Match updated successfully'})
    except Exception as e:
        logger.exception(f"Error updating match {match_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/matches/<int:match_id>', methods=['DELETE'])
@login_required
def api_delete_match(match_id):
    try:
        check = db.execute_query('SELECT match_id FROM match_info WHERE match_id = %s', (match_id,), fetch_all=True)
        if not check:
            return jsonify({'success': False, 'error': 'Match not found'}), 404
        db.execute_query('DELETE FROM match_info WHERE match_id = %s', (match_id,), fetch_all=False)
        return jsonify({'success': True, 'message': 'Match deleted successfully'})
    except Exception as e:
        logger.exception(f"Error deleting match {match_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/match/seasons', methods=['GET'])
def api_match_seasons():
    """Return distinct seasons available in match_info"""
    try:
        rows = db.execute_query("SELECT DISTINCT season FROM match_info WHERE season IS NOT NULL ORDER BY season DESC", fetch_all=True)
        seasons = [r['season'] for r in rows if r.get('season') is not None]
        return jsonify({'seasons': seasons})
    except Exception as e:
        logger.exception(f"Error fetching match seasons: {e}")
        return jsonify({'seasons': []}), 500


@app.route("/api/matches", methods=['POST'])
def api_matches():
    """Return matches filtered by supplied JSON filters."""
    filters = request.get_json(silent=True) or {}
    limit = min(int(filters.get('limit', 50)), 5000)
    
    # Build parameterized query
    sql = [
        "SELECT mi.match_id, mi.date, mi.season, mi.league,",
        "       mi.team_h, mi.team_a, mi.h_goals, mi.a_goals,",
        "       mi.h_xg, mi.a_xg, mi.h_shot, mi.a_shot,",
        "       md.isResult, md.xG_h, md.xG_a, md.forecast_w, md.forecast_d, md.forecast_l",
        "FROM match_info mi",
        "LEFT JOIN match_data md ON mi.match_id = md.match_id",
        "WHERE 1=1"
    ]
    params = []

    if filters.get('q'):
        sql.append("AND (LOWER(mi.team_h) LIKE %s OR LOWER(mi.team_a) LIKE %s OR mi.match_id = %s)")
        q = f"%{filters['q'].lower()}%"
        params.extend([q, q, filters['q']])
    
    if filters.get('season'):
        sql.append("AND mi.season = %s")
        params.append(filters['season'])
    
    if filters.get('team_home'):
        sql.append("AND mi.team_h = %s")
        params.append(filters['team_home'])
    
    if filters.get('team_away'):
        sql.append("AND mi.team_a = %s")
        params.append(filters['team_away'])
    
    if filters.get('date_from'):
        sql.append("AND mi.date >= %s")
        params.append(filters['date_from'])
    
    if filters.get('date_to'):
        sql.append("AND mi.date <= %s")
        params.append(filters['date_to'])
    
    if filters.get('min_goals'):
        sql.append("AND (COALESCE(mi.h_goals,0) + COALESCE(mi.a_goals,0)) >= %s")
        params.append(int(filters['min_goals']))
    
    if filters.get('max_goals'):
        sql.append("AND (COALESCE(mi.h_goals,0) + COALESCE(mi.a_goals,0)) <= %s")
        params.append(int(filters['max_goals']))
    
    if filters.get('min_xg'):
        sql.append("AND (COALESCE(mi.h_xg,0) + COALESCE(mi.a_xg,0)) >= %s")
        params.append(float(filters['min_xg']))

    sql.append(f"ORDER BY mi.date DESC LIMIT {limit}")
    query = " ".join(sql)

    try:
        matches = db.execute_query(query, params=params)
        return jsonify({"matches": matches or [], "limit": limit})
    except Exception as e:
        logger.exception("Error fetching matches: %s", e)
        return jsonify({"error": "Database error", "matches": []}), 500




# -------------------------------------------------
#  Main Entry Point
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

