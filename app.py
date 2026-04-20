"""Flask app — mirrors server.js exactly"""
import os
from flask import Flask, send_from_directory, jsonify

def create_app():
    frontend = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    app = Flask(__name__, static_folder=frontend, static_url_path="")
    os.environ.setdefault("FLASK_SKIP_DOTENV", "1")

    app.config["SECRET_KEY"]                  = os.getenv("SECRET_KEY", "ecu-analytics-secret-2025")
    app.config["SESSION_COOKIE_HTTPONLY"]      = True
    app.config["SESSION_COOKIE_SAMESITE"]      = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"]   = 86400

    try:
        from flask_cors import CORS
        CORS(app, supports_credentials=True)
    except ImportError:
        pass

    from backend.routes.auth    import auth_bp
    from backend.routes.ecu     import ecu_bp
    from backend.routes.alerts  import alerts_bp
    from backend.routes.admin   import admin_bp
    from backend.routes.metrics import metrics_bp

    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(ecu_bp,     url_prefix="/api/ecu")
    app.register_blueprint(alerts_bp,  url_prefix="/api/alerts")
    app.register_blueprint(admin_bp,   url_prefix="/api/admin")
    app.register_blueprint(metrics_bp, url_prefix="/api/metrics")

    @app.get("/api/health")
    def health():
        from datetime import datetime
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

    # Serve frontend HTML files
    @app.get("/")
    def index():
        return send_from_directory(frontend, "login.html")

    @app.errorhandler(404)
    def not_found(e):
        from flask import request
        if request.path.startswith("/api/"):
            return jsonify({"error": "Endpoint not found"}), 404
        return send_from_directory(frontend, "login.html")

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Server error"}), 500

    return app
