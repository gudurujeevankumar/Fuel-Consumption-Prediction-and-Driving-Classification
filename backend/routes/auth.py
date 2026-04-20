"""Auth routes — mirrors routes/auth.js exactly"""
from flask import Blueprint, request, session, jsonify
from backend.db import query, query_one, execute
from backend.middleware.auth import require_user
import bcrypt

auth_bp = Blueprint("auth", __name__)

VEHICLE_MAP = {
    "TYT": ["Toyota", "Innova Crysta", 2022],
    "HON": ["Honda", "City", 2023],
    "MAR": ["Maruti", "Swift", 2021],
    "HYN": ["Hyundai", "Creta", 2023],
    "KIA": ["Kia", "Seltos", 2023],
    "TAT": ["Tata", "Nexon", 2023],
    "MHN": ["Mahindra", "XUV700", 2022],
    "BMW": ["BMW", "3 Series", 2022],
    "MRC": ["Mercedes-Benz", "C-Class", 2023],
}

@auth_bp.post("/register")
def register():
    d = request.get_json() or {}
    name = d.get("name","").strip()
    email = d.get("email","").strip().lower()
    password = d.get("password","")
    vehicle_api_key = d.get("vehicle_api_key","").strip().upper()

    if not all([name, email, password, vehicle_api_key]):
        return jsonify({"error": "All fields are required"}), 400

    existing = query("SELECT id FROM users WHERE email=%s OR vehicle_api_key=%s", (email, vehicle_api_key))
    if existing:
        return jsonify({"error": "Email or vehicle API key already registered"}), 409

    prefix = vehicle_api_key[:3]
    make, model, year = VEHICLE_MAP.get(prefix, ["Generic", "Sedan", 2020])
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()

    new_id = execute(
        "INSERT INTO users (name,email,password_hash,vehicle_api_key,vehicle_company,vehicle_model,vehicle_year) VALUES(%s,%s,%s,%s,%s,%s,%s)",
        (name, email, pw_hash, vehicle_api_key, make, model, year)
    )
    return jsonify({"success": True, "user": {"id": new_id, "name": name, "email": email,
                    "vehicle_company": make, "vehicle_model": model, "vehicle_year": year,
                    "vehicle_api_key": vehicle_api_key}})

@auth_bp.post("/login")
def login():
    d = request.get_json() or {}
    email = d.get("email","").strip().lower()
    password = d.get("password","")
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = query_one("SELECT * FROM users WHERE email=%s", (email,))
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    if not user["is_active"]:
        return jsonify({"error": "Account is deactivated"}), 403
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    execute("UPDATE users SET last_login=NOW() WHERE id=%s", (user["id"],))
    session["userId"]  = user["id"]
    session["isAdmin"] = bool(user["is_admin"])

    return jsonify({"success": True, "is_admin": bool(user["is_admin"]),
                    "user": {"id": user["id"], "name": user["name"], "email": user["email"],
                             "vehicle_company": user["vehicle_company"],
                             "vehicle_model": user["vehicle_model"],
                             "vehicle_year": user["vehicle_year"],
                             "vehicle_api_key": user["vehicle_api_key"]}})

@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})

@auth_bp.get("/me")
@require_user
def me(user):
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"],
                    "is_admin": bool(user["is_admin"]),
                    "vehicle_company": user["vehicle_company"],
                    "vehicle_model": user["vehicle_model"],
                    "vehicle_year": user["vehicle_year"],
                    "vehicle_api_key": user["vehicle_api_key"]})
