-- ECU Analytics — Database Setup (SQLite)

-- Users
CREATE TABLE IF NOT EXISTS users (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  name             VARCHAR(120)  NOT NULL,
  email            VARCHAR(180)  NOT NULL UNIQUE,
  password_hash    VARCHAR(255)  NOT NULL,
  vehicle_api_key  VARCHAR(100)  NOT NULL UNIQUE,
  vehicle_company  VARCHAR(100),
  vehicle_model    VARCHAR(100),
  vehicle_year     SMALLINT,
  is_active        TINYINT(1)    DEFAULT 1,
  is_admin         TINYINT(1)    DEFAULT 0,
  created_at       DATETIME      DEFAULT CURRENT_TIMESTAMP,
  last_login       DATETIME
);

-- Telemetry Log
CREATE TABLE IF NOT EXISTS telemetry_log (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id              INT           NOT NULL,
  session_id           VARCHAR(60)   NOT NULL,
  timestamp            DATETIME      DEFAULT CURRENT_TIMESTAMP,
  engine_rpm           FLOAT,
  vehicle_speed        FLOAT,
  throttle_position    FLOAT,
  acceleration         FLOAT,
  engine_load          FLOAT,
  fuel_injection_rate  FLOAT,
  coolant_temperature  FLOAT,
  mass_air_flow        FLOAT,
  fuel_predicted_xgb   FLOAT,
  fuel_predicted_ridge FLOAT,
  fuel_predicted_svr   FLOAT,
  fuel_avg             FLOAT,
  driving_label        VARCHAR(12),
  driving_code         TINYINT,
  speed_alert          TINYINT(1)    DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_telemetry_user ON telemetry_log(user_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry_log(session_id);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INT          NOT NULL,
  session_id  VARCHAR(60),
  alert_type  VARCHAR(30)  NOT NULL,
  rpm_value   FLOAT,
  speed_value FLOAT,
  timestamp   DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);

-- Drive Sessions
CREATE TABLE IF NOT EXISTS drive_sessions (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id         INT      NOT NULL,
  session_id      VARCHAR(60) UNIQUE,
  started_at      DATETIME,
  ended_at        DATETIME,
  avg_fuel        FLOAT,
  avg_speed       FLOAT,
  max_speed       FLOAT,
  eco_pct         FLOAT,
  normal_pct      FLOAT,
  aggressive_pct  FLOAT,
  alert_count     INT DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Admin User (password: admin123)
INSERT OR IGNORE INTO users (name, email, password_hash, vehicle_api_key, is_admin, is_active)
VALUES (
  'Administrator',
  'admin@ecu.com',
  '$2b$10$rQnK8JzXmP2vL9wE3dF1.OQqZYp8mNcXkH5tV7sA4bR6uJ0eI2yG.',
  'ADMIN-KEY-001',
  1, 1
);
