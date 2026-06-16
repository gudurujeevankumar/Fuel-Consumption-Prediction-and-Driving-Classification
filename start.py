#!/usr/bin/env python3
"""
ECU Analytics — One-Click Launcher
Run: python3 start.py
      python3 start.py --port 8080
"""
import os, sys, logging, argparse
from pathlib import Path

HERE = Path(__file__).parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

# Load .env
env_file = HERE / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# Port from --port flag or .env
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--port", type=int, default=None)
args, _ = parser.parse_known_args()
PORT = args.port or int(os.getenv("PORT", 8080))

# Logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler("logs/server.log", encoding="utf-8")]
)
for lib in ("urllib3","werkzeug","charset_normalizer"):
    logging.getLogger(lib).setLevel(logging.WARNING)

print("""
╔══════════════════════════════════════════════════════╗
║          ECU Analytics — Python Backend              ║
║   ML Fuel Prediction · Driving Profile · Dashboard   ║
╚══════════════════════════════════════════════════════╝
""")

# 1. Database & 2. Schema
print("  [1/4] Connecting to SQLite and verifying schema ...")
from backend.db import query_one, execute, get_conn  # type: ignore
try:
    sql = (HERE / "database" / "setup.sql").read_text()
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(sql)
    conn.commit()
    conn.close()
    print("  ✓  SQLite connected & Schema ready")
except Exception as e:
    print(f"  ✗  SQLite setup failed: {e}")
    sys.exit(1)

# Refresh admin password
try:
    import bcrypt  # type: ignore
    pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt(10)).decode()
    if query_one("SELECT id FROM users WHERE email='admin@ecu.com'"):
        execute("UPDATE users SET password_hash=%s WHERE email='admin@ecu.com'", (pw,))
    else:
        execute("INSERT INTO users(name,email,password_hash,vehicle_api_key,is_admin,is_active) VALUES(%s,%s,%s,%s,%s,%s)",
                ("Administrator","admin@ecu.com",pw,"ADMIN-KEY-001",1,1))
    print("  ✓  Admin user ready  (admin@ecu.com / admin123)")
except Exception as e:
    print(f"  ⚠  Admin setup: {e}")

# 3. ML Models
print("\n  [3/4] Loading / training ML models ...")
try:
    from backend.ml.predictor import get_predictor  # type: ignore
    p = get_predictor()
    m = p.get_metrics()
    if m and "regression" in m:
        print(f"  ✓  XGBoost Regressor  R²={m['regression']['xgb']['r2']}")
        print(f"  ✓  Ridge Regression   R²={m['regression']['ridge']['r2']}")
        print(f"  ✓  SVR (RBF)          R²={m['regression']['svr']['r2']}")
        print(f"  ✓  Classifier         Acc={m['classification']['xgb']['accuracy']}")
    else:
        print("  ✓  ML models ready")
except Exception as e:
    print(f"  ✗  ML failed: {e}")
    sys.exit(1)

# 4. Flask
if os.getenv("RENDER"):
    print("\n  [4/4] Setup complete. Skipping Flask server start because we are in Render build phase.")
    print("        Gunicorn will handle the server start.")
else:
    print(f"\n  [4/4] Starting Flask server on port {PORT} ...")
    print(f"""
      ┌─────────────────────────────────────────────────────┐
      │  Dashboard : http://localhost:{PORT}                   │
      │  Admin     : http://localhost:{PORT}/admin_login.html  │
      │  API Health: http://localhost:{PORT}/api/health        │
      │                                                     │
      │  Admin login: admin@ecu.com / admin123              │
      │  Press Ctrl+C to stop                               │
      └─────────────────────────────────────────────────────┘
    """)
    
    from app import create_app  # type: ignore
    flask_app = create_app()
    try:
        flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n  Server stopped.\n")
