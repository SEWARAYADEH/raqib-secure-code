# Raqeeb training / evaluation cases

"Training" here means a **knowledge and deterministic evaluation dataset for Raqeeb**, not machine-learning model training. No model is trained from this directory.

## Required case types

Every security pack should accumulate:

- deliberately vulnerable cases,
- safe counterexamples,
- ambiguous or unresolved cases,
- fixed versions,
- regression cases that previously failed,
- cross-function and cross-file cases when the engine supports those relationships.

The objective is not to maximize finding count. The objective is to prove that Raqeeb can distinguish supported evidence from uncertainty and avoid promoting a dangerous method name or pattern into a vulnerability claim by itself.

## Current focused packs

1. SQL Injection — bounded static-candidate assessment implemented.
2. Command Injection — partial static source/sink candidate coverage.
3. Path Traversal — planned.
4. XSS — planned.
5. Broken Authorization / IDOR — planned.

See `docs/FOCUSED_SCOPE.md` and `docs/PROJECT_STRUCTURE.md`.

## Current case contract

A deterministic case should record:

- stable case ID,
- language/file name,
- source fixture or fixture reference,
- expected candidate count,
- expected non-candidate or unresolved count,
- expected pack status,
- expected verification state,
- optional expected trace facts.

Runtime exploit verification is not performed from `training/` until an approved disposable isolation runtime exists.

The current SQL dataset lives in `training/cases/sql_injection.json` and includes unsafe, safe bound-parameter, unrelated-method, misleading-name, and one-boundary safe cases.
