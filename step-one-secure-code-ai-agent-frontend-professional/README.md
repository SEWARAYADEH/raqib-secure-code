# Step One / Raqeeb — Secure Code AI Agent

Professional React + Vite frontend for the existing Step One / Raqeeb product.

## Frontend-only boundary

This delivery does **not** include or simulate a real backend service. It contains no:

- Flask application
- database
- real authentication / authorization
- email service
- real TOTP implementation
- scanner engine
- AI model call
- real file-processing pipeline
- real session server
- invented backend URL or API endpoint

No `fetch()` or `axios` call is used. Security/product results come from isolated mock fixtures under `src/mock/`.

## Product flow

### Public

- `/` — Home
- `/how-it-works` — product workflow
- `/security-trust` — current trust/security boundary
- `/login` — sign in preview
- `/create-account` — account creation UX
- `/verify-email` — email OTP UX
- `/two-factor` — sign-in 2FA challenge
- `/forgot-password` — recovery start
- `/reset-password` — verification + password-reset UX

### Protected frontend preview

- `/projects` — projects
- `/analysis/new` — new analysis
- `/analysis/progress` — ordered analysis progress
- `/projects/:projectId/findings` — findings
- `/projects/:projectId/findings/:findingId` — finding detail
- `/projects/:projectId/workbench` — Secure Workbench
- `/projects/:projectId/report` — report
- `/configuration` — frontend preview of future AI / scan configuration
- `/account` — profile, security, sessions, sign out

Protected routes use an in-memory frontend guard for demonstration only. Backend authorization must replace and enforce this later.

## Core workflow

`Code → Finding → Evidence → Secure Change → Verification → Updated File`

The Secure Workbench keeps the file/function/line close to the finding, remediation candidate, and verification state.

## Identity preview

The frontend includes complete UX states for:

- sign in
- create account
- email verification OTP
- forgot/reset password
- two-factor challenge
- authenticator setup UX
- recovery codes
- frontend-only protected route behavior
- account security
- session preview
- sign out

These states are intentionally local/demo behavior. No cryptographic or server-side security is claimed.

## Arabic / English

- English: LTR
- Arabic: RTL
- technical content remains LTR where required: source code, filenames, paths, hashes, identifiers, CWE/CVE references, package names, and function names
- the same components serve both languages; Arabic is not a duplicated application

## Updated-file download

The existing updated-code download capability is preserved.

Implementation:

- `src/components/UpdatedFileDownload.jsx`
- `src/utils/fileDownload.js`

Filename rule:

`originalName_update_action.ext`

The final extension is preserved, including multi-dot filenames. If no reliable action exists, the fallback is `originalName_update.ext`.

## Project structure

The existing architecture remains intentionally small:

- `src/pages/`
- `src/components/`
- `src/api/` — local mock data boundary only; no real API calls
- `src/mock/`
- `src/hooks/`
- `src/utils/`
- `src/assets/`
- `src/styles.css`
- `src/auth.jsx`
- `src/i18n.jsx`
- `src/routes.jsx`

## Run locally

```bash
npm install
npm run dev
```

Production command available in `package.json`:

```bash
npm run build
```

There is no lint script in the current `package.json`.

## Validation executed in the delivery environment

PASS:

- 43 JS/JSX files parsed with the available TypeScript JSX parser
- 147 relative imports resolved
- unused-import heuristic
- CSS brace balance
- no `fetch()` / `axios`
- no dead `href="#"` / `to="#"`
- no `.py`, `.sql`, or `.php` backend files in the frontend project
- updated filename rules for `.py`, `.js`, `.tsx`, and multi-dot `.php`
- updated-code Blob/download test confirmed the downloaded Blob contains the updated content

Not executed successfully:

- `npm install` could not complete in this environment because registry packages are unavailable here; an offline attempt returned `ENOTCACHED`
- therefore `npm run build` could not be executed honestly in this environment
- no lint command exists in `package.json`

## Backend-only requirements remaining

A later backend/security phase still owns:

- real account creation and authentication
- password hashing and reset tokens
- email delivery and OTP verification
- TOTP secret generation/storage/verification
- recovery-code persistence
- sessions, revocation, and authorization
- upload validation, isolation, and storage
- language/framework detection
- code parsing and application understanding
- scanner rules and scan-profile definitions
- finding generation
- exploitability verification
- AI provider integration and credentials
- remediation orchestration
- functional testing
- re-scan / re-trace / replay
- evidence-backed remediation state
- report data and artifact storage
