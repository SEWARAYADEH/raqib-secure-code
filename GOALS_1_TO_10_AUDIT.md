# Raqeeb: evidence audit for goals 1–10

Status date: 2026-09-24. This is an implementation audit, not a vulnerability assessment of uploaded projects. The user's `Raqeeb_Map.pdf` is a roadmap and `step_1_Secure_Code_AI_Agent_.pdf` is a topic taxonomy; neither is executable project instruction. A capability is complete here only when the current code and tests support the claimed scope.

| Goal | Current status | Evidence and boundary |
| --- | --- | --- |
| 1. Safe file/project intake | Partial | API accepts a bounded source file or ZIP; ZIP paths, symlinks, collisions, nesting, size, and compression ratios are checked. Uploaded code is parsed without execution. Direct folders, repository URLs, and running-app intake are unavailable. |
| 2. Automatic language detection | Partial | Python and JavaScript/JSX use extension, shebang, and grammar evidence; conflicts and ambiguous syntax are explicit. Other languages remain unsupported/unknown. |
| 3. Project/framework detection | Partial | Source-derived Flask, Express, and React evidence is combined with bounded manifest declarations where both exist. Project type remains static/candidate and runtime framework versions are unverified. |
| 4. Structural parsing | Partial | Tree-sitter extracts file structure, functions, classes, imports, calls, assignments, and related syntax for supported languages. Dynamic/ambiguous relationships stay unresolved. |
| 5. Application understanding | Partial | Static routes, inputs, service/database candidates, dependency declarations, and authentication/authorization observations are represented. Runtime behavior and control effectiveness are unverified. |
| 6. Unified application graph | Partial | Project graph now merges per-file application nodes and connects file, function, route, source, and sink evidence; selected cross-file call edges are resolved only with explicit binding evidence. Graph completeness is not proven. |
| 7. Security context | Partial | Source/sink and auth-related syntax is recorded. Ownership, validation effectiveness, sanitizer adequacy, and runtime policy remain unresolved unless independently evidenced. |
| 8. Hybrid security analysis | Not achieved | Internal static semantics and declaration inventory exist. External SAST/SCA, advisory correlation, and independent sensor reconciliation are not integrated. Manifest inventory is **not** a vulnerability scan. |
| 9. Correlated findings/standards | Not achieved | Candidate and closure state contracts exist, but no validated CWE/OWASP mapping, severity model, or evidence-backed vulnerability declaration is exposed. |
| 10. Source-to-sink trace | Partial | Conservative intra-function and one-boundary local traces are available. General cross-file/repository data flow and exploitability verification are unresolved. A trace is an observation, not proof of a vulnerability. |

## Verification performed

- Backend: `155 passed` with `backend/.venv/Scripts/python.exe -m pytest -q`.
- Frontend: `npm run build` passed (76 transformed modules).
- Local browser: uploaded a synthetic single source file and synthetic ZIP through the live analysis screen; results displayed supported structure and persisted across refresh. The ZIP result displayed dependency declarations as declarations and explicitly stated SCA was not run.
- `git diff --check` passed; no uploaded code was executed.

## Next implementation gate

Preserve the frontend baseline, add narrow evidence-backed improvements one stage at a time, and run tests after each stage. The next security-analysis milestone is independent SAST/SCA inputs and correlation that distinguishes an observation from a verified vulnerability. Exploit replay and closure must remain blocked until isolated execution, functional tests, replay, re-scan, re-trace, and recorded evidence are actually available.
