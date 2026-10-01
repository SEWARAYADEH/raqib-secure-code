# RAQEEB controlled static-analysis demo

`security_fixtures/raqeeB_demo_5_vulnerabilities_550plus.py` is a 1,459-line, 51,416-byte synthetic Python fixture. Its SHA-256 is `7ec03e9f02f2edacd8608b01cd6142404a7b5788555268fbef7a119a470b06d4`. The copy is byte-for-byte identical to the supplied file. Do not import or run it. Upload it only as a code file through **New Analysis**.

The ordinary `/api/v1/analysis/source` route applies bounded intake, content-based language detection, tree-sitter parsing, application understanding, security semantics, intra-function data flow, candidate assessment, append-only owner-scoped persistence, and the saved-record API. The frontend reads that saved record. No demo finding is seeded or hardcoded.

## Observed result on 2026-10-01

Baseline before demo changes: backend 195 passed, frontend 4 passed, production build passed. The first live upload produced one analyzed Python file, 117 functions, 10 Flask routes, 8 detected sources, 7 detected sinks, 4 observed static paths, 3 candidates, and 1 non-candidate path. The second live upload after adding bounded code excerpts produced the same counts. All three findings are `CANDIDATE`; zero vulnerabilities were runtime-verified and zero were closed.

| Test category | Input present | Current engine result | Evidence / limit |
| --- | --- | --- | --- |
| SQL Injection | Yes | Detected, static candidate | `request.args.get` line 164 → `user_id` → `query` → `cursor.execute` line 175. |
| Command Injection | Yes | Detected, static candidate | `request.args.get` line 228 → `host` → `command` → `subprocess.run` line 234. Runtime exploitability unverified. |
| Path Traversal | Yes | Not detected; pack not implemented | Input exists in the fixture, but no supported pack finding. |
| Reflected XSS | Yes | Not detected; pack not implemented | Input exists in the fixture, but no supported pack finding. |
| IDOR / Broken Authorization | Yes | Not detected; pack not implemented | Route exists in the fixture, but no supported pack finding. |

The parameterized SQL counterpart at lines 191–202 is classified `NON_QUERY_ARGUMENT_ONLY`. The original command assessment also promoted the `shell=False` argument-list counterpart at lines 259–267; that earlier saved result remains in history. The current assessment classifies that path `NON_SHELL_ARGUMENT_FLOW`, with the called program's argument semantics still `UNRESOLVED`. A shell interpreter launched through a list remains a candidate.

The report derives file, source, sink, candidate, trace, and unresolved counts from the persisted analysis. Finding details display only bounded code excerpts tied to the source and sink line numbers; React renders them as text, without HTML injection. Excerpts remain in the owner-scoped integrity-checked record and are excluded from the optional Codex advisor context. Previously saved records do not gain excerpts retroactively.

Earlier live screenshot record for `admin@securenergy.com`: `266704ad-a129-4843-8361-79c3e67c3c13`. It was independently read back from the HMAC-checked SQLite store with the fixture SHA-256 above, 3 candidates, 1 non-candidate path, and the `shell=True` source excerpt on line 236. Post-change checks: backend 196 passed, frontend 4 passed, production build passed.

Current analysis after command assessment: `a51fbf76-6eee-4bbf-9a40-4373370eab52`, with 2 static candidates and 2 non-candidate paths. The regular upload endpoint created this HMAC-checked owner record. The repair-proposal endpoint then accepted the exact original SHA-256 and returned separate SQL and command diffs. Each edited variant passed Python syntax parsing and its original function/category no longer produced a static candidate. A combined proposed file is saved privately at `backend/instance/demo_output/raqeeB_demo_5_vulnerabilities_550plus.proposed.py`: 0 static candidates, 4 non-candidate paths, valid syntax. None of this is functional verification, replay, or verified closure. Command portability, especially `echo` as a shell built-in on Windows, is unresolved and requires a real isolated functional test before applying that proposal.

## Screenshot order

1. Projects: latest `raqeeB_demo_5_vulnerabilities_550plus.py` entry.
2. New Analysis: Code File selected.
3. Selected file facts: name, 50.2 KB, preliminary Python.
4. Analysis Progress: one file, four observed paths, three candidates.
5. Project Structure: Flask routes and 117 functions.
6. Findings: two current static candidates; historical records still show the earlier false positive.
7. SQL Finding Detail: lines 164 → 172 → 175.
8. SQL trace and code excerpts.
9. Command Finding Detail: lines 228 → 231 → 234.
10. Technical report: parameterized SQL and `shell=False` list paths not promoted; inspect their stated limits.
11. Executive report: original SHA-256, counts, candidate list.
12. Closure tab: testing, replay, re-scan, and re-trace remain not run.

Do not label any static candidate a verified vulnerability or a closed fix. No uploaded source was executed or copied into the training corpus.
