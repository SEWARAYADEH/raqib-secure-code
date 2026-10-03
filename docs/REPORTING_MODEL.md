# Reporting model

Raqeeb reports must distinguish observation, candidate, verified exploitability, remediation, and closure.

Project reports also include cross-file findings only when the stored evidence uniquely resolves the import binding, caller, argument position, callee parameter, and sensitive sink. These findings are project-scoped; patch, runtime, and closure remain unavailable unless their independent evidence gates exist.

## Executive report

Shows:
- artifact/project identity,
- languages/frameworks,
- analyzed files,
- focused security-pack coverage,
- candidate count,
- verified-exploitable count,
- verified-closed count,
- unresolved risks and blockers.

## Technical report

For each candidate:
- finding ID,
- file/function/line,
- source,
- sink,
- trace,
- security context and observed controls,
- candidate CWE/OWASP mapping,
- static reachability,
- exploitability status,
- root-cause status,
- patch status,
- test status.

## Evidence-of-closure report

Required before `VERIFIED_CLOSED`:
- original artifact SHA-256,
- before trace,
- exploitability/replay evidence,
- root cause,
- exact patch diff,
- patched artifact SHA-256,
- functional test result,
- replay result,
- re-scan result,
- re-trace result,
- final closure decision.

## Status vocabulary

- `OBSERVED`: evidence exists.
- `CANDIDATE`: security issue candidate, not verified.
- `UNRESOLVED`: evidence is insufficient.
- `NOT_PROVEN`: attempted reasoning/testing did not prove exploitability.
- `VERIFIED_EXPLOITABLE`: approved verification established exploitability.
- `PATCH_REJECTED`: patch failed a required validation gate.
- `VERIFIED_CLOSED`: all closure gates passed.

No UI element should imply a stronger state than the stored evidence supports.

`GET /api/v1/analyses/<analysis_id>/findings/<finding_id>/lifecycle` is the authoritative per-finding lifecycle contract. Its optional authenticated downloads return the encrypted-at-rest patched artifact or a JSON security report. The report never treats a proposed patch, zero candidates, syntax success, or static re-scan as verified closure.

`POST /api/v1/analyses/<analysis_id>/findings/<finding_id>/verify-repair` requires the exact original file again and a previously saved encrypted patch. It returns `503 ISOLATION_RUNTIME_UNAVAILABLE` unless a Docker/Podman engine and digest-pinned local image pass capability checks. Successful evidence is append-only and HMAC protected. A separate closure record is created only when every server-side gate passes and is marked `training_eligible=false`; customer source is not copied to the evaluation/training store.
