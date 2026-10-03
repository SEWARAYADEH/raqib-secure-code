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
- The directory is a Git repository with a public GitHub remote. Authenticated analysis, saved results, findings, report, and project workspace now use owner-scoped API records.
- Frontend: React/Vite professional UI. Its analysis flow accepts supported source files and ZIP projects, and its production build passes.
- Backend before this work: Flask app factory, health route, safe text intake, language evidence, Tree-sitter parsing for Python/JavaScript, local call relationships, and source/sink observations.
- Baseline before continuation: 35 backend tests passed; frontend production build passed.
- Known presentation risk: static candidates must not be described as verified exploitability or completed repair.

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

Current verified baseline (2026-09-24): **155 backend tests passed** and the frontend production build passed (76 transformed modules). A persistence smoke test returned `persisted: true`.

## Current module map

Latest lifecycle continuation: supported single-file SQL/command findings can persist a complete patched copy encrypted at rest, download it without overwriting the original, and download a finding security report. The backend lifecycle endpoint is the only status source used by Finding Detail. Static re-scan/re-trace can pass, but runtime verification, functional execution, and replay remain `NOT_AVAILABLE` because this host has no reviewed Docker/Podman/WSL isolation runtime; closure therefore remains `CLOSURE_INCOMPLETE`.

Latest understanding continuation (2026-10-03): the existing ZIP intake now reports bounded extraction evidence and rejects binary source members in addition to traversal, links, nested archives, duplicate paths, encryption, and resource-limit violations. Framework evidence covers Flask, FastAPI, Django, Express, and React. Statically resolved Python imports, JavaScript named imports, and destructured CommonJS `require` calls can form a one-call-boundary cross-file Source → Argument → Parameter → Sink path and persisted project finding. Path Traversal is now a partial static pack with filesystem sinks and observed normalization/containment controls; exploitability, automatic path repair, and closure remain unavailable.

- `backend/app/intake.py`: bounded UTF-8 source intake and artifact metadata.
- `backend/app/language_detection.py`: extension, shebang, and Tree-sitter syntax evidence with explicit conflict/unknown handling; only Python and JavaScript/JSX have parsers.
- `backend/app/parser_engine.py`: Tree-sitter structure, assignments, calls, and arguments.
- `backend/app/framework_intelligence.py`: evidence-backed Flask, Express, React, route, authentication, and authorization understanding.
- `backend/app/application_context.py`: dependencies, service instances, database-operation candidates, and security context without effectiveness claims.
- `backend/app/project_understanding.py`: project type, cross-file import resolution, unified graph with file-level application nodes, manifest declarations, and explicit ambiguous/unresolved relations.
- `backend/app/project_calls.py`: partial static Python cross-file call resolution for unique, top-level, unshadowed `from ... import ...` bindings, plus JavaScript named-import call resolution with explicit export evidence. Other calls and all cross-file data flow remain unresolved.
- `backend/app/javascript_bindings.py`: tree-sitter evidence for direct JavaScript named imports, direct calls in top-level functions, and exported target functions. Rebinding, shadowing, nested callers, syntax errors, and unsupported import forms remain unresolved.
- `frontend/src/pages/AnalysisProgressPage.jsx`: project ZIP results now display project type, file/import/route/call counts, observed frameworks, and up to eight statically evidenced cross-file calls with a clear non-exploitability caveat. Existing per-file presentation remains intact.
- Persisted analyses now navigate to `/analysis/progress/:analysisId`; refreshing that route loads the HMAC-verified, owner-scoped result through the existing read API. Non-persisted analyses still use navigation state and cannot be restored after refresh. Frontend build passed after this integration.
- The analyses list is real: `GET /api/v1/analyses` returns the latest 20 owner-scoped, HMAC-verified metadata summaries without source/result bodies. The `/projects` screen uses these records and opens saved results; its aggregate values are limited to those 20 records.
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
- `backend/app/archive_intake.py`: bounded ZIP intake with traversal, symlink, collision, depth, count, size, nested-archive, and compression-ratio defenses; safely reads a bounded set of dependency manifests.
- `backend/app/manifest_intelligence.py`: read-only `package.json`/`requirements.txt` declarations, exact-version versus unresolved-range distinctions; no package installation or SCA vulnerability claim.
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
4. Expand the narrowly verified Python and JavaScript cross-file call subsets only with equivalent evidence; do not claim repository-level data-flow traces yet. See `GOALS_1_TO_10_AUDIT.md` for objective-by-objective evidence and gaps.
5. Execute exploitability verification, then root-cause remediation, functional tests, replay, re-scan, re-trace, closure evidence, and updated-artifact download in that order.

