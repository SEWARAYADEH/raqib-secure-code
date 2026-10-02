# Focused security verification scope

Decision captured 2026-09-28 from the final five messages of the user-selected "تذكّر مشروع ستيب ون" conversation. This file preserves the product decisions without publishing the private chat transcript or credentials. The target is application understanding, verification, minimal repair, functional tests, replay, re-scan, re-trace, and evidence of closure—not a catalogue of SAST alerts.

## Five security packs

Implementation order is technical progression, not severity ranking:

1. **SQL injection:** HTTP input → variables/functions → query construction → SQL sink → parameter binding. Current status: bounded static candidates, a reviewed narrow Python SQLite patch, encrypted patched-artifact persistence, static re-scan/re-trace, and owner-scoped downloads. Runtime verification, functional execution, and replay are unavailable without isolation.
2. **Command injection:** input → command construction → shell/process sink → allowlist and shell-mode context. Current status: bounded static candidates and a reviewed narrow Python subprocess argument-list patch with static re-scan/re-trace. Runtime verification, functional execution, and replay are unavailable without isolation.
3. **Path traversal:** input path → normalization/join → filesystem operation → allowed root. Current status: partial static candidates for supported Python/JavaScript filesystem calls, with normalization and terminating containment guards retained as non-candidate observations. Runtime verification, automatic repair, replay, and closure are unavailable.
4. **XSS:** input → transformations → HTML/JavaScript sink → context-appropriate encoding. Current status: planned; no pack implementation or claim.
5. **IDOR/broken authorization:** route → actor → resource ID → ownership/role guard → resource access. Current status: planned; no pack implementation or claim.

Packs are added only when their rules, counterexamples, and tests exist. Empty module directories are not created. `backend/app/security_packs/sql_injection.py` is the first implemented pack; `training/cases/sql_injection.json` is a regression dataset, not machine-learning model training. The requested folder map and current-to-target mapping are in `docs/PROJECT_STRUCTURE.md`.

## User-visible workflow

Upload → intake → understand → trace → classify observations/candidates → verify → fix → functional tests → replay → re-scan → re-trace → closure evidence → report/download. Each stage must show its actual status; unavailable stages remain blocked. A candidate is not a verified vulnerability. Green "VERIFIED CLOSED" is reserved for completed evidence gates.

The saved analysis screen shows metrics, trace, non-candidate reasons, and backend-owned lifecycle states. Supported single-file findings can produce an encrypted patched copy and downloadable security report without overwriting the original. A proposed patch is not a verified fix; closure remains `CLOSURE_INCOMPLETE` while runtime, functional, or replay gates are unavailable.

## Evaluation rule

Each pack needs deliberately unsafe, safe, ambiguous, and regression cases before expanding detection. SQL's first cases include dynamic query concatenation, bound parameters, an unrelated `.execute` method, and a bound parameter passed across one function boundary. The goal is to reduce unsupported claims, not optimize a benchmark count.
