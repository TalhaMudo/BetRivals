from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import logging
from dotenv import load_dotenv
from utils import DatabaseConnector

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
