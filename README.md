# Live Realtime Database in Python

Type a message in one browser window and it appears **instantly** in every
other open window. No refresh, no polling: the server pushes it over a
websocket the moment it is saved.

## How it works

1. Browser opens `http://127.0.0.1:5000` and connects with Socket.IO.
2. Sending a message emits a `send_message` event to the server.
3. The server **saves it in SQLite** (`realtime.db`) and **pushes**
   a `new_message` event to every other connected client.
4. Every client renders the message the moment the push arrives.
   Reloading the page re-loads the saved history from `/api/messages`.

This is a local realtime demo built with Flask + Flask-SocketIO. It is
**not** Firebase and does not claim to be: no Firebase project, keys, or
account are involved.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000` in **two** browser windows, type in one,
and watch the other update live.

## Files

- `app.py` — Flask server, SQLite storage, Socket.IO push logic.
- `templates/index.html` — the chat UI (plain HTML + JS).
- `requirements.txt` — `flask`, `flask-socketio`.
- `verify.py` — builder's run check (two real socket clients + SQLite
  history check). Not needed to run the app.
