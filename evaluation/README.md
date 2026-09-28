# Raqeeb evaluation cases

This directory is the product's deterministic security-evaluation area. It is **not** machine-learning model training data and must never be presented as such.

## Purpose

Every security pack must be tested against:

- deliberately vulnerable cases,
- safe counterexamples,
- ambiguous or unresolved cases,
- fixed versions,
- regression cases that previously failed.

The objective is not to maximize finding count. The objective is to prove that Raqeeb can distinguish supported evidence from uncertainty and avoid promoting a dangerous method name or pattern into a vulnerability claim by itself.

## Current pack coverage

1. SQL Injection — implemented at bounded static-candidate level.
2. Command Injection — partial static candidate coverage.
3. Path Traversal — planned.
4. XSS — planned.
5. Broken Authorization / IDOR — planned.

See `docs/FOCUSED_SCOPE.md` for the exact product boundary.

## Case contract

A case should record:

- stable case ID,
- language/file name,
- source fixture or fixture reference,
- expected candidate count,
- expected non-candidate/unresolved count,
- expected pack status,
- expected verification state,
- optional expected trace facts.

Runtime exploit verification is not performed from this directory until the disposable isolation runtime exists.

The current SQL cases live in `evaluation/cases/sql_injection.json`.
