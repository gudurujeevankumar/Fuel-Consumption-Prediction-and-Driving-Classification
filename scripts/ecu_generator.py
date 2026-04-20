#!/usr/bin/env python3
"""
ECU Data Generator — Python
Simulates real-time ECU telemetry and writes to ecu_data.csv
Run: python3 scripts/ecu_generator.py
"""
import csv, os, random, time
from datetime import datetime
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "ecu_data.csv"
HEADERS  = ["timestamp","engine_rpm","vehicle_speed","throttle_position",
            "acceleration","engine_load","fuel_injection_rate","coolant_temperature","mass_air_flow"]

state = {"rpm":800,"speed":0,"throttle":5,"load":20,"coolant":30,
         "profile":0,"timer":0,"duration":random.randint(30,90)}

def targets():
    if state["profile"]==0: return {"rpm":(900,2000),"speed":(15,60),"throttle":(8,30),"load":(18,50)}
    if state["profile"]==1: return {"rpm":(1400,3500),"speed":(35,90),"throttle":(22,55),"load":(38,72)}
    return {"rpm":(2800,6500),"speed":(75,140),"throttle":(58,92),"load":(62,95)}

def smooth(v, lo, hi, r=0.07):
    return v + r*(random.uniform(lo,hi)-v)

def step():
    state["timer"] += 1
    if state["timer"] >= state["duration"]:
        state["profile"]  = random.choices([0,1,2],[0.5,0.3,0.2])[0]
        state["duration"] = random.randint(25,85)
        state["timer"]    = 0
    t = targets()
    prev_speed = state["speed"]
    state["rpm"]      = max(t["rpm"][0],     min(t["rpm"][1],     smooth(state["rpm"],     *t["rpm"])))
    state["speed"]    = max(t["speed"][0],   min(t["speed"][1],   smooth(state["speed"],   *t["speed"],   0.04)))
    state["throttle"] = max(t["throttle"][0],min(t["throttle"][1],smooth(state["throttle"],*t["throttle"])))
    state["load"]     = max(t["load"][0],    min(t["load"][1],    smooth(state["load"],    *t["load"],    0.07)))
    if state["coolant"] < 85: state["coolant"] = min(85, state["coolant"]+random.uniform(0.2,0.9))
    else: state["coolant"] = max(82,min(102,state["coolant"]+random.uniform(-0.4,0.4)))
    maf   = max(1, state["rpm"]/600*(state["throttle"]/100)*12 + random.uniform(-0.4,0.4))
    fuel  = max(0.3,min(28, 0.00038*state["rpm"]+0.048*state["load"]+0.019*state["throttle"]+random.uniform(-0.08,0.08)))
    accel = (state["speed"]-prev_speed)/3.6
    return {"timestamp":datetime.utcnow().isoformat(),
            "engine_rpm":round(state["rpm"],1),"vehicle_speed":round(state["speed"],1),
            "throttle_position":round(state["throttle"],1),"acceleration":round(accel,3),
            "engine_load":round(state["load"],1),"fuel_injection_rate":round(fuel,3),
            "coolant_temperature":round(state["coolant"],1),"mass_air_flow":round(maf,2)}

new_file = not CSV_PATH.exists()
print("⚡ ECU Data Generator running → ecu_data.csv\nPress Ctrl+C to stop\n")
LABELS = {0:"🌿 ECO",1:"🚗 NORMAL",2:"🔥 AGGRESSIVE"}
try:
    while True:
        row = step()
        with open(CSV_PATH,"a",newline="") as f:
            w=csv.writer(f)
            if new_file: w.writerow(HEADERS); new_file=False
            w.writerow([row[h] for h in HEADERS])
        print(f"\r  RPM:{row['engine_rpm']:>6.0f}  Speed:{row['vehicle_speed']:>5.1f}km/h  "
              f"Fuel:{row['fuel_injection_rate']:>5.2f}L/h  {LABELS[state['profile']]}   ", end="", flush=True)
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nGenerator stopped.")