## Deferred by design

- No uploaded-code execution or exploit testing because an approved isolation runtime is unavailable.
- ZIP project intake is supported. Direct folder, repository URL, and running-application intake remain unsupported.
- No vulnerability declaration, CWE/severity assignment, or verified-closed state.
- No job queue, sandbox runtime, external SAST/SCA sensor, or enabled AI call yet.
- No patch or updated download is exposed before verified exploitability and closure evidence.

## 2026-09-28 continuation: goals 8–9 and deployment gate

- Added bounded, opt-in OSV lookups for exact declared PyPI/npm versions; lookup results remain advisory matches with unverified installed version and reachability. Source code and manifest bodies are not sent. Default `OSV_ADVISORY_LOOKUP_ENABLED=false`.
- Added per-file and project-level hybrid evidence contracts that keep semantic rules, static traces, application context, code candidates, and dependency advisories separate. Candidate CWE/OWASP mapping is shown without vulnerability or severity claims. External SAST is still not integrated.
- Replaced the mock configuration screen with an authenticated API status view. It gives an explicit server-side location for `OPENAI_API_KEY`/`OPENAI_MODEL`, never accepts or echoes key values, and displays actual persistence and sensor states.
- Verification: 162 backend tests and frontend build pass. An exact-version live OSV lookup returned IDs; this does not prove exploitability.
- SMTP reality check: the local Hostinger mailbox credential and the newly supplied credential both returned SMTP authentication error 535. `backend/.env` is ignored; no password is tracked. OTP delivery is still blocked pending a valid mailbox credential.
- Hostinger account shows Business Web Hosting and an unconfigured VPS offer; `raqib.alaseeltech.com` remains the default page. Hostinger documents Flask/Python as VPS-only. See `HOSTINGER_DEPLOYMENT.md`; do not publish a standalone UI as though it were the working service.

## 2026-09-28 focused-scope continuation

- Read only the final five messages in the selected "تذكّر مشروع ستيب ون" chat. Their project decisions are distilled into `docs/FOCUSED_SCOPE.md`; the private transcript and unrelated chats are not published.
- First meaningful SQL pack in `backend/app/security_packs/sql_injection.py`: distinguishes observed input in query text from input only in later bound-parameter arguments. A safe bound-parameter path is retained as a non-candidate, not mislabeled SQL injection. Ambiguous `.execute` without SQL-shape evidence is unresolved.
- Five evaluation cases in `training/cases/sql_injection.json` cover unsafe, bound safe, unrelated methods (including a misleading SQL-named variable), and one-boundary safe data flow. This is an evaluation dataset, not model training.
- Replaced the mock report page with a report derived from an HMAC-verified, owner-scoped saved analysis. Three layers are executive, technical, and explicitly unavailable closure evidence. The result page now shows non-candidate reasons and stage statuses. JSON report export does not contain uploaded source code.
- Verified baseline: 167 backend tests, 2 frontend report tests, and production build pass. Run `npm test` in the frontend; CI now includes it.

## 2026-09-28 folder-structure clarification

