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
PORT = args.port or int(os.getenv("PORT", 5000))

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

# 1. Database
print("  [1/4] Connecting to MySQL ...")
from backend.db import query_one, execute, get_conn  # type: ignore
try:
    get_conn().close()
    print("  ✓  MySQL connected")
except Exception as e:
    if "1049" in str(e) or "Unknown database" in str(e):
        print("  ⚠  Database not found. Creating it ...")
        try:
            import pymysql
            conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                charset="utf8mb4"
            )
            db_name = os.getenv("DB_NAME", "ecu_analytics")
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
            conn.commit()
            conn.close()
            print(f"  ✓  Database '{db_name}' created successfully")
        except Exception as inner_e:
            print(f"  ✗  Could not create database '{db_name}': {inner_e}")
            sys.exit(1)
    else:
        print(f"  ✗  MySQL failed: {e}")
        print("     → Check DB_PASSWORD in .env and ensure MySQL is running")
        sys.exit(1)

# 2. Schema
print("  [2/4] Verifying database schema ...")
sql = (HERE / "database" / "setup.sql").read_text()
try:
    import pymysql  # type: ignore
    conn = get_conn()
    with conn.cursor() as cur:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            try: cur.execute(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower(): pass
    conn.commit(); conn.close()
    print("  ✓  Schema ready")
except Exception as e:
    print(f"  ⚠  Schema warning: {e}")

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
