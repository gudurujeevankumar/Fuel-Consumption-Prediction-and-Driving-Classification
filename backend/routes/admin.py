"""Admin routes — mirrors routes/admin.js"""
from flask import Blueprint, request, jsonify
from backend.db import query, query_one, execute
from backend.middleware.auth import require_admin

admin_bp = Blueprint("admin", __name__)

@admin_bp.get("/overview")
@require_admin
def overview(user):
    total_users   = query_one("SELECT COUNT(*) as n FROM users WHERE is_admin=0")["n"]
    active_users  = query_one("SELECT COUNT(*) as n FROM users WHERE is_admin=0 AND is_active=1")["n"]
    total_logs    = query_one("SELECT COUNT(*) as n FROM telemetry_log")["n"]
    total_alerts  = query_one("SELECT COUNT(*) as n FROM alerts")["n"]
    total_sessions= query_one("SELECT COUNT(DISTINCT session_id) as n FROM telemetry_log")["n"]
    recent = query(
        """SELECT u.name,u.email,u.vehicle_company,u.vehicle_model,
                  t.driving_label,t.vehicle_speed,t.timestamp
           FROM telemetry_log t JOIN users u ON t.user_id=u.id
           ORDER BY t.timestamp DESC LIMIT 10"""
    )
    return jsonify({"total_users":total_users,"active_users":active_users,
                    "total_logs":total_logs,"total_alerts":total_alerts,
                    "total_sessions":total_sessions,"recent_activity":recent})

@admin_bp.get("/users")
@require_admin
def users(user):
    rows = query(
        """SELECT u.id,u.name,u.email,u.vehicle_api_key,u.vehicle_company,
                  u.vehicle_model,u.vehicle_year,u.is_active,u.created_at,u.last_login,
                  COUNT(t.id) as log_count, MAX(t.driving_label) as last_label
           FROM users u LEFT JOIN telemetry_log t ON t.user_id=u.id
           WHERE u.is_admin=0 GROUP BY u.id ORDER BY u.created_at DESC"""
    )
    return jsonify({"users": rows})

@admin_bp.patch("/users/<int:uid>")
@require_admin
def toggle_user(user, uid):
    is_active = 1 if (request.get_json() or {}).get("is_active") else 0
    execute("UPDATE users SET is_active=%s WHERE id=%s AND is_admin=0", (is_active, uid))
    return jsonify({"success": True})

@admin_bp.get("/alerts")
@require_admin
def all_alerts(user):
    rows = query(
        """SELECT a.*,u.name as driver_name,u.email
           FROM alerts a JOIN users u ON a.user_id=u.id
           ORDER BY a.timestamp DESC LIMIT 200"""
    )
    return jsonify({"alerts": rows})
