# Raqeeb complete project inventory and honest status

Status: 2026-10-01. Source root: the repository checkout containing this file.

The private full-file inventory is `backend/instance/project_inventory_2026-10-01.json` on the owner's laptop. It records relative path, byte count, and SHA-256 for every local file (including ignored dependencies and local configuration), without embedding file contents. It is intentionally ignored by Git because local configuration and dependency trees are not public source. The inventory was generated from 5,039 readable files, 89,792,566 bytes, with zero read errors; regenerate after edits for current hashes.

## What actually works

- Python, JavaScript, JSX, and ZIP intake; bounded static parsing and project structure. Uploaded code is never executed.
- Routes, imports, calls, source/sink observations, narrow static traces, and candidate findings. Unknown relationships stay unresolved.
- SQL Injection, Command Injection, and Path Traversal have partial static analysis. XSS and IDOR packs are not implemented.
- Authenticated, owner-scoped saved analyses with HMAC integrity. Three requested demo accounts are seeded only in the ignored local password database, not in public source.
- Narrow Python SQLite and subprocess findings can produce a separate encrypted patched artifact with SHA-256, static re-scan/re-trace, and owner-scoped downloads. Uploaded code is not executed on the host; runtime verification, functional execution, replay, and verified closure remain unavailable without reviewed isolation.
- The supplied Raqeeb artwork is used in the existing public hero; the live format and pack labels still come from the backend.

## Verification boundary for goals 1–20

| Goals | State | Evidence boundary |
| --- | --- | --- |
| 1–7: intake, language, project understanding, parsing, graph | Partial | Bounded source/ZIP tests, Flask/FastAPI/Django/Express/React evidence, structure tests, resolved imports/calls, and one-boundary cross-file flow; no completeness claim. |
| 8–14: sources, sinks, flow, context, hybrid analysis, standards | Partial | Static observations/candidates and explicit unresolved states. |
| 15: runtime reachability/exploitability | Not available | Uploaded projects are never run in an isolation runtime. |
| 16: root cause | Candidate only | Hypotheses are not validated root-cause proof. |
| 17–19: patch, functional test, replay, re-scan/re-trace | Partial | Narrow Python patches and static re-scan/re-trace work; functional execution and replay require isolation. |
| 20: closure evidence and updated project download | Partial | Patched files and security reports are downloadable; closure remains incomplete without runtime gates. |

## Source tree: every Git-tracked file and this new asset

147 source/repository entries: .github 1, .gitignore 1, GOALS_1_TO_10_AUDIT.md 1, HOSTINGER_DEPLOYMENT.md 1, PROJECT_CONTEXT.md 1, README.md 1, backend 75, docs 6, step-one-secure-code-ai-agent-frontend-professional 53, training 7.