- The final chat's proposed folder tree is recorded in `docs/PROJECT_STRUCTURE.md` with an explicit current-to-target map and implementation status. A proposed file or folder is not represented as implemented.
- Renamed the deterministic case dataset from `evaluation/` to `training/` to match the requested vocabulary. `training/README.md` explains that no model is being trained.
- Retain the current flat backend modules and established frontend directory until each domain move has focused tests. Do not create empty security pack, scenario, verification, or remediation implementations.

## 2026-09-28 focused workflow and product-clarity continuation

- Added a real `GET /api/v1/analysis/options` contract so the upload screen reads supported scopes, size limits, safety rules, and the five focused security-pack states from the backend instead of mock analysis options.
- Expanded security-pack metadata with explicit implementation order, understanding focus, and truthful exploitability/patch/closure capabilities.
- Upload UI now shows the actual safety contract, original-file preservation, evidence-gated claim policy, and current state of all five focused packs before analysis starts.
- Arabic/English preference is persisted locally; no security material is stored with it.
- Removed misleading demo identity/status text from the authenticated workspace shell.
- Configuration now exposes storage responsibility: owner-scoped append-only records, HMAC integrity, temporary uploaded-source workspaces, and no overwrite of originals.
- Hostinger SMTP host/port are documented in `backend/.env.example` without any mailbox password or secret value.
- Added `docs/REPOSITORY_MAP.md`, `docs/WORKFLOW_AND_STORAGE.md`, and `docs/REPORTING_MODEL.md` while retaining `docs/PROJECT_STRUCTURE.md`; the target tree and current implementation are kept distinct.
- Expanded `training/README.md` so vulnerable, safe, ambiguous, fixed, and regression cases are clearly separated from ML model training.
- No password or private chat transcript is stored in Git. Any credential previously typed into chat must be treated as exposed and replaced before production use.

## 2026-09-29 SMTP diagnosis

- Hostinger SMTP host/port/SSL, username, sender, and allowlisted recipient are present in the ignored local `backend/.env`. A login-only SMTP check still returns `535` (authentication refused), so the current blocker is the mailbox credential, not a missing hostname or IMAP setting. No test email or OTP was sent by this check.
- The frontend's `EMAIL_DELIVERY_UNAVAILABLE` text now describes failed delivery rather than falsely asserting missing configuration. The tracked environment example and default SMTP host match Hostinger; no secret was added to Git.

## 2026-09-29 sign-in and portfolio continuation

- Replaced OTP-on-every-visit with password sign-in after an email-verified first visit. Passwords are scrypt-hashed in an ignored local SQLite file, login attempts are throttled, and a seven-day signed session is restored across reloads. Email verification is still needed for first setup or a forgotten password. SMTP authentication remains blocked by Hostinger error 535, so real first-time enrollment is not yet operational.
- Login now has explicit visible labels and password/email-code tabs. Successful first verification goes to Account and security for password setup. Legacy mock signup/reset screens redirect to the real email-code flow.
- Added a dependency-free corporate portfolio under `public/portfolio/index.html`; `/` redirects there. Light/dark themes, smart header, responsive service cards, horizontal process steps, and honest feature states were checked in the local browser.
- Added a SQLite-backed catalog of five trusted synthetic SQL cases. Startup analyzes these versioned fixtures once, checks expected counts, and exposes only summary metadata through `GET /api/v1/examples`; user uploads are excluded. The local browser showed all five cases.
- Verification: 174 backend tests and the frontend production build passed before final commit. The portfolio works at `/portfolio/index.html`; the explicit filename avoids Vite's root SPA fallback.

## 2026-09-29 focused product UX continuation

