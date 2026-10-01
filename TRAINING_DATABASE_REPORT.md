# Raqeeb training and test persistence — 2026-10-01

## Implemented

Raqeeb now stores trusted, versioned security evaluation fixtures and actual automated test outcomes in a private SQLite database. This gives future model work a reproducible data source without treating an unverified static finding as a proven vulnerability. No machine-learning model was trained in this change.

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| `training/cases/sql_injection.json` | Seven existing synthetic SQL cases, including unsafe patterns and safe counterexamples. |
| `training/cases/reference_fixtures.json` | Five versioned Python, JavaScript, and JSX references with expected static outcomes and before/after pairing. |
| `training/fixtures/` | Full trusted synthetic source files used by the reference tests. |
| `backend/app/training_store.py` | SQLite schema, checked-in case validation, immutable case IDs, suite and individual test evidence, restricted JSONL export. |
| `backend/record_training_tests.py` | Runs real backend tests, frontend tests, and production build; records their outcomes. |
| `backend/tests/test_training_store.py` | Persistence, restart, label, private export, and uploaded-code isolation tests. |
| `backend/tests/test_reference_repairs.py` | Reuses the reference manifest to test real parser/analysis results and the trusted Python/JavaScript repair examples. |

## Database and export

The database is `backend/instance/training_evaluation.sqlite3`; the synthetic export is `backend/instance/training_cases.jsonl`. Both paths are ignored by Git. The database uses SQLite WAL journaling and full synchronous writes.

- `training_cases`: trusted synthetic source, SHA-256 hashes, provenance, language, pack, before/after pair, expected and observed static counts, and one of `STATIC_CANDIDATE`, `STATIC_NON_CANDIDATE`, `NO_SECURITY_CLAIM`. Verification and closure counts are fixed at zero.
- `training_test_runs`: suite, pass/fail status, exit code, aggregate counts, UTC timestamp, and SHA-256 of command output. Raw command output is not retained.
- `training_test_results`: individual trusted test identity and `PASSED`, `FAILED`, or `SKIPPED`, linked to its run.

The corpus is loaded only from checked-in `training/` manifests and fixtures. Existing IDs cannot be silently overwritten with changed source or expectations. Uploaded customer code is analyzed through the normal API but is not copied into this corpus, its export, or the public examples endpoint. Export is restricted to the private database directory.

## Verified results

The latest recorded run passed **186 backend tests**, **4 frontend tests**, and the **frontend production build**. The database contains **190 passing individual test outcomes** from that run. Earlier run history, including a failed run while adjusting the published demo-account production guard, is retained rather than rewritten. It contains **12 trusted source cases**: four static candidates, seven static non-candidates, and one JSX structure-only case. The user-upload isolation test passed. The JSONL export has 12 synthetic records.

The Python SQL pair has in-memory SQLite functional and replay assertions; the JavaScript pair has Node assertions using a recording database adapter. These checks apply only to those trusted fixtures. They do not prove an arbitrary uploaded project's exploitability, repair, or closure.

## Reproduce

From the project root on Windows:

```powershell
backend\.venv\Scripts\python.exe backend\record_training_tests.py
```

The runner requires the existing Python virtual environment and Node.js/npm. It runs repository-owned tests and build commands, not uploaded projects. For future model work, separate paired before/after cases by `pair_id` during dataset splitting and never promote static candidate labels to ground-truth vulnerability labels without independent verification.
