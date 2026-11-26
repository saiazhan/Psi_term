import os
import json
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv
import paramiko

ROOT = Path(__file__).resolve().parent.parent
BACKEND = Path(__file__).resolve().parent
load_dotenv(BACKEND / ".env")

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
app.config["SECRET_KEY"] = os.getenv("APP_SECRET", "local-prototype-only")
SSH_USER = os.getenv("SSH_USER", "")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "")
SSH_TIMEOUT = float(os.getenv("SSH_TIMEOUT", "5"))

with open(BACKEND / "devices.json", "r", encoding="utf-8") as fh:
    DEVICES = json.load(f)


def check_ssh(device):
    if not SSH_USER or not SSH_PASSWORD:
        return {"ok": False, "message": "SSH credentials are not configured in backend/.env"}

    client = paramiko.SSHClient()
    client.load_host_keys(str(BACKEND / "known_hosts"))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(
            hostname=device["ip"],
            port=int(device["port"]),
            username=SSH_USER,
            password=SSH_PASSWORD,
            timeout=SSH_TIMEOUT,
            banner_timeout=SSH_TIMEOUT,
            auth_timeout=SSH_TIMEOUT,
            allow_agent=False,
            look_for_keys=False,
        )
        return {"ok": True, "message": "SSH authentication succeeded"}
    except paramiko.BadHostKeyException:
        return {"ok": False, "message": "Host key mismatch; verify device identity"}
    except paramiko.SSHException as exc:
        return {"ok": False, "message": "SSH connection failed: " + str(exc)}
    except Exception as exc:
        return {"ok": False, "message": "Connection failed: " + str(exc)}
    finally:
        client.close()


@app.route("/")
def index():
    return send_from_directory(str(ROOT), "index.html")


@app.route("/api/devices")
def list_devices():
    # Only test inventory metadata is returned; credentials are never exposed.
    return jsonify([{"id": d["id"], "name": d["name"], "ip": d["ip"], "port": d["port"]} for d in DEVICES])


@app.route("/api/ssh-check/<device_id>", methods=["POST"])
def ssh_check(device_id):
    device = next((d for d in DEVICES if d["id"] == device_id), None)
    if device is None:
        return jsonify({"ok": False, "message": "Unknown test device"}), 404
    result = check_ssh(device)
    return jsonify(result)


if __name__ == "__main__":
    # Local-only test server. Do not expose this on the network.
    app.run(host="127.0.0.1", port=5000, debug=False)
