"""Live-sync realtime database (local demo, no Firebase).

One message written in one browser window appears instantly in every other
open window: the server pushes it over a websocket AND saves it in SQLite
at the same time. Open http://127.0.0.1:5000 in two browser windows and try it.

Run:  pip install -r requirements.txt
       python app.py
"""
import sqlite3

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
DB = "realtime.db"


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "username TEXT NOT NULL,"
            "text TEXT NOT NULL,"
            "created_at TEXT DEFAULT (datetime('now')))"
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages")
def history():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "SELECT username, text, created_at FROM messages ORDER BY id"
        ).fetchall()
    return jsonify([{"user": u, "text": t, "at": a} for u, t, a in rows])


@socketio.on("connect")
def on_connect():
    print("Client connected", flush=True)


@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected", flush=True)


@socketio.on("send_message")
def on_message(data):
    user = (data.get("user") or "guest").strip() or "guest"
    text = (data.get("text") or "").strip()
    if not text:
        return
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO messages (username, text) VALUES (?, ?)", (user, text)
        )
    print(f"Saved + pushed live: {user}: {text}", flush=True)
    # Push to every OTHER connected client. The sender already shows its
    # own message locally, so skipping the sender avoids a duplicate.
    emit("new_message", {"user": user, "text": text},
         broadcast=True, skip_sid=request.sid)


if __name__ == "__main__":
    init_db()
    print("Realtime database running on http://127.0.0.1:5000", flush=True)
    socketio.run(app, host="127.0.0.1", port=5000, allow_unsafe_werkzeug=True)
