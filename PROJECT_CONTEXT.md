# Raqeeb Project Context

This file is the single working memory for future implementation. Read it before work. Do not rescan completed areas unless a failing test or a changed dependency makes that necessary.

## Product promise

Raqeeb must understand application structure and connect security evidence to its path and context. The required order is:

`Understand -> Trace -> Verify Exploitability -> Fix Root Cause -> Test Functionality -> Re-Verify -> Evidence of Closure`

## Final product acceptance map

The required product pipeline is:

`Upload -> Safe Intake -> Language Intelligence -> Parsing -> Application Understanding -> Application Graph -> Security Semantics -> Data Flow / Trace -> Security Analysis -> Exploitability Verification -> Root Cause -> Minimal Secure Patch -> Functional Verification -> Re-Scan -> Re-Trace -> Replay -> Evidence of Closure -> Report -> Download Updated File / Project`

The final system must securely accept a file or project; establish language using multiple evidence sources; identify project type and frameworks; extract files, functions, classes, imports, calls, variables, routes, APIs, database access, authentication, services, and dependencies; build application and call graphs without invented edges; identify sources, sinks, controls, and data flow; combine rules, sensors, dependency evidence, flow, and context; map proven findings to CWE/OWASP; distinguish observations from vulnerabilities; verify reachability and exploitability; identify root cause; create a minimal secure patch; preserve functionality through build and tests; re-scan, re-trace, and replay; produce evidence of closure and reports; and provide a new updated artifact without overwriting the original.

Sensors such as SAST, SCA, and AI may add evidence. They are not the reasoning or verification core. An observation is not a vulnerability. A path is not proof of exploitability. A finding is never closed without before-and-after evidence.

## Mandatory engineering rules

- Any imprecise behavior or claim is rejected.
- Any insecure implementation is rejected.
- Raqeeb must never collapse into a simple scanner or weak file analyzer; it must model application structure.
- The architecture is multi-language from the start. Python and JavaScript are the first verified parsers, not the final scope.
- Intake must establish language evidence, line count, source structure, functions, and syntax understanding. Submitted source may be processed internally but must not be echoed in API responses or logs.
- Unproven facts use explicit states such as `UNKNOWN`, `UNRESOLVED`, `CANDIDATE`, or `OBSERVED`.
- AI is not a security source of truth and cannot declare closure.
- SAST/SCA/scanners are future sensors, not the product core.
- Closure requires Test + Replay + Re-Scan + Re-Trace + Evidence.
- Remediation must address root cause with the smallest reviewable patch.
- Security changes must preserve original application functionality.
- Work proceeds incrementally, file by file, with a narrow reviewed scope.
- Every stage has tests and cannot advance until its tests pass.
- Dependencies, architecture, and features require a direct role in the product promise.
- The approved professional frontend is a stable baseline. Frontend changes are limited to necessary backend integration and truthful presentation of live evidence.
- Untrusted source code is parsed as data and is never executed during understanding or tracing.
- Prefer explicit uncertainty to guessed relationships or findings.
- Keep modules narrow, typed by contract, and independently testable.
- Do not return complete submitted source in API responses or write it to logs.
- Production configuration must fail closed when secrets are absent or weak.
- Implement one secure vertical slice before adding repositories, ZIP ingestion, scanners, AI, or remediation.
- Use only the context needed for the current stage. Do not rescan unrelated frontend pages, presentation assets, PDFs, or completed backend modules.

## Completed baseline review

- No `AGENTS.md` exists.
- The directory is not currently a Git repository.
- Frontend: React/Vite professional mock UI. It builds successfully but still uses mock API data.
- Backend before this work: Flask app factory, health route, safe text intake, language evidence, Tree-sitter parsing for Python/JavaScript, local call relationships, and source/sink observations.
- Baseline before continuation: 35 backend tests passed; frontend production build passed.
- Known presentation risk: the mock UI must not be described as a working verification engine.

## Implemented in this continuation

1. Completed parser assignment extraction for Python and JavaScript.
2. Added call argument text and structured argument expressions.
3. Added conservative intra-function data flow:
   - source -> assignment -> identifier propagation -> sensitive sink;
   - no cross-function claims;
   - direct and heuristic evidence remain distinct;
   - output is `SOURCE_TO_SENSITIVE_SINK_PATH` with status `OBSERVED`, never a vulnerability.
4. Added `POST /api/v1/analysis/source` as the first secure vertical API slice:
   - accepts exactly one multipart source file;
   - bounded request and file reads;
   - local-only access by default, or constant-time bearer-token comparison when configured;
   - unified JSON result containing intake metadata, language evidence, structure, relationships, semantics, and data-flow evidence;
   - never echoes the full submitted source;
   - versioned result schema and explicit execution/finding policies.
5. Added request IDs, no-store and defensive HTTP headers, JSON 413 errors, production secret validation, and disabled hardcoded Flask debug mode.
6. Added `.gitignore` coverage for secrets, virtual environments, caches, builds, logs, and archives.

Current verified baseline: **141 backend tests passed** and the frontend production build passed (76 transformed modules). A persistence smoke test returned `persisted: true`.

## Current module map