- The first public screen now states the concrete input (.py/.js/.jsx/ZIP), static trace purpose, and evidence limit. The next sections show five focused packs with statuses fetched from `/api/v1/analysis/options`, accepted formats from that same contract, and nine workflow stages whose availability also comes from the backend. Duplicate text-heavy About/Services sections were removed; the existing hero/stepper/footer structure remains.
- Updated the existing New Analysis screen to prioritize Code File vs ZIP Project, a single file picker, pre-submit facts (name, size, scope, preliminary extension hint labeled as such), and one Start Analysis action. Backend parsing remains the authority for actual language and structure.
- Updated the real Analysis Result page with a compact project summary and direct candidate rows before collapsible technical evidence. Finding list/detail routes now read the owner-scoped HMAC-verified stored analysis, replacing the old mock finding data on those two routes. Their WHERE/WHY/TRACE/VERIFICATION/ROOT CAUSE/FIX/DIFF/TESTS/RE-VERIFY/EVIDENCE sections explicitly mark unavailable evidence.
- Browser QA: Chrome rendered the desktop and phone portfolio without horizontal page overflow, and displayed the correct live pack states, four accepted formats, nine stages, and five seeded examples. The frontend build, its two report tests, and 174 backend tests passed. Production startup now rejects `ANALYSIS_LOCAL_ONLY=true` so a reverse proxy cannot accidentally expose the development access path.

## 2026-09-29 compact visual continuation

- Shortened the public page without changing backend claims: a CSS code guardian illustrates Raqeeb standing over an application trace; shorter headline and copy, denser five-pack cards, prominent two-path upload, compact stepper, and evaluation examples collapsed behind a disclosure. The illustration is explicitly decorative rather than a live finding.
- Browser QA at desktop and narrow phone widths found no horizontal overflow; all five pack cards fit, four accepted formats and nine backend-status stages remain visible, and the five stored synthetic examples remain accessible on demand.
- Authentication safety: removing an address from `VERIFICATION_ALLOWED_EMAILS` now invalidates its existing signed session as well as password sign-in. This is covered by a regression test.

## 2026-09-30 authenticated workspace completion

- Rebuilt `/projects` as a concise dashboard using owner-scoped saved records: actual analysis/file/path/candidate counts, search, file/ZIP filter, direct result and structure navigation, and a useful zero-record state. The list API adds only derived count metadata from HMAC-verified records; no uploaded source is exposed in the list.
- Replaced the old mock `/projects/:id/workbench` with a real saved-evidence explorer. It shows analyzed files, extracted functions/imports/routes, observed paths, and candidate links. Raw uploaded source is intentionally not retained, so this screen does not pretend to be a code editor.
- Navigation now connects the result, structure, findings, and report pages for a saved analysis. Removed the unused mock data/endpoints, stale demo workbench components, and fake account name. Duplicate candidate IDs across distinct files now require a file path when opening details instead of silently selecting the wrong file.
- Tests: 175 backend tests, 4 frontend tests, and the frontend production build pass. The analysis-store list is covered for actual candidate/path counts and metadata-only output; finding lookup has a duplicate-ID regression test. Browser navigation was blocked by the app's browser URL policy during this continuation, so the authenticated dashboard layout has not been visually verified in a browser on this date.

## 2026-09-30 precision and reference repair continuation

- Corrected the SQL candidate gate: a static Python or JavaScript query string is not promoted to query-text influence merely because an input variable shares a word with that string. Dynamic interpolation remains a candidate. This is an assessment refinement, not proof that any database API binds parameters correctly.
- Added five trusted source fixtures across `.py`, `.js`, and `.jsx`: vulnerable/fixed SQLite-style lookup pairs in Python and JavaScript plus a JSX structure example. `backend/tests/test_reference_repairs.py` runs all five through the real analysis pipeline. The Python pair also gets in-memory SQLite functional and injection replay checks; the JavaScript pair is executed under Node with a recording database adapter. Uploaded source is never executed by these tests or the product.
- Added two JavaScript SQL evaluation records to the existing public example catalog. Startup now inserts missing versioned records while checking that previously saved rows still match their fixtures; it never clears the example database. The public examples endpoint has seven synthetic cases (two candidates) and still returns metadata only.
- Simplified the sign-in screen, made the first-use email-code route explicit, added password visibility with an accessible label, and corrected the generic error text. Password sign-in still requires an account previously established through email verification. Hostinger SMTP 535 remains the enrollment blocker until the mailbox credential is corrected.
- Verification after the catalog extension: 176 backend tests, 4 frontend tests, and frontend production build passed. Browser visual inspection was blocked by the app browser URL policy; do not claim it was visually checked. Arbitrary project repair, isolated execution, and verified closure remain unavailable.

