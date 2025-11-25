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


@app.route("/bilge")
def bilge():
    """Bilge sayfası"""
    return render_template("bilge.html", title="Bilge")
#--------------BILGE-START-----------------------------




#--------------BILGE-END-------------------------------
@app.route("/talha")
def talha():
    """Talha sayfası"""
    return render_template("talha.html", title="Talha")
#--------------TALHA-START-----------------------------




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

#2sg - - - - - - - - - - - - - - - - - - below is for admin page : 

# Add these routes to your app.py (in OSMAN section or appropriate place)

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


@app.route("/api/matches", methods=['POST'])
def api_matches():
    """execute query and return matches filtered by supplied JSON filters."""
    filters = request.get_json(silent=True) or {}
    
    sql = [
        # query here
    ]
    params = []

    if filters.get('team_home'):
        sql.append("AND mi.team_h = %s")
        params.append(filters['team_home'])
    
    if filters.get('team_away'):
        sql.append("AND mi.team_a = %s")
        params.append(filters['team_away'])
    
    # others filters

    query = " ".join(sql)

    try:
        matches = db.execute_query(query, params=params)
        return jsonify({"matches": matches or []})
    except Exception as e:
        logger.exception("Error fetching matches: %s", e)
        return jsonify({"error": "Database error", "matches": []}), 500


# -------------------------------------------------
#  Main Entry Point
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
