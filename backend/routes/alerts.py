"""Alerts routes — mirrors routes/alerts.js"""
from flask import Blueprint, jsonify
from backend.db import query
from backend.middleware.auth import require_user

alerts_bp = Blueprint("alerts", __name__)

@alerts_bp.get("/")
@require_user
def get_alerts(user):
    rows = query("SELECT * FROM alerts WHERE user_id=%s ORDER BY timestamp DESC LIMIT 100", (user["id"],))
    return jsonify({"alerts": rows})