## 2026-10-01 complete-checkout inventory and local demo access

- Inventoried all 5,039 local files (89,792,566 bytes at the scan time) with path, size, and SHA-256 in ignored `backend/instance/project_inventory_2026-10-01.json`; zero read errors. The checked-in source tree and honest goals 1–20 boundary are recorded in `docs/PROJECT_AUDIT_FULL.md`. This is a complete file inventory, not a claim that every dependency or generated file was semantically reviewed.
- Seeded the three user-requested demo addresses in the ignored local password database with scrypt hashes. Their short supplied passwords bypassed only the one-time local seed; the normal password-creation policy remains 12–128 characters with complexity checks. Added the addresses to the ignored local allowlist and set `ANALYSIS_LOCAL_ONLY=false`, so anonymous analysis APIs now return 401.
- Live HTTP checks: all three demo accounts signed in with independent sessions; a wrong password returned 401. A trusted Python SQL candidate, fixed JavaScript SQL example, and JSX example were uploaded under separate owners and persisted. Each account saw only its own new analysis; a cross-owner record read returned 403. These are local demo records, not verified vulnerability closure.
- Added the user-supplied transparent Raqeeb artwork to the existing public hero while retaining the code-trace composition and backend-driven support labels. Image response returned 200. Visual browser inspection remains unverified due the prior browser policy block.

## 2026-10-01 UI spacing and responsive refinement

- Updated only the two existing CSS files. The public hero has more breathing room; the five security focus cards use a 3/2/1-column responsive grid instead of five cramped desktop columns; upload formats, callout, process cards, and the optional example cards have larger readable spacing. The authenticated intake support cards use a 3/2/1-column grid, while the upload target, saved-results summary, findings, dashboard, and workbench have more space.
- No JSX, HTML, JavaScript, API, labels, buttons, or capabilities were removed. CSS parsed successfully; 176 backend tests, 4 frontend tests, frontend production build, and `git diff --check` passed. Local public page, CSS, image, login, and options API returned HTTP 200. Visual browser review remains unavailable under the browser tool policy and must not be claimed.

## 2026-10-01 Private evaluation and test persistence

- Added a private SQLite evaluation store separate from uploaded analyses. It persists seven inline SQL cases and five reference fixtures with immutable IDs, source hashes, honest static labels, expected/observed counts, and no closure claims. `backend/record_training_tests.py` records suite runs plus individual pytest/Node test outcomes, stores only output hashes, and exports the synthetic corpus to an ignored JSONL file. A new isolation test confirms uploaded source is absent from the corpus. Latest run: 180 backend tests, four frontend tests, and production build passed; 184 individual outcomes saved. This is future ML input, not a trained model.

## 2026-10-01 Proposal, demo sign-in, and optional mail sender

- Re-enabled only the three requested demo addresses in the ignored local email allowlist. Their existing scrypt-hashed passwords were verified through live HTTP password sign-in, all returning 200. Publicly documented demo addresses are rejected in production configuration and signed-session authorization. Do not copy the local credential database to production.
- Added `PROJECT_PROPOSAL_AR.md` with the 12 requested proposal elements and current-vs-planned boundaries. The README documents the demo sign-ins for local delivery.
- Added optional `POST /send` backed by Flask-Mail 0.10.0 and Gmail STARTTLS 587. It is disabled by default, requires an independent bearer token and recipient allowlist, reads `EMAIL_USER`/`EMAIL_PASS` from the ignored environment, and returns generic delivery errors. Hostinger OTP transport remains separate. Real Gmail delivery is unverified until a valid Gmail/Workspace sender credential and domain authentication are configured.
- Latest full check: 184 backend tests, four frontend tests, frontend production build, `pip check`, and local API/frontend HTTP checks passed. This includes a production guard test and mail endpoint unit tests; no live Gmail message was sent.
- Added `backend/seed_demo_accounts.py` so a fresh checkout can generate the three local demo accounts without publishing a credential database. It stores scrypt hashes, preserves existing matching accounts and other allowlist addresses, and refuses production. Focused seed tests and the latest complete run passed: 186 backend tests, four frontend tests, and the production build, with 190 individual outcomes from that run saved.

