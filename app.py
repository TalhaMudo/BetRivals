from flask import Flask, render_template, jsonify, request, redirect, url_for

# -------------------------------------------------
#  Flask Uygulaması Oluşturma
# -------------------------------------------------
app = Flask(__name__)

# Gizli anahtar (örnek)
app.config["SECRET_KEY"] = "dev-secret-key"

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


@app.route("/api/data", methods=["GET"])
def api_data():
    """Basit bir API endpoint"""
    sample_data = {
        "status": "success",
        "message": "Hello from Flask API!",
        "data": [1, 2, 3, 4]
    }
    return jsonify(sample_data)


@app.route("/form", methods=["GET", "POST"])
def form_example():
    """Form örneği"""
    if request.method == "POST":
        name = request.form.get("name")
        return render_template("form.html", submitted=True, name=name)
    return render_template("form.html", submitted=False)


# -------------------------------------------------
#  Error Handling
# -------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    """404 - Sayfa bulunamadı hatası"""
    return render_template("404.html", title="Page Not Found"), 404


@app.errorhandler(500)
def internal_error(error):
    """500 - Sunucu hatası"""
    return render_template("500.html", title="Internal Server Error"), 500


# -------------------------------------------------
#  Main Entry Point
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)