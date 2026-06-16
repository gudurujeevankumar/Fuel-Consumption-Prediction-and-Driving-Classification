"""SQLite connection — drop-in replacement for db.js/pymysql"""
import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecu_analytics.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _prepare_sql(sql):
    sql = sql.replace("%s", "?")
    sql = sql.replace("NOW()", "CURRENT_TIMESTAMP")
    return sql

def query(sql, args=()):
    sql = _prepare_sql(sql)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, args)
        rows = cur.fetchall()
        return [dict(row) for row in rows]

def query_one(sql, args=()):
    sql = _prepare_sql(sql)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, args)
        row = cur.fetchone()
        return dict(row) if row else None

def execute(sql, args=()):
    sql = _prepare_sql(sql)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, args)
        conn.commit()
        return cur.lastrowid
