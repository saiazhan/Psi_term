import os
import json
import logging
from logging.handlers import RotatingFileHandler
from time import perf_counter
from pathlib import Path

from flask import Flask, jsonify, send_from_directory, request, g
from dotenv import load_dotenv
import paramiko

ROOT = Path(__file__).resolve().parent.parent
BACKEND = Path(__file__).resolve().parent
LOG_DIR = BACKEND / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "psiterm.log"
logger = logging.getLogger("PsiTerm")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
load_dotenv(BACKEND / ".env")
logger.info("PsiTerm backend boot | root=%s | backend=%s", ROOT, BACKEND)

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
app.config["SECRET_KEY"] = os.getenv("APP_SECRET", "local-prototype-only")
SSH_USER = os.getenv("SSH_USER", "")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "")
SSH_TIMEOUT = float(os.getenv("SSH_TIMEOUT", "5"))

def load_devices():
    logger.debug("Reading inventory file: %s", BACKEND / "devices.json")
    with open(BACKEND / "devices.json", "r", encoding="utf-8") as fh:
        devices = json.load(fh)
    logger.info("Inventory loaded | count=%s", len(devices))
    return devices


DEVICES = load_devices()


@app.before_request
def request_log_start():
    g.request_started_at = perf_counter()
    logger.info("HTTP request | %s %s | client=%s", request.method, request.path, request.remote_addr)


@app.after_request
def request_log_end(response):
    elapsed = (perf_counter() - getattr(g, "request_started_at", perf_counter())) * 1000
    logger.info("HTTP response | %s %s | status=%s | %.1f ms", request.method, request.path, response.status_code, elapsed)
    return response


def check_ssh(device):
    logger.info("SSH check requested | id=%s | ip=%s | port=%s", device.get("id"), device.get("ip"), device.get("port"))
    if not SSH_USER or not SSH_PASSWORD:
        logger.warning("SSH check aborted: credentials are not configured")
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
        logger.info("SSH authentication succeeded | id=%s", device.get("id"))
        return {"ok": True, "message": "SSH authentication succeeded"}
    except paramiko.BadHostKeyException:
        logger.error("SSH host-key mismatch | id=%s", device.get("id"))
        return {"ok": False, "message": "Host key mismatch; verify device identity"}
    except paramiko.SSHException as exc:
        logger.warning("SSH failed | id=%s | reason=%s", device.get("id"), exc)
        return {"ok": False, "message": "SSH connection failed: " + str(exc)}
    except Exception as exc:
        logger.exception("Unexpected SSH check error | id=%s", device.get("id"))
        return {"ok": False, "message": "Connection failed: " + str(exc)}
    finally:
        client.close()
        logger.debug("SSH client closed | id=%s", device.get("id"))


@app.route("/")
def index():
    logger.debug("Serving frontend index")
    return send_from_directory(str(ROOT), "index.html")


@app.route("/api/devices")
def list_devices():
    # Only test inventory metadata is returned; credentials are never exposed.
    logger.info("API device inventory request")
    try:
        devices = load_devices()
        response_data = [{"id": d["id"], "name": d["name"], "ip": d["ip"], "port": d["port"]} for d in devices]
        logger.info("API device inventory success | count=%s", len(response_data))
        return jsonify(response_data)
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("API device inventory error")
        return jsonify({"error": "Unable to read backend/devices.json", "detail": str(exc)}), 500


@app.route("/api/ssh-check/<device_id>", methods=["POST"])
def ssh_check(device_id):
    logger.info("API SSH-check request | id=%s", device_id)
    device = next((d for d in DEVICES if d["id"] == device_id), None)
    if device is None:
        logger.warning("API SSH-check unknown device | id=%s", device_id)
        return jsonify({"ok": False, "message": "Unknown test device"}), 404
    result = check_ssh(device)
    logger.info("API SSH-check complete | id=%s | ok=%s", device_id, result.get("ok"))
    return jsonify(result)


if __name__ == "__main__":
    # Local-only test server. Do not expose this on the network.
    app.run(host="127.0.0.1", port=5000, debug=False)
