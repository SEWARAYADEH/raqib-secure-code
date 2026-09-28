# Workflow, storage, and responsibility model

## User-visible workflow

1. Upload a supported source file or ZIP project.
2. Safe intake validates size, filename/path rules, ZIP safety, member counts, and supported source types.
3. Language intelligence records evidence and rejects unresolved parser coverage.
4. Application understanding extracts structure, frameworks, routes, calls, imports, database candidates, and security context.
5. Data-flow tracing connects user-controlled sources to sensitive sinks when the relationship is supported by evidence.
6. Security packs classify observations into candidates or non-candidates.
7. Exploitability verification runs only in an approved disposable isolation runtime.
8. Root cause and minimal remediation are proposed only from supported evidence.
9. Syntax/build/unit/integration/functional checks verify the application still works.
10. Replay, re-scan, and re-trace repeat the relevant security scenario.
11. Evidence of closure is produced only if every required gate passes.
12. Updated artifacts are downloaded separately; the original is never overwritten.

## Current safety contract

- Uploaded-code execution during intake: disabled.
- Original overwrite: disabled.
- Nested ZIP archives: rejected.
- ZIP symlinks: rejected.
- Analysis claims: evidence gated.
- AI authority: advisory only.
- Green/closed state: reserved for completed verification evidence.

## Persisted data

Persisted:
- analysis identifier,
- owner subject,
- artifact hash,
- structured analysis result,
- record integrity MAC.

Not intentionally persisted as part of the analysis record:
- plaintext service secrets,
- AI API keys,
- SMTP passwords,
- raw uploaded source text.

Temporary:
- extracted project workspace used during bounded analysis.

## Secrets

Required production secrets belong in the host secret store or local `backend/.env` only:

- `SECRET_KEY`
- `ANALYSIS_API_TOKEN`
- `RECORD_INTEGRITY_KEY`
- `EMAIL_VERIFICATION_HMAC_KEY`
- `SMTP_PASSWORD`
- optional `OPENAI_API_KEY`

Never commit a real `.env` file.

## AI boundary

The AI advisor can help explain:
- root-cause hypotheses,
- minimal patch strategy,
- suggested tests,
- unresolved questions.

It cannot independently set:
- exploitability verified,
- vulnerability closed,
- evidence of closure.
