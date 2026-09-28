# Reporting model

Raqeeb reports must distinguish observation, candidate, verified exploitability, remediation, and closure.

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
