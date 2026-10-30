"""Run verification for the realtime database (run by the builder, not shipped).

Starts the real server, connects TWO real socket clients, sends a message
from client A, and asserts client B receives it live AND that the message
is saved in SQLite (via the HTTP history endpoint). Prints evidence lines.
"""
import os
import subprocess
import sys
import time
import urllib.request
import json

HERE = os.path.dirname(os.path.abspath(__file__))
VENV_PY = os.path.join(HERE, ".venv", "bin", "python")
DB = os.path.join(HERE, "realtime.db")
if os.path.exists(DB):
    os.remove(DB)

log = open(os.path.join(HERE, "server.log"), "w")
srv = subprocess.Popen([VENV_PY, "app.py"], cwd=HERE,
                       stdout=log, stderr=subprocess.STDOUT)
try:
    # Wait for the server to answer.
    for _ in range(50):
        try:
            with urllib.request.urlopen("http://127.0.0.1:5000/api/messages",
                                        timeout=2) as r:
                assert r.status == 200
            break
        except Exception:
            time.sleep(0.2)
    else:
        raise RuntimeError("server did not start")

    import socketio

    received_b = []

    client_b = socketio.Client()
    client_b.on("new_message", lambda m: received_b.append(m))
    client_a = socketio.Client()
    client_a.connect("http://127.0.0.1:5000")
    client_b.connect("http://127.0.0.1:5000")
    time.sleep(0.5)
    print("EVIDENCE: both clients connected (A=sender, B=receiver)")

    client_a.emit("send_message", {"user": "Ali", "text": "Hello live database"})
    deadline = time.time() + 8
    while time.time() < deadline and not received_b:
        time.sleep(0.1)
    assert received_b, "FAIL: client B never received the live push"
    assert received_b[0]["user"] == "Ali"
    assert received_b[0]["text"] == "Hello live database"
    print(f"EVIDENCE: client B received live push: {received_b[0]}")

    with urllib.request.urlopen("http://127.0.0.1:5000/api/messages",
                                timeout=5) as r:
        history = json.loads(r.read().decode())
    assert any(m["user"] == "Ali" and m["text"] == "Hello live database"
               for m in history), "FAIL: message not saved in SQLite"
    print(f"EVIDENCE: message saved in SQLite, history now: {history}")

    with urllib.request.urlopen("http://127.0.0.1:5000/", timeout=5) as r:
        page = r.read().decode()
    assert "Live Realtime Database" in page and "socket.io" in page
    print("EVIDENCE: web UI served (title + socket.io client present)")

    client_a.disconnect()
    client_b.disconnect()
    print("VERIFICATION PASSED: live push + SQLite save + web UI all work.")
finally:
    srv.terminate()
    try:
        srv.wait(timeout=5)
    except Exception:
        srv.kill()
    log.close()
    with open(os.path.join(HERE, "server.log")) as f:
        print("--- server log ---")
        print(f.read().strip())
