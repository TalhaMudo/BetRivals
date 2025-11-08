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

#--------------BILGE-START------------------------------

@app.route("/teams")
def teams_page():
    return render_template("teams.html", title="Teams")

@app.route("/seasons")
def seasons_page():
    return render_template("seasons.html", title="Seasons")


# BILGE: Teams API 
@app.route("/api/teams", methods=["GET"])
def api_teams_list():
    """En fazla 100 takımı döndürür (id, ad)."""
    try:
        rows = db.execute_query(
            "SELECT team_id, team_name FROM teams ORDER BY team_id DESC LIMIT 100"
        )
        items = [{"team_id": r[0], "team_name": r[1]} for r in rows]
        return jsonify({"items": items})
    except Exception as e:
        logger.exception("teams list error: %s", e)
        return jsonify({"error": "db error", "items": []}), 500

@app.route("/api/teams", methods=["POST"])
def api_team_create():
    """Body: {team_name}"""
    data = request.get_json(silent=True) or {}
    name = (data.get("team_name") or "").strip()
    if not name:
        return jsonify({"error": "team_name required"}), 400
    try:
        db.execute_query("INSERT INTO teams (team_name) VALUES (%s)", [name])
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("team create error: %s", e)
        return jsonify({"error": "db error"}), 500

@app.route("/api/teams/<int:team_id>/delete", methods=["POST"])
def api_team_delete(team_id):
    """Takımı siler (FK varsa hata)."""
    try:
        db.execute_query("DELETE FROM teams WHERE team_id=%s", [team_id])
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("team delete error: %s", e)
        return jsonify({"error": "cannot delete team (FK?)"}), 400


# BILGE: Seasons API
@app.route("/api/seasons", methods=["GET"])
def api_seasons_list():
    """En fazla 100 sezonu döndürür (temel alanlar)."""
    try:
        rows = db.execute_query(
            """
            SELECT seasonentryid, team_id, title, year, h_a, result, pts
            FROM season
            ORDER BY seasonentryid DESC
            LIMIT 100
            """
        )
        items = [
            {
                "seasonentryid": r[0],
                "team_id": r[1],
                "title": r[2],
                "year": r[3],
                "h_a": r[4],
                "result": r[5],
                "pts": r[6],
            }
            for r in rows
        ]
        return jsonify({"items": items})
    except Exception as e:
        logger.exception("seasons list error: %s", e)
        return jsonify({"error": "db error", "items": []}), 500

@app.route("/api/seasons", methods=["POST"])
def api_season_create():
    """
    Body (JSON) minimal:
      - team_id (zorunlu)
      - year    (zorunlu)
      - title, h_a, result, pts (opsiyonel)
    """
    d = request.get_json(silent=True) or {}
    if not d.get("team_id") or not d.get("year"):
        return jsonify({"error": "team_id and year required"}), 400

    # kolonları minimal tuttuk; istersen genişletirsin
    cols, vals, params = ["team_id","year"], ["%s","%s"], [d["team_id"], d["year"]]
    for k in ("title","h_a","result","pts"):
        if k in d and d[k] not in (None, ""):
            cols.append(k); vals.append("%s"); params.append(d[k])

    try:
        db.execute_query(
            f"INSERT INTO season ({', '.join(cols)}) VALUES ({', '.join(vals)})",
            params
        )
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("season create error: %s", e)
        return jsonify({"error": "db error"}), 500

@app.route("/api/seasons/<int:seasonentryid>/delete", methods=["POST"])
def api_season_delete(seasonentryid):
    """Sezon kaydını siler."""
    try:
        db.execute_query("DELETE FROM season WHERE seasonentryid=%s", [seasonentryid])
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("season delete error: %s", e)
        return jsonify({"error": "cannot delete season"}), 400



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