## 2026-10-01 controlled demo repair continuation

- The 1,459-line supplied fixture entered the real upload route as a static input. Earlier immutable records have three candidates, including a safe `shell=False` argument-list false positive. The current command assessment retains the unsafe shell-string candidate but marks the safe argument-list path `NON_SHELL_ARGUMENT_FLOW` with argument semantics unresolved. The new saved analysis `a51fbf76-6eee-4bbf-9a40-4373370eab52` has two candidates and two non-candidate paths.
- A scoped repair-proposal endpoint requires the exact original file and SHA-256, the same owner, and an existing finding ID. It generates only reviewed Python SQLite-ID and subprocess-shell call-shape proposals, never executes uploaded code, never overwrites the original, and returns a full updated file plus minimal diff. The patched file is syntax-checked and statically re-analyzed; the UI labels functional tests and runtime replay `NOT_RUN` and never claims verified closure.
- SQL and command proposals were obtained through the live endpoint; a combined private proposed file is at `backend/instance/demo_output/raqeeB_demo_5_vulnerabilities_550plus.proposed.py`. Its syntax is valid and the current static analyzer reports zero candidates and four non-candidate paths. This is **not** proof of functional safety: command portability on Windows is unresolved.
- Seven inline SQL cases plus seven small reference fixtures sync at startup. The explicit `backend/record_training_tests.py` run additionally evaluated the controlled large fixture, giving 15 immutable trusted cases in the ignored SQLite database. This is deterministic evaluation data, not trained model weights. Its latest run saved all 207 backend test outcomes, four frontend outcomes, and a successful production build. Uploaded customer source is not copied into the corpus.

## 2026-10-01 end-to-end priority and isolation gap

- Priority is now one deep SQL Injection lifecycle before adding vulnerability classes. Current upload, parsing, application context, source/sink trace, static candidate, HMAC-protected analysis record, narrow patch proposal, static re-scan, and static re-trace are real. The proposal response now includes the observed post-patch non-candidate path and its assessment, not just a zero count.
- No reviewed runtime executor exists in this checkout or on the current host. `AnalysisWorkspace` is a temporary filesystem directory, not a process sandbox. Docker/Podman were unavailable; WSL has no installed distribution. Setting `ISOLATION_RUNTIME_AVAILABLE=true` therefore cannot make a plan ready: the runtime capability gate fails closed and the configuration API reports unavailable.
- Uploaded code is never run. Exploitability proof, original-project functional tests, same-scenario runtime replay, runtime re-trace, and VERIFIED_CLOSED remain NOT_AVAILABLE. The trusted checked-in SQLite fixture has a real local regression test, but it is not evidence that an arbitrary uploaded project was isolated and verified. Do not promote that fixture result into a user finding's closure state.
- The large controlled fixture now has a real upload → persisted SQL candidate → same-owner exact-file repair proposal → static re-scan → static re-trace regression test. Latest full run: 208 backend tests, four frontend tests, and production build passed; 15 trusted evaluation cases remain in the private store.

## 2026-10-02 SQL lifecycle evidence continuation