```text
.github/workflows/ci.yml
.gitignore
GOALS_1_TO_10_AUDIT.md
HOSTINGER_DEPLOYMENT.md
PROJECT_CONTEXT.md
README.md
backend/.env.example
backend/app/__init__.py
backend/app/analysis_service.py
backend/app/analysis_store.py
backend/app/api_errors.py
backend/app/application_context.py
backend/app/application_model.py
backend/app/archive_intake.py
backend/app/archive_routes.py
backend/app/archive_service.py
backend/app/auth.py
backend/app/codex_advisor.py
backend/app/control_flow.py
backend/app/data_flow.py
backend/app/dependency_advisories.py
backend/app/email_verification.py
backend/app/email_verification_routes.py
backend/app/example_catalog.py
backend/app/finding_lifecycle.py
backend/app/finding_model.py
backend/app/framework_intelligence.py
backend/app/http_security.py
backend/app/hybrid_security.py
backend/app/intake.py
backend/app/interprocedural_flow.py
backend/app/javascript_bindings.py
backend/app/language_detection.py
backend/app/manifest_intelligence.py
backend/app/parser_engine.py
backend/app/password_auth.py
backend/app/pipeline_state.py
backend/app/project_calls.py
backend/app/project_understanding.py
backend/app/relationship_model.py
backend/app/routes.py
backend/app/security_packs/__init__.py
backend/app/security_packs/registry.py
backend/app/security_packs/sql_injection.py
backend/app/security_semantics.py
backend/app/test_intake.py
backend/app/verification_planner.py
backend/app/workspace.py
backend/config.py
backend/requirements.txt
backend/run.py
backend/tests/test_analysis_api.py
backend/tests/test_analysis_store.py
backend/tests/test_application_context.py
backend/tests/test_application_model.py
backend/tests/test_archive_api.py
backend/tests/test_archive_intake.py
backend/tests/test_codex_advisor.py
backend/tests/test_configuration_status.py
backend/tests/test_cors.py
backend/tests/test_data_flow.py
backend/tests/test_dependency_advisories.py
backend/tests/test_email_verification.py
backend/tests/test_example_catalog.py
backend/tests/test_finding_lifecycle.py
backend/tests/test_finding_model.py
backend/tests/test_framework_intelligence.py
backend/tests/test_health.py
backend/tests/test_hybrid_security.py
backend/tests/test_interprocedural_flow.py
backend/tests/test_language_detection.py
backend/tests/test_manifest_intelligence.py
backend/tests/test_parser_engine.py
backend/tests/test_password_auth.py
backend/tests/test_pipeline_state.py
backend/tests/test_project_understanding.py
backend/tests/test_reference_repairs.py
backend/tests/test_relationship_model.py
backend/tests/test_security_semantics.py
backend/tests/test_sql_evaluation_cases.py
backend/tests/test_verification_planner.py
docs/FOCUSED_SCOPE.md
docs/PROJECT_AUDIT_FULL.md
docs/PROJECT_STRUCTURE.md
docs/REPORTING_MODEL.md
docs/REPOSITORY_MAP.md
docs/WORKFLOW_AND_STORAGE.md
step-one-secure-code-ai-agent-frontend-professional/.env.example
step-one-secure-code-ai-agent-frontend-professional/FRONTEND_DELIVERY.md
step-one-secure-code-ai-agent-frontend-professional/README.md
step-one-secure-code-ai-agent-frontend-professional/index.html
step-one-secure-code-ai-agent-frontend-professional/package-lock.json
step-one-secure-code-ai-agent-frontend-professional/package.json
step-one-secure-code-ai-agent-frontend-professional/public/portfolio/app.js
step-one-secure-code-ai-agent-frontend-professional/public/portfolio/index.html
step-one-secure-code-ai-agent-frontend-professional/public/portfolio/raqib-guardian.png
step-one-secure-code-ai-agent-frontend-professional/public/portfolio/styles.css
step-one-secure-code-ai-agent-frontend-professional/src/App.jsx
step-one-secure-code-ai-agent-frontend-professional/src/api/client.js
step-one-secure-code-ai-agent-frontend-professional/src/api/endpoints.js
step-one-secure-code-ai-agent-frontend-professional/src/assets/raqib-logo.png
step-one-secure-code-ai-agent-frontend-professional/src/auth.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/AppShell.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/AsyncState.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/AuthLayout.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/Icon.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/OtpInput.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/ProtectedRoute.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/PublicHeader.jsx
step-one-secure-code-ai-agent-frontend-professional/src/components/StatusBadge.jsx
step-one-secure-code-ai-agent-frontend-professional/src/hooks/useAsyncResource.js
step-one-secure-code-ai-agent-frontend-professional/src/i18n.jsx
step-one-secure-code-ai-agent-frontend-professional/src/main.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/AccountPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/AnalysisProgressPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/ConfigurationPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/CreateAccountPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/FindingDetailPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/FindingsPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/ForgotPasswordPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/HowItWorksPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/LandingPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/LoginPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/NewAnalysisPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/ProjectsPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/ReportPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/ResetPasswordPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/SecurityTrustPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/SystemStatePage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/TwoFactorPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/VerifyEmailPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/pages/WorkbenchPage.jsx
step-one-secure-code-ai-agent-frontend-professional/src/report/buildReport.js
step-one-secure-code-ai-agent-frontend-professional/src/report/buildReport.test.js
step-one-secure-code-ai-agent-frontend-professional/src/routes.jsx
step-one-secure-code-ai-agent-frontend-professional/src/styles.css
step-one-secure-code-ai-agent-frontend-professional/src/utils/fileDownload.js
step-one-secure-code-ai-agent-frontend-professional/src/workspace/locateFinding.js
step-one-secure-code-ai-agent-frontend-professional/src/workspace/locateFinding.test.js
step-one-secure-code-ai-agent-frontend-professional/vite.config.js
training/README.md
training/cases/sql_injection.json
training/fixtures/javascript/UserLabel.jsx
training/fixtures/javascript/sql_lookup_fixed.js
training/fixtures/javascript/sql_lookup_unsafe.js
training/fixtures/python/sql_lookup_fixed.py
training/fixtures/python/sql_lookup_unsafe.py
```

Local-only items such as `.env`, SQLite databases, `.venv`, `node_modules`, caches, and `.git` are represented in the private full-file inventory. They are not committed or distributed as application source.
