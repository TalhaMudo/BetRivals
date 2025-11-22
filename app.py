from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import logging
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
    return render_template("index.html", title="Home Page")


@app.route("/about")
def about():
    """Hakkında sayfası"""
    return render_template("about.html", title="About Us")

#--------------BILGE-START------------------------------

# ========= BILGE: Teams & Seasons pages =========

@app.route("/teams")
def teams_page():
    return render_template("teams.html", title="Teams")

@app.route("/seasons")
def seasons_page():
    return render_template("seasons.html", title="Seasons")

# ========= BILGE: Teams API =========

@app.route("/api/teams", methods=["GET"])
def api_teams_list():
    """
    Filters:
      - q: name search
      - page, per_page
    """
    q = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 20)), 1), 200)
    offset = (page - 1) * per_page

    base = ["FROM teams WHERE 1=1"]
    params = []
    if q:
        base.append("AND team_name LIKE %s")
        params.append(f"%{q}%")

    try:
        total = db.execute_query(f"SELECT COUNT(*) { ' '.join(base) }", params)[0][0]
        rows = db.execute_query(
            f"""
            SELECT team_id, team_name
            { ' '.join(base) }
            ORDER BY team_name ASC
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset]
        )
        items = [
            {"team_id": r[0], "team_name": r[1]}
            for r in rows
        ]
        return jsonify({"total": total, "page": page, "per_page": per_page, "items": items})
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
        db.execute_query("INSERT INTO teams (team_name) VALUES (%s)", [name])
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
        db.execute_query("UPDATE teams SET team_name=%s WHERE team_id=%s", [name, team_id])
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error updating team: %s", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/api/teams/<int:team_id>/delete", methods=["POST"])
def api_team_delete(team_id):
    try:
        db.execute_query("DELETE FROM teams WHERE team_id=%s", [team_id])
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error deleting team: %s", e)
        # FK varsa silinemez
        return jsonify({"error": "Cannot delete team (FK in use?)"}), 400


# ========= BILGE: Seasons API =========

@app.route("/api/seasons", methods=["GET"])
def api_seasons_list():
    """
    Filters:
      - team_id, year, h_a, result
      - title (substring)
      - date_from, date_to  (YYYY-MM-DD)
      - order_by in {year_desc, year_asc, pts_desc, pts_asc, date_desc, date_asc}
      - page, per_page
    """
    team_id = request.args.get("team_id")
    year = request.args.get("year")
    title = request.args.get("title", "").strip()
    h_a = request.args.get("h_a")
    result = request.args.get("result")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    order_by = request.args.get("order_by", "year_desc")

    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 20)), 1), 200)
    offset = (page - 1) * per_page

    order_map = {
        "year_desc": "s.year DESC, t.team_name ASC",
        "year_asc":  "s.year ASC, t.team_name ASC",
        "pts_desc":  "s.pts DESC, t.team_name ASC",
        "pts_asc":   "s.pts ASC, t.team_name ASC",
        "date_desc": "s.date DESC",
        "date_asc":  "s.date ASC",
    }
    order_sql = order_map.get(order_by, "s.year DESC, t.team_name ASC")

    base = ["""
        FROM season s
        LEFT JOIN teams t ON t.team_id = s.team_id
        WHERE 1=1
    """]
    params = []

    if team_id:
        base.append("AND s.team_id = %s")
        params.append(team_id)
    if year:
        base.append("AND s.year = %s")
        params.append(year)
    if title:
        base.append("AND s.title LIKE %s")
        params.append(f"%{title}%")
    if h_a in ("H", "A"):
        base.append("AND s.h_a = %s")
        params.append(h_a)
    if result in ("W", "D", "L"):
        base.append("AND s.result = %s")
        params.append(result)
    if date_from:
        base.append("AND s.date >= %s")
        params.append(f"{date_from} 00:00:00")
    if date_to:
        base.append("AND s.date <= %s")
        params.append(f"{date_to} 23:59:59")

    try:
        total = db.execute_query(f"SELECT COUNT(*) { ' '.join(base) }", params)[0][0]
        rows = db.execute_query(
            f"""
            SELECT
              s.seasonentryid, s.team_id, IFNULL(t.team_name,''), s.title, s.year, s.h_a,
              s.xG, s.xGA, s.npxG, s.npxGA, s.deep, s.deep_allowed, s.scored, s.missed,
              s.xpts, s.result, s.date, s.wins, s.draws, s.loses, s.pts, s.npxGD,
              s.ppda_att, s.ppda_def, s.ppda_allowed_att, s.ppda_allowed_def
            { ' '.join(base) }
            ORDER BY {order_sql}
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset]
        )
        items = []
        for r in rows:
            items.append({
                "seasonentryid": r[0], "team_id": r[1], "team_name": r[2], "title": r[3],
                "year": r[4], "h_a": r[5], "xG": r[6], "xGA": r[7], "npxG": r[8], "npxGA": r[9],
                "deep": r[10], "deep_allowed": r[11], "scored": r[12], "missed": r[13],
                "xpts": r[14], "result": r[15], "date": r[16],
                "wins": r[17], "draws": r[18], "loses": r[19], "pts": r[20], "npxGD": r[21],
                "ppda_att": r[22], "ppda_def": r[23], "ppda_allowed_att": r[24], "ppda_allowed_def": r[25],
            })
        return jsonify({"total": total, "page": page, "per_page": per_page, "items": items})
    except Exception as e:
        logger.exception("Error listing seasons: %s", e)
        return jsonify({"error": "Database error", "items": []}), 500


