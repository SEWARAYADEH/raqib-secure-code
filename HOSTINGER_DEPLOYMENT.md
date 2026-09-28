# Hostinger deployment gate

Verified 2026-09-28: `raqib.alaseeltech.com` displays Hostinger's default page on a Business Web Hosting plan. The panel offers VPS setup but shows no existing VPS. [Hostinger support](https://www.hostinger.com/support/which-programming-languages-and-frameworks-are-supported-at-hostinger/) states that Python/Flask requires VPS Hosting. This repository uses Flask; publishing only its React build here would create a login and analysis UI without a working API. Do not call that a working Raqeeb release.

## Required infrastructure

1. Hostinger VPS or another approved Python/Flask-capable backend host, HTTPS routing for the subdomain, and an explicit spending decision before any paid plan change.
2. Server-side secret storage for `SECRET_KEY`, `ANALYSIS_API_TOKEN`, `RECORD_INTEGRITY_KEY`, `EMAIL_VERIFICATION_HMAC_KEY`, `SMTP_PASSWORD`, and optional `OPENAI_API_KEY`. Never upload `.env` or the analysis database.
3. A persistent private database/workspace, process supervisor, reverse proxy, TLS, backups with restore verification, and one worker until email challenge state is shared.
4. Working SMTP. Both the earlier local credential and the password supplied on 2026-09-28 received SMTP authentication error `535` from `smtp.hostinger.com:465`. The mailbox credential must be corrected in Hostinger and stored privately; verify delivery before release.
5. `OSV_ADVISORY_LOOKUP_ENABLED` defaults to false. Enabling it sends exact package coordinates, not uploaded source or manifest bodies, to the [OSV querybatch API](https://google.github.io/osv.dev/post-v1-querybatch/). Disclose this external lookup before enabling it publicly.

## Release acceptance

Run backend tests and frontend build; deploy API and UI; verify `/api/health`; complete a real OTP; upload harmless file and ZIP; refresh owner-scoped saved results; and check the public HTTPS page and API together. No uploaded-code replay or verified closure is available without disposable isolation and the full evidence pipeline.
