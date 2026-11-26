# PsiTerm backend — Windows 7 local test

This backend is a small local prototype for the existing PsiTerm web UI.

## Features in this test
- Serves the existing repository frontend at `http://127.0.0.1:5000`.
- Provides `GET /api/devices` for the four test inventory entries.
- Provides `POST /api/ssh-check/<device_id>` for SSH handshake/authentication checks.
- Performs no remote command execution and does not open an interactive shell.
- Rejects unknown SSH host keys; verified host keys must be added to `known_hosts` first.
- Listens on localhost only.

## Windows 7 / Python 3.8 setup
1. Open Command Prompt in the repository root.
2. `python -m venv venv`
3. `venv\\Scripts\\activate`
4. `python -m pip install -r backend/requirements.txt`
5. Copy `backend/.env.example` to `backend/.env`; enter SSH username/password there. Do not share the file or commit it.
6. Add verified SSH host keys to `backend/known_hosts`.
7. Run `python backend/app.py`.
8. Open `http://127.0.0.1:5000`.

## Test devices
The four entries represent two test IPs with SSH ports 1022 and 2022 each. Adjust the test inventory only when you have confirmed the intended endpoints.

## Important
This is a local development prototype, not production authentication or a secure remote-management service. Do not publish it or expose port 5000. The SSH check only confirms connection/authentication and then closes the session. Host keys should be verified from a trusted source before adding them to `known_hosts`.