@app.route("/api/seasons", methods=["POST"])
def api_season_create():
    """
    Body (JSON): season alanlarının tamamı opsiyonel; gerekli olanlar:
      - team_id, year  (FK ve mantıksal)
    """
    data = request.get_json(silent=True) or {}
    if not data.get("team_id") or not data.get("year"):
        return jsonify({"error": "team_id and year are required"}), 400

    fields = [
        "seasonentryid","team_id","title","year","h_a","xG","xGA","npxG","npxGA",
        "deep","deep_allowed","scored","missed","xpts","result","date",
        "wins","draws","loses","pts","npxGD","ppda_att","ppda_def","ppda_allowed_att","ppda_allowed_def"
    ]
    cols = []
    vals = []
    params = []
    for f in fields:
        if f in data and data[f] not in (None, ""):
            cols.append(f)
            vals.append("%s")
            params.append(data[f])

    if not cols:
        return jsonify({"error": "no fields to insert"}), 400

    sql = f"INSERT INTO season ({', '.join(cols)}) VALUES ({', '.join(vals)})"
    try:
        db.execute_query(sql, params)
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error creating season: %s", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/api/seasons/<int:seasonentryid>/update", methods=["POST"])
def api_season_update(seasonentryid):
    data = request.get_json(silent=True) or {}
    # boş body gelirse engelle
    updatable = [
        "team_id","title","year","h_a","xG","xGA","npxG","npxGA",
        "deep","deep_allowed","scored","missed","xpts","result","date",
        "wins","draws","loses","pts","npxGD","ppda_att","ppda_def","ppda_allowed_att","ppda_allowed_def"
    ]
    sets = []
    params = []
    for f in updatable:
        if f in data:
            sets.append(f"{f}=%s")
            params.append(data[f])

    if not sets:
        return jsonify({"error": "no fields to update"}), 400

    params.append(seasonentryid)
    sql = f"UPDATE season SET {', '.join(sets)} WHERE seasonentryid=%s"
    try:
        db.execute_query(sql, params)
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error updating season: %s", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/api/seasons/<int:seasonentryid>/delete", methods=["POST"])
def api_season_delete(seasonentryid):
    try:
        db.execute_query("DELETE FROM season WHERE seasonentryid=%s", [seasonentryid])
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Error deleting season: %s", e)
        return jsonify({"error": "Cannot delete season"}), 400



#--------------BILGE-END-------------------------------


@app.route("/talha")
def talha():
    """Talha sayfası"""
    return render_template("talha.html", title="Talha")
#--------------TALHA-START-----------------------------

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
        
        # Use LIKE for partial matching
        search_pattern = f"%{search_query}%"
        query = """
        SELECT DISTINCT
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
        WHERE p.player_name LIKE %s 
           OR p.team_title LIKE %s 
           OR p.position LIKE %s
        ORDER BY p.player_name
        LIMIT 50
        """
        results = db.execute_query(query, params=[search_pattern, search_pattern, search_pattern])
        return jsonify({
            "players": results or [], 
            "count": len(results) if results else 0
        })
    except Exception as e:
        logger.exception("Error searching players: %s", e)
        return jsonify({"error": "Database error", "players": []}), 500

@app.route("/api/players/<int:player_id>", methods=['GET'])
def api_player_detail(player_id):
    """Get full player details by player_id"""
    try:
        query = """
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
        return jsonify({"player": results[0]})
    except Exception as e:
        logger.exception("Error fetching player detail: %s", e)
        return jsonify({"error": "Database error"}), 500

@app.route("/talha/<int:player_id>")
def player_detail(player_id):
    """Individual player detail page"""
    return render_template("player_detail.html", title="Player Details", player_id=player_id)

#--------------TALHA-END-------------------------------



@app.route("/osman")
def osman():
    """Osman sayfası"""
    return render_template("osman.html", title="Osman")
#--------------OSMAN-START-----------------------------

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
        
        return render_template('shot_detail.html',
                             shot=shot,
                             player=player,
                             other_shots=other_shots,
                             season_stats=season_stats)
        
    except Exception as e:
        logger.exception(f"Error fetching shot {shot_id}: {e}")
        return render_template('error.html',
                             error="Database Error",
                             message=str(e)), 500


    
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

@app.route("/admin/shots")
@login_required
def admin_shots():
    # Fetch shots data
    sql = "SELECT * FROM shots ORDER BY date DESC LIMIT 100"
    shots = db.execute_query(sql)
    return render_template("admin_shots.html", shots=shots, username=session.get("username"))

@app.route("/admin/players")
@login_required
def admin_players():
    # Fetch players data
    sql = "SELECT * FROM players ORDER BY name ASC"
    players = db.execute_query(sql)
    return render_template("admin_players.html", players=players, username=session.get("username"))

@app.route("/admin/teams")
@login_required
def admin_teams():
    # Fetch teams data
    sql = "SELECT * FROM teams ORDER BY name ASC"
    teams = db.execute_query(sql)
    return render_template("admin_teams.html", teams=teams, username=session.get("username"))

@app.route("/admin/settings")
@login_required
def admin_settings():
    return render_template("admin_settings.html", username=session.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login?logged_out=true")
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

@app.route("/api/add_match", methods=['POST'])
def api_add_match():
    """Create a new match entry in the database.""" # admin user only
    pass

@app.route("/api/modify_match", methods=['POST'])
def api_delete_match():
    """Modify a match entry from the database. It can be used to delete a match as well.""" # admin user only
    pass


# -------------------------------------------------
#  Main Entry Point
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
