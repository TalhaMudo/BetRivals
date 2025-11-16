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

@app.route("/talha")
def talha():
    """Talha sayfası"""
    return render_template("talha.html", title="Talha")

@app.route("/osman")
def osman():
    """Osman sayfası"""
    return render_template("osman.html", title="Osman")

@app.route("/matches")
def matches():
    """Matches sayfası"""
    return render_template("matches.html", title="matches")

@app.route("/api")
def api_data():
    """API verileri sayfası"""
    return jsonify({"message": "API endpoint", "status": "ok"})


@app.route("/api/matches", methods=['POST'])
def api_matches():
    """Return matches filtered by supplied JSON filters."""
    filters = request.get_json(silent=True) or {}
    
    # Build parameterized query
    sql = [
        "SELECT mi.match_id, mi.date, mi.season, mi.league,",
        "       mi.team_h, mi.team_a, mi.h_goals, mi.a_goals,",
        "       mi.h_xg, mi.a_xg, mi.h_shot, mi.a_shot,",
        "       md.isResult",
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
    
    if filters.get('league'):
        sql.append("AND LOWER(mi.league) = %s")
        params.append(str(filters['league']).lower())
    
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
    
    if filters.get('isResult') not in (None, '', False):
        sql.append("AND COALESCE(md.isResult,0) = %s")
        params.append(filters['isResult'])

    sql.append("ORDER BY mi.date DESC LIMIT 1000")
    query = " ".join(sql)

    try:
        matches = db.execute_query(query, params=params)
        return jsonify({"matches": matches or []})
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