- `backend/app/intake.py`: bounded UTF-8 source intake and artifact metadata.
- `backend/app/language_detection.py`: extension/shebang evidence and conflict handling.
- `backend/app/parser_engine.py`: Tree-sitter structure, assignments, calls, and arguments.
- `backend/app/framework_intelligence.py`: evidence-backed Flask, Express, React, route, authentication, and authorization understanding.
- `backend/app/application_context.py`: dependencies, service instances, database-operation candidates, and security context without effectiveness claims.
- `backend/app/project_understanding.py`: project type, cross-file import resolution, project graph, and explicit ambiguous/unresolved relations.
- `backend/app/project_calls.py`: partial static Python cross-file call resolution only for unique, top-level, unshadowed `from ... import ...` bindings. Other calls and all cross-file data flow remain unresolved.
- `backend/app/relationship_model.py`: conservative local call resolution.
- `backend/app/security_semantics.py`: source/sink observations; no findings.
- `backend/app/data_flow.py`: conservative intra-function evidence paths.
- `backend/app/application_model.py`: stable typed nodes and evidence-backed edges shared by later engines.
- `backend/app/analysis_service.py`: ordered analysis orchestration and response contract.
- `backend/app/http_security.py`: request identity, access gate, and response headers.
- `backend/app/api_errors.py`: shared API error envelope.
- `backend/app/routes.py`: health and versioned single-file analysis endpoints.
- `backend/app/control_flow.py`: explicit branch regions and mutually exclusive path constraints.
- `backend/app/interprocedural_flow.py`: one-boundary local source-to-sink tracing.
- `backend/app/auth.py`: explicit analysis principals, roles, and scopes.
- `backend/app/analysis_store.py`: append-only SQLite records with HMAC-SHA256 integrity checks and owner enforcement.
- `backend/app/workspace.py`: temporary workspace creation, path containment, and verified cleanup.
- `backend/app/archive_intake.py`: bounded ZIP intake with traversal, symlink, collision, depth, count, size, nested-archive, and compression-ratio defenses.
- `backend/app/archive_service.py`: safe project analysis with per-file results and project understanding without executing source.
- `backend/app/archive_routes.py`: authenticated archive-analysis API.
- `frontend/src/api/client.js`: real no-store API client and structured error handling.
- `frontend/src/pages/NewAnalysisPage.jsx`: live single-file and ZIP submission.
- `frontend/src/pages/AnalysisProgressPage.jsx`: truthful live evidence rendering; observations are never labeled vulnerabilities.
- `backend/app/finding_model.py`: evidence-gated finding candidates; sink presence alone never creates a candidate.
- `backend/app/finding_lifecycle.py`: enforced state transitions and five-part closure evidence gate.
- `backend/app/verification_planner.py`: fail-closed sandbox replay plans and capability restrictions.
- `backend/app/pipeline_state.py`: truthful per-stage completion, blocker, and updated-artifact availability.
- `backend/app/email_verification.py`: single-use HMAC email challenges with expiry, resend throttling, and attempt limits.
- `backend/app/email_verification_routes.py`: email verification, signed user sessions, session restore, and logout.
- `backend/app/codex_advisor.py`: optional OpenAI Responses API advisor with strict structured output, `store:false`, minimal context, and no verification authority.

## Current runtime configuration

- 2026-09-24 OTP diagnosis: the browser's `127.0.0.1:5173` origin was missing from local `FRONTEND_ORIGIN`; it is now allowed. A direct API request now reaches the email service and returns `503 EMAIL_DELIVERY_UNAVAILABLE` because SMTP credentials are absent. No real email has been delivered or verified.
- Public repository preparation: personal address remains only in ignored `backend/.env`; tracked files contain no personal allowlist, secret, or analysis database. Root `README.md` states the current implementation limits.
- Public repository: `https://github.com/SEWARAYADEH/raqib-secure-code` on `main`. GitHub Actions checks backend tests and frontend build on pushes and pull requests. The environment-independent test fix passed both CI jobs in run `35981311858`; recheck CI after each push.
- Hostinger mailbox `raqib@alaseeltech.com` exists. Local ignored `backend/.env` has `smtp.hostinger.com`, SSL port 465, and this mailbox as SMTP username/sender. `SMTP_PASSWORD` is empty, so OTP is still unavailable. Mailbox password setup and entry into `.env` require user handling; never commit or print it.
- Hostinger accepted `raqib.alaseeltech.com` as the domain for a new PHP/HTML site. The site contains no deployed Raqeeb frontend or backend. DNS/HTTPS and actual deployment are unverified; GitHub is source hosting, not running application hosting.
- Local immutable analysis storage is enabled in ignored `backend/.env`; secrets and integrity keys are random and at least 32 characters.
- Signed sessions use `HttpOnly`, `SameSite=Strict`, a 30-minute lifetime, scoped RBAC, and trusted-origin enforcement on state-changing session requests.
- Email verification uses an allowlist configured only in ignored `backend/.env`; real delivery remains unavailable until `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_SENDER` are configured outside source control.
- The Codex advisor is implemented but disabled until an approved `OPENAI_API_KEY` and explicit `OPENAI_MODEL` are configured.
- Exploit replay is blocked because this host has neither Docker nor Podman. Uploaded code remains unexecuted.

## Strict next order

1. Keep the backend suite green and review only files changed by a failure.
2. Configure a disposable isolation runtime before executing any uploaded code; keep verification blocked until then.
3. Configure SMTP and the optional Codex advisor only through environment secrets.
4. Expand the narrowly verified Python cross-file call subset and add JavaScript binding resolution only with equivalent evidence; do not claim repository-level data-flow traces yet.
5. Execute exploitability verification, then root-cause remediation, functional tests, replay, re-scan, re-trace, closure evidence, and updated-artifact download in that order.

## Deferred by design

- No uploaded-code execution or exploit testing because an approved isolation runtime is unavailable.
- ZIP project intake is supported. Direct folder, repository URL, and running-application intake remain unsupported.
- No vulnerability declaration, CWE/severity assignment, or verified-closed state.
- No job queue, sandbox runtime, external SAST/SCA sensor, or enabled AI call yet.
- No patch or updated download is exposed before verified exploitability and closure evidence.
