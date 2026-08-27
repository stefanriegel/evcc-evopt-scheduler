# Decisions: Add pull-request CI gates

- **D1 — PR events only.** Use `pull_request` for opened, synchronized, reopened, and ready-for-review activity; never `pull_request_target` or a non-PR trigger.
- **D2 — Read-only token.** Grant only workflow-level `contents: read`.
- **D3 — Immutable first-party Actions.** Pin checkout v4 to `11d5960a326750d5838078e36cf38b85af677262` and setup-python v5 to `a26af69be951a213d495a4c3e4e4022e16d87065`, authenticated from their official repositories.
- **D4 — Python 3.11.** Use the runtime shared by all current add-on base images; no matrix.
- **D5 — Existing pins only.** Install unchanged requirements without pip upgrade, cache, or another dependency source.
- **D6 — Exact validation.** Run focused unittest discovery and the exact approved compilation argv.
- **D7 — Per-PR cancellation.** Cancel superseded runs only for the same workflow and PR number.
- **D8 — CI proves itself.** Require an observed failing PR run and corrected successful run at the reviewed head.
