# Raqeeb repository map

This map preserves the current working code while making the product structure explicit. Files are moved only when a refactor is justified by tests; no information is discarded for appearance alone.

## Runtime code

- `backend/app/intake.py`, `archive_intake.py`, `workspace.py`: safe bounded intake and temporary workspace handling.
- `backend/app/language_detection.py`, `parser_engine.py`: language evidence and syntax structure.
- `backend/app/application_*.py`, `framework_intelligence.py`, `project_understanding.py`: application understanding.
- `backend/app/relationship_model.py`, `project_calls.py`, `data_flow.py`, `interprocedural_flow.py`: relationships and trace evidence.
- `backend/app/security_semantics.py`: source, sink, and control observations.
- `backend/app/security_packs/`: focused vulnerability-specific reasoning.
- `backend/app/verification_planner.py`, `finding_lifecycle.py`, `pipeline_state.py`: verification and closure gates.
- `backend/app/codex_advisor.py`: AI advisory only; never closure authority.
- `backend/app/analysis_store.py`: owner-scoped append-only analysis records with HMAC-SHA256 integrity.
- `backend/app/routes.py`, `archive_routes.py`: versioned API.
- `step-one-secure-code-ai-agent-frontend-professional/src/pages/`: user workflow and reports.
- `step-one-secure-code-ai-agent-frontend-professional/src/report/`: report assembly from stored evidence.

## Focused security packs

1. SQL Injection
2. Command Injection
3. Path Traversal
4. Cross-Site Scripting
5. Broken Authorization / IDOR

Each pack progresses through:

`rules/semantics -> candidate evidence -> verification -> root cause -> minimal patch -> functional tests -> replay -> re-scan -> re-trace -> closure evidence`

A pack is not called complete until the required gates exist and pass.

## Evaluation and training material

`evaluation/` is the deterministic product-evaluation area. It is not ML model training. Each security pack should contain:

- vulnerable cases,
- safe counterexamples,
- ambiguous/unresolved cases,
- fixed versions,
- regression expectations.

## Reports

The product exposes three report layers:

1. Executive summary.
2. Technical evidence report.
3. Evidence-of-closure report.

Until runtime verification and patch validation are implemented, closure remains `NOT_AVAILABLE`.

## Storage responsibilities

- Uploaded code is never executed during static intake.
- Project workspaces are temporary and bounded.
- Original uploads are never overwritten.
- Persisted analysis records are owner-scoped and integrity checked.
- Secrets live only in server environment/secret storage, never in the frontend or Git.
