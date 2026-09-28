# Raqeeb training / evaluation cases

"Training" here means a knowledge and evaluation dataset for Raqeeb, not machine-learning model training. Cases are deterministic regressions: each records a short source program and expected static candidate count. The suite includes safe and unresolved counterexamples so a dangerous method name alone cannot pass as a finding. No case is executed as uploaded application code.

The first implemented pack is SQL injection. The other four competition packs remain scoped but not claimed complete; see `docs/FOCUSED_SCOPE.md` and `docs/PROJECT_STRUCTURE.md`.
