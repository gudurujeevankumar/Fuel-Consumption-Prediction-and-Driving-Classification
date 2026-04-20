"""
ML Predictor — Real Python scikit-learn models.
Trains XGBoost(GradientBoosting)/Ridge/SVR regressors + classifier on startup.
Exact same output keys as the original predictor.js.
"""
import os, logging, numpy as np, joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)
MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)

LABEL_MAP = {0: "Eco", 1: "Normal", 2: "Aggressive"}


def _generate_data(n=5000):
    rng = np.random.default_rng(42)
    profiles = rng.choice([0, 1, 2], size=n, p=[0.40, 0.40, 0.20])
    rows = []
    for p in profiles:
        if p == 0:
            rpm=rng.uniform(800,2200); speed=rng.uniform(0,80)
            thr=rng.uniform(5,35);    load=rng.uniform(15,55)
        elif p == 1:
            rpm=rng.uniform(1500,4000); speed=rng.uniform(30,120)
            thr=rng.uniform(25,65);     load=rng.uniform(40,75)
        else:
            rpm=rng.uniform(3000,7000); speed=rng.uniform(80,200)
            thr=rng.uniform(60,100);    load=rng.uniform(65,100)
        maf   = max(2, rpm/600*(thr/100)*14 + rng.normal(0,0.8))
        accel = rng.uniform(-2,5) if p==2 else rng.uniform(-1,2)
        fuel  = max(0.3, min(30, (maf/14.7)*0.74*3.6 + rpm*0.00015 + load*0.018 + max(0,accel)*0.12 + rng.normal(0,0.08)))
        rows.append([rpm, speed, thr, load, maf, accel, fuel, p])
    arr = np.array(rows)
    return arr[:,:6], arr[:,6], arr[:,7].astype(int)


def train():
    logger.info("Training ML models on 5000 ECU samples...")
    X, y_fuel, y_label = _generate_data(5000)
    X_tr, X_te, yf_tr, yf_te, yl_tr, yl_te = train_test_split(X, y_fuel, y_label, test_size=0.2, random_state=42)

    sc = StandardScaler().fit(X_tr)
    Xs_tr, Xs_te = sc.transform(X_tr), sc.transform(X_te)

    # XGBoost equivalent (GradientBoosting)
    xgb_reg = GradientBoostingRegressor(n_estimators=200, max_depth=6, learning_rate=0.08, random_state=42)
    xgb_reg.fit(X_tr, yf_tr)

    ridge = Ridge(alpha=1.0).fit(Xs_tr, yf_tr)
    svr   = SVR(kernel="rbf", C=10, epsilon=0.05).fit(Xs_tr, yf_tr)

    xgb_cls = GradientBoostingClassifier(n_estimators=150, max_depth=5, learning_rate=0.1, random_state=42)
    xgb_cls.fit(X_tr, yl_tr)
    lr_cls = LogisticRegression(C=1.0, max_iter=1000, random_state=42).fit(Xs_tr, yl_tr)

    joblib.dump({"xgb_reg":xgb_reg,"ridge":ridge,"svr":svr,
                 "xgb_cls":xgb_cls,"lr_cls":lr_cls,"scaler":sc}, MODEL_DIR/"models.pkl")

    from sklearn.metrics import r2_score, accuracy_score
    m = {
        "regression": {
            "xgb":   {"r2": round(float(r2_score(yf_te, xgb_reg.predict(X_te))),4)},
            "ridge": {"r2": round(float(r2_score(yf_te, ridge.predict(Xs_te))),4)},
            "svr":   {"r2": round(float(r2_score(yf_te, svr.predict(Xs_te))),4)},
        },
        "classification": {
            "xgb": {"accuracy": round(float(accuracy_score(yl_te, xgb_cls.predict(X_te))),4)},
            "lr":  {"accuracy": round(float(accuracy_score(yl_te, lr_cls.predict(Xs_te))),4)},
        },
        "training_samples": 5000,
    }
    logger.info("XGB R²=%.4f | Ridge R²=%.4f | SVR R²=%.4f | Cls Acc=%.4f",
                m["regression"]["xgb"]["r2"], m["regression"]["ridge"]["r2"],
                m["regression"]["svr"]["r2"], m["classification"]["xgb"]["accuracy"])
    return m


class ECUPredictor:
    def __init__(self):
        self._metrics = {}
        pkl = MODEL_DIR / "models.pkl"
        if not pkl.exists():
            self._metrics = train()
        else:
            logger.info("Loading pre-trained models...")
        d = joblib.load(pkl)
        self.xgb_reg  = d["xgb_reg"]
        self.ridge    = d["ridge"]
        self.svr      = d["svr"]
        self.xgb_cls  = d["xgb_cls"]
        self.lr_cls   = d["lr_cls"]
        self.scaler   = d["scaler"]
        logger.info("ECUPredictor ready.")

    def get_metrics(self):
        return self._metrics

    def predict(self, row):
        """Returns same keys as original predictor.js predict()"""
        x = np.array([[
            float(row.get("engine_rpm",0)),
            float(row.get("vehicle_speed",0)),
            float(row.get("throttle_position",0)),
            float(row.get("engine_load",0)),
            float(row.get("mass_air_flow",0)),
            float(row.get("acceleration",0)),
        ]])
        xs = self.scaler.transform(x)

        fuel_xgb   = float(np.clip(self.xgb_reg.predict(x)[0],  0.3, 30))
        fuel_ridge  = float(np.clip(self.ridge.predict(xs)[0],   0.3, 30))
        fuel_svr    = float(np.clip(self.svr.predict(xs)[0],     0.3, 30))
        fuel_avg    = round((fuel_xgb + fuel_ridge + fuel_svr) / 3, 3)

        driving_code      = int(self.xgb_cls.predict(x)[0])
        driving_label     = LABEL_MAP[driving_code]
        driving_label_lr  = LABEL_MAP[int(self.lr_cls.predict(xs)[0])]
        speed_alert       = float(row.get("vehicle_speed", 0)) > 100

        return {
            "fuel_xgb":        round(fuel_xgb, 3),
            "fuel_ridge":      round(fuel_ridge, 3),
            "fuel_svr":        round(fuel_svr, 3),
            "fuel_avg":        fuel_avg,
            "driving_label":   driving_label,
            "driving_label_lr": driving_label_lr,
            "driving_code":    driving_code,
            "speed_alert":     speed_alert,
        }


_instance = None
def get_predictor():
    global _instance
    if _instance is None:
        _instance = ECUPredictor()
    return _instance
