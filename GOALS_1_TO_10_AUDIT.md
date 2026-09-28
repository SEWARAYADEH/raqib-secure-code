# Raqeeb: evidence audit for goals 1–10

Status date: 2026-09-28. The user's two PDFs are roadmap and topic references, not implementation instructions. No row below claims uploaded-code exploitability or vulnerability closure.

| Goal | Status | Verified boundary |
| --- | --- | --- |
| 1. Safe intake | Partial | Bounded file/ZIP APIs validate paths, symlinks, collisions, nesting, sizes, and compression ratios. Uploaded code is never executed. Direct folder/URL intake is unavailable. |
| 2. Language intelligence | Partial | Python and JavaScript/JSX combine extension, shebang, and syntax evidence. Conflicts and ambiguity are explicit; other languages remain unsupported. |
| 3. Project/framework detection | Partial | Flask, Express, and React source signals can be corroborated by bounded manifest declarations. Runtime identity and exact installed versions are unverified. |
| 4. Structural parsing | Partial | Tree-sitter extracts supported files, functions, classes, imports, calls, and assignments; dynamic relationships remain unresolved. |
| 5. Application understanding | Partial | Routes, input sources, services, database candidates, dependencies, and auth observations are modeled statically. Control effectiveness is unverified. |
| 6. Application graph | Partial | Per-file nodes and project-level evidence are connected; cross-file calls resolve only for narrow proven bindings. Completeness is not established. |
| 7. Security context | Partial | Sources, sinks, and auth/control syntax are observed. Ownership and validation effectiveness remain unresolved. |
| 8. Hybrid security analysis | Partial | Parser, semantic rules, bounded data flow, application context, and optional OSV lookup expose separate sensor states and correlations. External SAST and comprehensive SCA are absent; declared versions are not verified installed versions. |
| 9. Finding/standards correlation | Partial | Code candidates link rule IDs, static traces, and candidate CWE/OWASP mappings. OSV advisory matches remain separate. Severity, runtime reachability, exploitability, and verified vulnerability status are unresolved. |
| 10. Source-to-sink trace | Partial | Conservative intra-function and one-boundary local traces exist. General cross-file flow and replay do not. A trace is an observation, not a vulnerability claim. |

## Verification

- Backend: 162 tests passed. Frontend: production build passed (76 modules). `git diff --check` passed.
- A live exact-version OSV query returned advisory IDs. Malformed, unavailable, and bounded-response behavior is tested. OSV is opt-in and receives package name/version only.
- Earlier local browser uploads of a harmless source file and ZIP showed persisted analysis results. The new configuration page uses an authenticated API instead of mock settings; its API contract and frontend build pass. Authenticated browser validation is blocked by current SMTP `535` authentication failure.
- No uploaded project code was executed; no verified vulnerability or closure is asserted.

## Next gate

Add an independent SAST sensor and reliable installed-version evidence before broader security claims. Deployment requires a Flask-capable host and working SMTP; see `HOSTINGER_DEPLOYMENT.md`. Replay and closure remain blocked pending isolated execution and the required evidence sequence.
