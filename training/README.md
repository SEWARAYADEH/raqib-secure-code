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

The current SQL dataset lives in `training/cases/sql_injection.json` and includes Python and JavaScript unsafe/bound-parameter cases, unrelated-method and misleading-name counterexamples, and a cross-function safe case. New versioned cases are added to the persisted public example catalog without replacing existing records.

## Executable reference repairs

`training/fixtures/` contains checked-in Python, JavaScript, and JSX examples. `backend/tests/test_reference_repairs.py` sends each file through the real intake, parser, trace, and finding pipeline. The Python SQLite pair is also executed against an in-memory database: ordinary lookup remains functional, a known injected lookup succeeds before the fix and fails afterward, and the fixed file is re-analyzed. The JavaScript pair runs under Node with a recording database adapter to verify that the input remains a parameter instead of becoming query text. The JSX fixture checks language and structural parsing only.

These are **trusted test fixtures**, not uploaded source. The backend never executes user uploads. The JavaScript recording adapter proves the call arguments, not the behavior of every SQL driver. These reference tests do not change pack status or close findings in arbitrary projects; those require project-specific functional tests, replay, re-scan, re-trace, and evidence in an isolated runtime.
