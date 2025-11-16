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
