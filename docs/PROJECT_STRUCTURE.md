# Raqeeb project structure

This is the folder plan from the final folder-structure discussion in the selected project chat. It is a **target map**, not a claim that every module already exists. The repository uses its current paths until a small, tested move has a functional reason. Do not create empty implementation files to make the tree appear complete.

## Target ownership map

```text
raqib-secure-code/
├── backend/
│   ├── app/
│   │   ├── intake/                  # safe file/ZIP intake, workspace policy
│   │   ├── language/                # detection, registry, Python/JS adapters
│   │   ├── understanding/           # parser, symbols, calls, routes, framework, application graph
│   │   ├── dataflow/                # sources, sinks, controls, intra/inter-function and cross-file flow
│   │   ├── security_packs/
│   │   │   ├── sql_injection/       # rules, semantics, verifier, remediation, evidence
│   │   │   ├── command_injection/
│   │   │   ├── path_traversal/
│   │   │   ├── xss/
│   │   │   └── broken_authorization/
│   │   ├── verification/            # reachability, preconditions, isolated replay
│   │   ├── remediation/             # root cause, minimal patch, diff policy
│   │   ├── validation/              # syntax/build/functional tests, re-scan, re-trace
│   │   ├── ai/                      # advisory context, schema and policy; never closure verdict
│   │   ├── evidence/                # before/after snapshots, integrity, closure gates
│   │   ├── reports/                 # finding, project and closure reports, export
│   │   ├── storage/                 # analyses, artifacts, evidence and retention
│   │   ├── api/                     # analysis, findings, verification, repair, reports, config
│   │   └── auth/                    # sessions, authorization, email verification
│   ├── tests/                       # unit, integration, security and regression tests
│   └── run.py
├── frontend/src/                   # pages, components, api, i18n, styles
├── scenarios/                      # isolated end-to-end vulnerable/safe case projects
│   ├── sql_injection/
│   ├── command_injection/
│   ├── path_traversal/
│   ├── xss/
│   └── broken_authorization/
├── training/                       # knowledge/evaluation cases, NOT model training
│   ├── cases/
│   ├── expected_results/
│   ├── false_positives/
│   ├── fixed_versions/
│   └── regression_cases/
├── docs/                           # architecture, security rules, reports, deployment
└── .github/workflows/
```

The tree mirrors responsibility boundaries. A security pack becomes a package such as `sql_injection/rules.py`, `semantics.py`, `verifier.py`, `remediation.py`, and `evidence.py` **only as those behaviors are implemented and tested**. The sequence is SQL injection → command injection → path traversal → XSS → broken authorization/IDOR. This is an implementation sequence, not a severity order.

## What exists today

| Responsibility | Current path | State |
| --- | --- | --- |
| Safe intake | `backend/app/intake.py`, `archive_intake.py`, `workspace.py` | Implemented within documented limits |
| Language and frameworks | `language_detection.py`, `parser_engine.py`, `framework_intelligence.py`, `manifest_intelligence.py` | Python/JavaScript subsets; no general language support claim |
| Application understanding | `application_model.py`, `application_context.py`, `project_understanding.py`, `project_calls.py`, `relationship_model.py` | Partial, evidence-scoped |
| Data flow and semantics | `data_flow.py`, `interprocedural_flow.py`, `security_semantics.py` | Partial; general cross-file taint flow unresolved |
| SQL pack | `backend/app/security_packs/sql_injection.py`, `registry.py` | Static candidate assessment only |
| Other four packs | Registry statuses in `backend/app/security_packs/registry.py` | Command: partial source/sink trace; path/XSS/IDOR: not implemented as packs |
| Verification/repair | `verification_planner.py`, `finding_lifecycle.py` | Planning/status only; no exploit replay, patch or closure engine |
| AI advisor | `codex_advisor.py` | Optional advisory configuration; never security truth |
| Analysis storage | `analysis_store.py` | Owner-scoped saved analyses with integrity protection |
| API/auth | `routes.py`, `archive_routes.py`, `auth.py`, `email_verification.py`, `email_verification_routes.py` | Working subsets; real OTP depends on valid SMTP configuration |
| UI | `step-one-secure-code-ai-agent-frontend-professional/src/` | Existing frontend baseline; report uses persisted analysis, while some older pages still contain demo data |
| Case dataset | `training/cases/`, `training/fixtures/`, `backend/app/training_store.py` | Twelve trusted synthetic cases in private SQLite; individual test results recorded; no ML training |
| Scenario projects | `scenarios/` | Planned; no executable sandbox or end-to-end case project yet |
| Report layers | `step-one-secure-code-ai-agent-frontend-professional/src/report/buildReport.js`, `src/pages/ReportPage.jsx` | Executive + technical + explicit `NOT_AVAILABLE` closure layer |

The current frontend directory keeps its existing name. Renaming it to `frontend/` is a separate migration that must preserve imports, build, routes, and deployment references. Backend modules likewise move by domain only with import and API regression tests.

## Case and workspace contracts

A scenario folder, when implemented, should own a minimal `vulnerable/` project, expected trace and root-cause data, a minimal `fixed/` version, and a replay test. It must include safe, ambiguous, cross-function, cross-file and false-positive cases where the pack supports them. A case may say `UNRESOLVED`; expected outputs must not assert an exploit that was never replayed.

`training/` holds test knowledge and expected results. It is **not** a trained model. A fuller case contract includes vulnerable code, expected source/sink/trace/guard/status/root cause/fix/replay result; today the SQL JSON records source and expected candidate/non-candidate counts only. Missing fields remain planned, not fabricated.

For each analysis, the intended artifact roles are `original/`, `working/`, `patched/`, `tests/`, `verification/`, `evidence/`, and `report/`. These are logical roles, not current on-disk promises. Preserve the original artifact; a future download must distinguish `_original` from `_security_fixed` and exist only after a verified patch. Never publish user uploads, local analysis stores, email credentials, API keys, or private chat text to the public repository.

## User-visible order and report truth

Upload → safe intake → understand → trace → security candidate → verify → root-cause fix → functional tests → replay → re-scan → re-trace → closure evidence → report/download. A finding view should answer **where, why, trace, exploitability, root cause, fix, tests, re-verification, evidence** in that order. A real patch view must show Before / Diff / After, changed-file and changed-line counts, and preserved original. The current UI may show only stages backed by actual records; unimplemented stages show unavailable or unresolved.

Reports have three layers: executive scope and counts; technical source/sink/trace/context; and closure evidence containing original and patched hashes, verification, diff, functional tests, replay, re-scan and re-trace. The third layer is currently unavailable. Use candidate/orange, unproven/gray, informational/blue, verified exploitable/red, and verified closed/green consistently. Green requires actual evidence gates; an AI suggestion alone never changes closure state.
