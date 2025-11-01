from flask import Flask, render_template, jsonify, request, redirect, url_for

# -------------------------------------------------
#  Flask Uygulaması Oluşturma
# -------------------------------------------------
app = Flask(__name__, template_folder='main/templates', static_folder='main/static')

# Gizli anahtar (örnek)
app.config["SECRET_KEY"] = "bet-rivals-bostanXXX"

# -------------------------------------------------
#  Örnek Rotalar
# -------------------------------------------------

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

@app.route("/abdullah")
def abdullah():
    """Abdullah sayfası"""
    return render_template("abdullah.html", title="Abdullah")

@app.route("/api")
def api_data():
    """API verileri sayfası"""
    return jsonify({"message": "API endpoint", "status": "ok"})




# -------------------------------------------------
#  Main Entry Point
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)