"""Auth middleware — mirrors middleware/auth.js"""
import functools
from flask import session, jsonify
from backend.db import query_one

def require_user(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("userId")
        if not user_id:
            return jsonify({"error": "Unauthorized — please log in"}), 401
        user = query_one("SELECT * FROM users WHERE id=%s AND is_active=1", (user_id,))
        if not user:
            return jsonify({"error": "User not found or inactive"}), 401
        kwargs["user"] = user
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("userId")
        if not user_id:
            return jsonify({"error": "Unauthorized — please log in"}), 401
        user = query_one("SELECT * FROM users WHERE id=%s AND is_active=1", (user_id,))
        if not user:
            return jsonify({"error": "User not found or inactive"}), 401
        if not user["is_admin"]:
            return jsonify({"error": "Admin access required"}), 403
        kwargs["user"] = user
        return f(*args, **kwargs)
    return decorated