- Runtime capability matrix on this Windows host: Docker NOT AVAILABLE; Podman NOT AVAILABLE; WSL2 installed as a feature but no runnable distribution; Windows Sandbox feature disabled; Hyper-V feature disabled. No customer-code isolation is available. No tools or Windows features were installed or changed.
- A small `RuntimeVerifier` contract retains an unavailable implementation. Configuration alone cannot turn runtime verification on. Uploaded customer code is never executed.
- SQL repair proposals now carry structured, evidence-linked root cause, timestamp, analyzer schema version, original/patched hashes, diff, static re-scan, static re-trace, functional evidence, and computed closure gates. Append-only HMAC-protected repair evidence is stored beside the existing immutable analysis record without storing the full patched source; owner-scoped GET retrieves it after reload.
- For the pinned SHA-256 of the checked-in 1,459-line synthetic fixture only, a benign existing-ID functional check compiles only the reviewed SQL function, uses a temporary SQLite database and Flask request context, and compares the actual returned row before and after the exact two-line patch. This is trusted fixture functionality evidence, not a sandbox, exploit replay, or proof about arbitrary uploaded projects.
- The closure evaluator reports `CLOSURE_INCOMPLETE`: runtime verification before patch and same-scenario replay after patch are `NOT_AVAILABLE`. A static zero count, valid syntax, trusted normal-input PASS, or client-supplied `verified_closed=true` cannot promote a finding to `VERIFIED_CLOSED`.
- The same saved analysis `a51fbf76-6eee-4bbf-9a40-4373370eab52` now has a persisted SQL repair-evidence record. Browser reload recovered structured root cause, diff, trusted functional PASS, static recheck/retrace, and closure gates from the owner-scoped API. Full checks after this change: 212 backend tests, four frontend tests, production build; the uploaded source remained untouched.

## 2026-10-02 lifecycle artifact and isolation correction

- The earlier trusted-fixture functional execution was removed from the production repair path because it ran selected Python on the host. Repair now reports functional verification and replay as `NOT_AVAILABLE` until a reviewed isolated executor exists.
- Patched artifacts are stored separately from originals, encrypted with AES-GCM, bound to owner/finding/SHA-256, integrity-checked when read, and downloadable through the owner-scoped lifecycle endpoint. Security reports contain lifecycle evidence without embedding the patched source.
- Finding Detail reads its lifecycle states from that backend endpoint. Static re-scan and re-trace can pass from persisted analyzer evidence, while runtime verification, functional testing, replay, and verified closure remain unavailable. Final checks: 217 backend tests, four frontend tests, and production build passed.

## 2026-10-03 five-pack and isolated lifecycle continuation

- Added a fail-closed OCI verifier for reviewed single-file Python SQL/command shapes. It requires Docker/Podman plus a preinstalled digest-pinned image and enforces no network, no capabilities, no new privileges, non-root identity, read-only root/input, tmpfs scratch, and CPU/memory/process/time limits. Docker Desktop 29.8.1 is now installed on the prepared Windows host, and `python@sha256:0687a6bc9716edc2a6ee0fbfb0f87e7ee358b262b67c9215de91bc9b2d38ba71` is installed and configured locally.
- Added exact-original verification API, append-only HMAC-protected runtime evidence, closure records, and frontend controls. Closure is derived only from runtime-before, functional smoke, replay-after, static re-scan, and static re-trace. Customer-derived closure records explicitly remain ineligible for training without consent.
- Added a narrow Path Traversal patch for one reviewed `Path` join plus `open` shape. Added real partial XSS and IDOR packs with safe encoding/sanitization and terminating ownership-guard counterexamples. The controlled large fixture now yields five real static candidates and five real non-candidate paths.
- Real API-level controlled SQL Injection and Command Injection fixtures each completed upload, candidate, encrypted patch copy, isolated runtime-before proof, target-function smoke test, replay-after, static re-scan, static re-trace, signed closure record, patched download, and report download. Both reached `VERIFIED_CLOSED`; both closure records remain `training_eligible=false`.
- Final recorded verification: 260 backend tests passed, five frontend tests passed, and the production build passed. The private evaluation database stores the run evidence; no uploaded customer source was added to its corpus.
