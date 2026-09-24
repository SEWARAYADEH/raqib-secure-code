# رقيب | Raqeeb

Raqeeb accepts source files or ZIP projects, builds evidence-backed structure and security observations, and keeps suspected issues separate from verified vulnerabilities. Uploaded code is parsed without execution. The application does not claim an exploit is closed unless functional tests, replay, re-scan, re-trace, and closure evidence succeed.

## Current scope

- Safe bounded intake for a single file or ZIP project.
- Python and JavaScript structure, framework routes, application relationships, and conservative data-flow observations. Cross-file call edges cover narrow, statically evidenced Python `from ... import ...` and JavaScript named-import function calls; cross-file data flow is unresolved.
- Candidate findings and an explicit verification lifecycle. Exploit replay and automatic patching remain blocked until an isolated execution environment is available.
- Signed user sessions through short-lived email codes. SMTP credentials are required to deliver a real code.
- Optional Codex advisor, disabled by default. Its output cannot verify closure.

## Local development

Use Python 3.13 and Node.js 20 or newer. Copy `backend/.env.example` to `backend/.env` and set the required secrets locally. The `.env` file and analysis database are ignored by Git.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

In a second terminal:

```powershell
cd step-one-secure-code-ai-agent-frontend-professional
npm ci
npm run dev
```

Run the backend tests with `.\.venv\Scripts\python.exe -m pytest -q` from `backend`, and the frontend build with `npm run build` from the frontend directory.

## Deployment gate

Set `APP_ENV=production`, strong independent `SECRET_KEY`, `ANALYSIS_API_TOKEN`, `RECORD_INTEGRITY_KEY`, and `EMAIL_VERIFICATION_HMAC_KEY`, a private database path, and the exact HTTPS `FRONTEND_ORIGIN`. Real OTP also requires `VERIFICATION_ALLOWED_EMAILS`, `SMTP_USERNAME`, `SMTP_PASSWORD` (an app-specific credential), and `SMTP_SENDER`. Keep these values in the host secret store, never in Git. Run one backend worker until challenge state is moved to a shared store. A public GitHub repository is source hosting, not a running deployment.

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for the verified implementation status and ordered remaining work.
