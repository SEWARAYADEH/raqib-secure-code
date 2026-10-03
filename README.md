# رقيب | Raqeeb

Raqeeb accepts source files or ZIP projects, builds evidence-backed structure and security observations, and keeps suspected issues separate from verified vulnerabilities. Uploaded code is parsed without execution. The application does not claim an exploit is closed unless functional tests, replay, re-scan, re-trace, and closure evidence succeed.

## Current scope

- Safe bounded intake for a single file or ZIP project. ZIP intake rejects traversal, links, nested archives, duplicate paths, encryption, binary source members, and resource-limit violations; it records skipped unsupported files and removes its temporary workspace.
- Python and JavaScript/JSX structure, evidence-backed Flask/FastAPI/Django/Express/React detection, framework routes, application relationships, and conservative data-flow observations. One-boundary cross-file evidence covers unshadowed Python `from ... import ...`, JavaScript named imports, and destructured CommonJS `require`; unresolved bindings stay explicit.
- Candidate findings and an explicit backend-owned lifecycle. Narrow Python SQLite, subprocess, and `Path`/`open` repair proposals require re-uploading the exact original file; they are syntax-checked, statically re-analyzed, and statically re-traced. The original remains immutable. A complete patched copy is encrypted with AES-GCM in the private analysis database, bound to its owner/finding and SHA-256, and is downloadable separately.
- Uploaded source is never executed on the host. A fail-closed OCI verifier runs reviewed single-file SQL/command scenarios only when Docker or Podman and a locally installed digest-pinned image pass capability checks. It denies network and capabilities, uses a read-only root/input mount, non-root identity, ephemeral quota, and process/memory/CPU/time limits. Runtime, functional, replay, and signed closure evidence are persisted separately. The prepared development host uses Docker Desktop with a digest-pinned Python image; real API-level SQL and command fixtures passed the complete closure gates on 2026-10-03.
- Signed user sessions through a short-lived email code for first access or password reset, followed by a server-verified password for normal sign-in. Session cookies last up to seven days. SMTP credentials are required to deliver a real code.
- A standalone HTML/CSS/vanilla-JavaScript portfolio at `/portfolio/index.html` with light/dark mode, process steps, the supplied Raqeeb guardian artwork, and seven synthetic SQL evaluation results read from SQLite. These results are static-analysis candidates, not proven exploits.
- The public page and focused upload flow read current formats, pack states, and stage availability from the backend options contract. All five focused packs now expose bounded static candidates and safe counterexamples. XSS and IDOR remain evidence-limited and do not claim output context, actor identity, ownership, exploitability, or closure beyond what the trace proves.
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

Run the backend tests with `.\.venv\Scripts\python.exe -m pytest -q` from `backend`, then `npm test` and `npm run build` from the frontend directory. Open `http://127.0.0.1:5173/` for the portfolio, `/login` for sign-in, and `/projects` for the owner-scoped dashboard after sign-in. Use the same hostname consistently so the browser reuses its session cookie. The dashboard and project structure explorer read saved analysis evidence; they do not retain or display raw uploaded source.

The first successful email verification opens Account and security, where the user can create a password. Later visits default to password sign-in without a fresh email code. A lost password can be reset only after a new verified email challenge. Password hashes, attempt throttling, and the seven synthetic example summaries live in ignored local SQLite files. Uploaded user code is never published through the examples endpoint. The owner's local checkout also has three explicitly requested development demo accounts in its ignored credential database. They are not part of a production deployment or the public Git repository; normal account creation keeps its stronger password policy.

The three **local demonstration** sign-ins are below. They work only in the owner's prepared local credential database and allowlist. The production configuration rejects these published addresses, even if a local database is copied accidentally.

| Email | Development password |
| --- | --- |
| `admin@securenergy.com` | `Admin@12345` |
| `user1@securenergy.com` | `User@12345` |
| `engineer@securenergy.com` | `Eng@12345` |

