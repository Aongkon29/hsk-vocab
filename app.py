"""
HSK Vocab Trainer — Flask backend for PythonAnywhere.
Run locally:  python app.py
Deploy:        see README_DEPLOY.md
"""
import os
import json
import sqlite3
import secrets
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hsk.db")

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            token         TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id      INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            marks        TEXT NOT NULL DEFAULT '{}',
            known        TEXT NOT NULL DEFAULT '[]',
            unknown      TEXT NOT NULL DEFAULT '[]',
            best         INTEGER NOT NULL DEFAULT 0,
            theme        TEXT,
            recall       INTEGER,
            revise_list  TEXT NOT NULL DEFAULT '[]',
            rev_list     TEXT NOT NULL DEFAULT '[]',
            rev_idx      INTEGER NOT NULL DEFAULT 0,
            rev_known    TEXT NOT NULL DEFAULT '[]',
            rev_unknown  TEXT NOT NULL DEFAULT '[]',
            deck_pos     TEXT NOT NULL DEFAULT '{}',
            updated_at   TEXT
        )
    """)
    # add column if upgrading an existing DB
    try:
        c.execute("ALTER TABLE progress ADD COLUMN deck_pos TEXT NOT NULL DEFAULT '{}'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def user_by_token(token):
    if not token:
        return None
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
    conn.close()
    return row


def require_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user = user_by_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return f(user, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    if len(username) < 2 or len(password) < 4:
        return jsonify({"error": "Username min 2 chars, password min 4 chars."}), 400
    conn = get_db()
    try:
        token = secrets.token_hex(16)
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, token) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), token),
        )
        uid = cur.lastrowid
        conn.execute(
            "INSERT INTO progress (user_id) VALUES (?)", (uid,)
        )
        conn.commit()
        return jsonify({"ok": True, "user_id": uid, "token": token, "username": username})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already taken."}), 409
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid username or password."}), 401
    token = secrets.token_hex(16)
    conn = get_db()
    conn.execute("UPDATE users SET token = ? WHERE id = ?", (token, row["id"]))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "user_id": row["id"], "token": token, "username": username})


# ---------------------------------------------------------------------------
# Progress sync
# ---------------------------------------------------------------------------
PROGRESS_FIELDS = [
    "marks", "known", "unknown", "best", "theme", "recall",
    "revise_list", "rev_list", "rev_idx", "rev_known", "rev_unknown",
    "deck_pos",
]


def _json(v, default):
    try:
        return json.dumps(v if v is not None else default)
    except Exception:
        return json.dumps(default)


@app.route("/api/save", methods=["POST"])
@require_token
def save_progress(user):
    data = request.get_json(force=True)
    conn = get_db()
    sets = ", ".join(f"{f} = ?" for f in PROGRESS_FIELDS)
    vals = []
    for f in PROGRESS_FIELDS:
        v = data.get(f)
        if f == "best":
            vals.append(int(v or 0))
        elif f == "rev_idx":
            vals.append(int(v or 0))
        elif f == "recall":
            vals.append(1 if v else 0)
        elif f == "theme":
            vals.append(v)
        else:
            vals.append(_json(v, [] if f.endswith("list") or f.endswith("known") or f.endswith("unknown") else {}))
    vals.append(__import__("datetime").datetime.utcnow().isoformat())
    vals.append(user["id"])
    conn.execute(
        f"UPDATE progress SET {sets}, updated_at = ? WHERE user_id = ?",
        vals + [],
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/load", methods=["GET"])
@require_token
def load_progress(user):
    conn = get_db()
    row = conn.execute("SELECT * FROM progress WHERE user_id = ?", (user["id"],)).fetchone()
    conn.close()
    if not row:
        return jsonify({})
    out = {}
    for f in PROGRESS_FIELDS:
        v = row[f]
        if f in ("best", "rev_idx"):
            out[f] = v
        elif f == "recall":
            out[f] = bool(v) if v is not None else None
        elif f == "theme":
            out[f] = v
        else:
            try:
                out[f] = json.loads(v) if v else ([] if f.endswith("list") or f.endswith("known") or f.endswith("unknown") else {})
            except Exception:
                out[f] = [] if f.endswith("list") or f.endswith("known") or f.endswith("unknown") else {}
    return jsonify(out)


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(BASE_DIR, path)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
else:
    init_db()  # for WSGI
