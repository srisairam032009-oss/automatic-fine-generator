from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import sqlite3
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

app.secret_key = "automatic-fine-generator"

DATABASE = "fines.db"


# ==========================================
# FINE RULES
# ==========================================

FINE_RULES = {
    "No Helmet": 1000,
    "No Seat Belt": 1000,
    "Over Speeding": 2000,
    "Using Mobile While Driving": 5000,
    "Driving Without License": 5000,
    "Wrong Parking": 500,
    "Signal Jump": 1000,
    "Drunk Driving": 10000
}


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fines (

            fine_id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            phone TEXT,

            vehicle_no TEXT NOT NULL,

            vehicle_type TEXT,

            violation TEXT NOT NULL,

            amount INTEGER NOT NULL,

            fine_date TEXT NOT NULL,

            due_date TEXT NOT NULL,

            status TEXT NOT NULL

        )
    """)

    conn.commit()

    conn.close()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def index():

    conn = get_db()

    search = request.args.get("search", "").strip()

    if search:

        fines = conn.execute("""
            SELECT *
            FROM fines
            WHERE fine_id LIKE ?
               OR name LIKE ?
               OR vehicle_no LIKE ?
               OR violation LIKE ?
            ORDER BY rowid DESC
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

    else:

        fines = conn.execute("""
            SELECT *
            FROM fines
            ORDER BY rowid DESC
        """).fetchall()

    total_fines = conn.execute("""
        SELECT COUNT(*)
        FROM fines
    """).fetchone()[0]

    total_amount = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM fines
    """).fetchone()[0]

    paid_amount = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM fines
        WHERE status = 'PAID'
    """).fetchone()[0]

    unpaid_amount = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM fines
        WHERE status = 'UNPAID'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        fines=fines,
        fine_rules=FINE_RULES,
        total_fines=total_fines,
        total_amount=total_amount,
        paid_amount=paid_amount,
        unpaid_amount=unpaid_amount,
        search=search
    )