On a fresh clone, create these accounts locally with `backend\.venv\Scripts\python.exe backend\seed_demo_accounts.py` from the project root, then restart the backend. The command creates scrypt password hashes in the ignored local database and adds only the three demo addresses to the ignored `.env` allowlist. It refuses production mode and does not overwrite an existing account with a different password.

An optional `POST /send` mail service uses Flask-Mail with `smtp.gmail.com:587` and STARTTLS. It is disabled by default, requires a separate bearer token of at least 32 characters, and accepts only recipients listed in `MAIL_ALLOWED_RECIPIENTS`. To enable it, put `MAIL_SEND_ENABLED=true`, `MAIL_SEND_API_TOKEN`, `MAIL_ALLOWED_RECIPIENTS`, `EMAIL_USER`, and `EMAIL_PASS` in the ignored `backend/.env`; the exact template is `backend/.env.example`. The JSON body is `{"to":"recipient@example.com","subject":"Subject","body":"Plain text"}`. A successful HTTP 200 means Gmail SMTP accepted the message, not that it reached the inbox. Use an authorized Gmail/Workspace sender and app password; sender display name is `Raqeeb`. Keep the existing Hostinger OTP SMTP settings separate. Gmail delivery also depends on [Google's sender authentication and reputation requirements](https://support.google.com/mail/answer/81126); application code cannot guarantee inbox placement.

The trusted evaluation corpus and actual test outcomes are persisted in the ignored private SQLite database `backend/instance/training_evaluation.sqlite3`. From the project root, run `backend\.venv\Scripts\python.exe backend\record_training_tests.py` to run the suites, save per-test outcomes, and export trusted synthetic cases to `backend/instance/training_cases.jsonl`. Uploaded user code is excluded. See `training/README.md` for the labels and limitations; no machine-learning model has been trained.

Optional runtime verification uses `RUNTIME_OCI_ENGINE=docker` or `podman` and a `RUNTIME_OCI_IMAGE` pinned with `@sha256:<digest>`. Raqeeb never pulls an image during a request and refuses mutable tags, a missing daemon, or an absent pinned image. The user must re-upload the exact immutable original before verification. A closure record is written only when runtime-before, target-function smoke test, replay-after, static re-scan, and static re-trace all pass; customer source remains ineligible for training without a separate explicit consent policy.

## Deployment gate

Set `APP_ENV=production`, strong independent `SECRET_KEY`, `ANALYSIS_API_TOKEN`, `RECORD_INTEGRITY_KEY`, `PATCH_ARTIFACT_ENCRYPTION_KEY`, and `EMAIL_VERIFICATION_HMAC_KEY`, a private database path, and the exact HTTPS `FRONTEND_ORIGIN`. Real OTP also requires `VERIFICATION_ALLOWED_EMAILS`, `SMTP_USERNAME`, `SMTP_PASSWORD` (prefer a dedicated Hostinger Email app password if supported), and `SMTP_SENDER`. Keep these values in the host secret store, never in Git. Run one backend worker until challenge state is moved to a shared store. A public GitHub repository is source hosting, not a running deployment.

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for implementation status, [docs/PROJECT_AUDIT_FULL.md](docs/PROJECT_AUDIT_FULL.md) for the complete tracked source inventory and goals 1–20 boundary, [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for the target folder map, [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) for current responsibility mapping, [docs/FOCUSED_SCOPE.md](docs/FOCUSED_SCOPE.md) for the five-pack product scope, [docs/WORKFLOW_AND_STORAGE.md](docs/WORKFLOW_AND_STORAGE.md) for upload/storage responsibility, [docs/REPORTING_MODEL.md](docs/REPORTING_MODEL.md) for report and closure states, [GOALS_1_TO_10_AUDIT.md](GOALS_1_TO_10_AUDIT.md) for evidence and limits, and [HOSTINGER_DEPLOYMENT.md](HOSTINGER_DEPLOYMENT.md) for the hosting gate.

The Arabic handoff proposal is [PROJECT_PROPOSAL_AR.md](PROJECT_PROPOSAL_AR.md).
