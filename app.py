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

#2sg - - - - - - - - - - - - - - - - - - below is for admin page : 

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
def api_get_match(match_id):
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

        return render_template('match_detail.html', match=match, home_recent=home_recent, away_recent=away_recent, h2h_recent=h2h_recent, h2h_stats=h2h_stats)
    except Exception as e:
        logger.exception(f"Error fetching match {match_id}: %s", e)
        return render_template('error.html', error='Database Error', message=str(e)), 500


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
    app.run(debug=True, host="0.0.0.0")
