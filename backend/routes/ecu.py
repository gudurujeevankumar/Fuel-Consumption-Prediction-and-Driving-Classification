"""ECU routes — mirrors routes/ecu.js exactly"""
import csv, os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from backend.db import query, execute
from backend.middleware.auth import require_user
from backend.ml.predictor import get_predictor

ecu_bp = Blueprint("ecu", __name__)
CSV_PATH = Path(__file__).parent.parent.parent / "ecu_data.csv"

# Simulation state (mirrors _simState in ecu.js)
_sim = {"rpm": 1800, "speed": 45, "throttle": 25, "load": 40, "coolant": 88}

def _synthetic_row():
    import random, math
    def sm(v, t): return v + 0.08*(t-v) + (random.random()-0.5)*8
    _sim["rpm"]      = max(800,  min(6500, sm(_sim["rpm"],      1500+random.random()*2500)))
    _sim["speed"]    = max(0,    min(130,  sm(_sim["speed"],    20+random.random()*80)))
    _sim["throttle"] = max(5,    min(90,   sm(_sim["throttle"], 15+random.random()*60)))
    _sim["load"]     = max(15,   min(90,   sm(_sim["load"],     25+random.random()*55)))
    _sim["coolant"]  = max(82,   min(98,   sm(_sim["coolant"],  90)))
    maf   = max(1, _sim["rpm"]/600 + random.random())
    accel = (random.random()-0.5)*1.5
    fuel  = max(0.3, _sim["rpm"]*0.00028 + _sim["load"]*0.04 + _sim["throttle"]*0.018)
    return {
        "engine_rpm":          round(_sim["rpm"],1),
        "vehicle_speed":       round(_sim["speed"],1),
        "throttle_position":   round(_sim["throttle"],1),
        "acceleration":        round(accel,3),
        "engine_load":         round(_sim["load"],1),
        "fuel_injection_rate": round(fuel,3),
        "coolant_temperature": round(_sim["coolant"],1),
        "mass_air_flow":       round(maf,2),
    }

def _read_csv():
    try:
        if not CSV_PATH.exists(): return None
        lines = CSV_PATH.read_text().strip().split("\n")
        if len(lines) < 2: return None
        headers = [h.strip() for h in lines[0].split(",")]
        values  = lines[-1].split(",")
        row = {}
        for h, v in zip(headers, values):
            try: row[h] = float(v)
            except: row[h] = 0
        return row
    except: return None

def _save_telemetry(user_id, session_id, ecu, pred):
    row_id = execute(
        """INSERT INTO telemetry_log
           (user_id,session_id,engine_rpm,vehicle_speed,throttle_position,
            acceleration,engine_load,fuel_injection_rate,coolant_temperature,
            mass_air_flow,fuel_predicted_xgb,fuel_predicted_ridge,fuel_predicted_svr,
            fuel_avg,driving_label,driving_code,speed_alert)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (user_id, session_id,
         ecu.get("engine_rpm",0), ecu.get("vehicle_speed",0),
         ecu.get("throttle_position",0), ecu.get("acceleration",0),
         ecu.get("engine_load",0), ecu.get("fuel_injection_rate",0),
         ecu.get("coolant_temperature",85), ecu.get("mass_air_flow",0),
         pred["fuel_xgb"], pred["fuel_ridge"], pred["fuel_svr"], pred["fuel_avg"],
         pred["driving_label"], pred["driving_code"], int(pred["speed_alert"]))
    )
    if pred["speed_alert"]:
        execute("INSERT INTO alerts(user_id,session_id,alert_type,rpm_value,speed_value) VALUES(%s,%s,%s,%s,%s)",
                (user_id, session_id, "overspeeding", ecu.get("engine_rpm",0), ecu.get("vehicle_speed",0)))
    if pred["driving_label"] == "Aggressive":
        execute("INSERT INTO alerts(user_id,session_id,alert_type,rpm_value,speed_value) VALUES(%s,%s,%s,%s,%s)",
                (user_id, session_id, "aggressive_driving", ecu.get("engine_rpm",0), ecu.get("vehicle_speed",0)))
    return row_id

def _append_csv(ecu):
    cols = ["engine_rpm","vehicle_speed","throttle_position","acceleration",
            "engine_load","fuel_injection_rate","coolant_temperature","mass_air_flow"]
    try:
        new = not CSV_PATH.exists()
        with open(CSV_PATH, "a", newline="") as f:
            w = csv.writer(f)
            if new: w.writerow(["timestamp"] + cols)
            w.writerow([datetime.utcnow().isoformat()] + [ecu.get(c,0) for c in cols])
    except: pass

@ecu_bp.get("/live")
@require_user
def live(user):
    session_id = request.args.get("session_id") or f"sess-{int(datetime.utcnow().timestamp()*1000)}"
    ecu = _read_csv() or _synthetic_row()
    pred = get_predictor().predict(ecu)
    log_id = _save_telemetry(user["id"], session_id, ecu, pred)
    return jsonify({"session_id": session_id, "timestamp": datetime.utcnow().isoformat(),
                    "ecu": ecu, "prediction": pred, "log_id": log_id})

@ecu_bp.post("/ingest")
@require_user
def ingest(user):
    body = request.get_json() or {}
    required = ["engine_rpm","vehicle_speed","throttle_position","engine_load","coolant_temperature","mass_air_flow"]
    missing = [f for f in required if body.get(f) is None]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    ecu = {
        "engine_rpm":          float(body.get("engine_rpm",0)),
        "vehicle_speed":       float(body.get("vehicle_speed",0)),
        "throttle_position":   float(body.get("throttle_position",0)),
        "acceleration":        float(body.get("acceleration",0)),
        "engine_load":         float(body.get("engine_load",0)),
        "fuel_injection_rate": float(body.get("fuel_injection_rate", float(body.get("engine_rpm",0))*0.0028)),
        "coolant_temperature": float(body.get("coolant_temperature",85)),
        "mass_air_flow":       float(body.get("mass_air_flow",0)),
    }
    session_id = body.get("session_id") or f"demo-{int(datetime.utcnow().timestamp()*1000)}"
    pred   = get_predictor().predict(ecu)
    log_id = _save_telemetry(user["id"], session_id, ecu, pred)
    _append_csv(ecu)
    return jsonify({"status":"ok","session_id":session_id,
                    "timestamp":datetime.utcnow().isoformat(),
                    "log_id":log_id,"ecu":ecu,"prediction":pred})

@ecu_bp.get("/history")
@require_user
def history(user):
    limit = min(int(request.args.get("limit",100)), 500)
    rows = query("SELECT * FROM telemetry_log WHERE user_id=%s ORDER BY timestamp DESC LIMIT %s",
                 (user["id"], limit))
    return jsonify({"count": len(rows), "logs": rows})
