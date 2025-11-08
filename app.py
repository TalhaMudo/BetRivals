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




#--------------TALHA-END-------------------------------

@app.route("/osman")
def osman():
    """Osman sayfası"""
    return render_template("osman.html", title="Osman")
#--------------OSMAN-START-----------------------------


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
