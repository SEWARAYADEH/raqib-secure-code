# Focused security verification scope

Decision captured 2026-09-28 from the final five messages of the user-selected "تذكّر مشروع ستيب ون" conversation. This file preserves the product decisions without publishing the private chat transcript or credentials. The target is application understanding, verification, minimal repair, functional tests, replay, re-scan, re-trace, and evidence of closure—not a catalogue of SAST alerts.

## Five security packs

Implementation order is technical progression, not severity ranking:

1. **SQL injection:** HTTP input → variables/functions → query construction → SQL sink → parameter binding. Current status: bounded static candidates, reviewed Python SQLite patches, encrypted artifacts, static re-scan/re-trace, and optional isolated before/replay verification for reviewed single-file shapes.
2. **Command injection:** input → command construction → shell/process sink → argument-list and shell-mode context. Current status: bounded static candidates, a reviewed Python subprocess patch, static re-scan/re-trace, and the same optional isolated evidence gates.
3. **Path traversal:** input path → normalization/join → filesystem operation → allowed root. Current status: partial static candidates, normalization/containment counterexamples, and a narrow Python `Path` plus `open` patch. Runtime replay remains unsupported.
4. **XSS:** input → transformations → HTML/JavaScript sink → output encoding/sanitization. Current status: partial static candidates for supported Python raw-template and JavaScript HTML/DOM calls; observed encoding/sanitization is retained as an unverified non-candidate. Rendering context and runtime exploitability remain unresolved.
5. **IDOR/broken authorization:** route → resource ID → ownership/role guard → object access. Current status: partial static candidates for supported ORM/resource-map lookups plus terminating ownership-guard counterexamples. Actor identity, policy correctness, runtime exploitability, and repair remain unresolved.

Packs are added only when their rules, counterexamples, and tests exist. Empty module directories are not created. `backend/app/security_packs/sql_injection.py` is the first implemented pack; `training/cases/sql_injection.json` is a regression dataset, not machine-learning model training. The requested folder map and current-to-target mapping are in `docs/PROJECT_STRUCTURE.md`.

## User-visible workflow

Upload → intake → understand → trace → classify observations/candidates → verify → fix → functional tests → replay → re-scan → re-trace → closure evidence → report/download. Each stage must show its actual status; unavailable stages remain blocked. A candidate is not a verified vulnerability. Green "VERIFIED CLOSED" is reserved for completed evidence gates.

The saved analysis screen shows metrics, trace, non-candidate reasons, and backend-owned lifecycle states. Supported single-file findings can produce an encrypted patched copy and downloadable security report without overwriting the original. The prepared development host now has a tested Docker engine and digest-pinned Python image, so reviewed SQL/command shapes can persist isolated runtime-before, smoke-test, replay-after, re-scan, re-trace, and closure evidence. Unsupported shapes still remain `CLOSURE_INCOMPLETE`.

## Evaluation rule

Each pack needs deliberately unsafe, safe, ambiguous, and regression cases before expanding detection. SQL's first cases include dynamic query concatenation, bound parameters, an unrelated `.execute` method, and a bound parameter passed across one function boundary. The goal is to reduce unsupported claims, not optimize a benchmark count.
