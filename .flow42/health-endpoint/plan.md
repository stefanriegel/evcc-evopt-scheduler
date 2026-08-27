# Plan: Add lightweight REST health endpoint

- Work ID: `health-endpoint`
- Approved specification: `43c7407d994c163bd56895df8fdb86df775b8f72b71f883d828aaafbefa6a45c`
- Risk: medium; planning advances directly to building without a plan approval gate.
- Scope boundary: only the product, tests, documentation, changelog, and Flow42 evidence/state paths authorized by the approved specification. No protected path, dependency, CI, release, PR, merge, deploy, or publication change.

## Vertical slices

### Slice 1 — Executable liveness contract (red)

- Outcome: a standard-library `unittest` suite exercises the real `aiohttp` application and specifies the complete six-route surface, exact health response, idempotence/state independence, unchanged status response shape, and GET-only method behavior.
- Dependencies: approved spec; throwaway venv populated from the unchanged pinned `requirements.txt`.
- Owned files: `evcc_evopt_scheduler/tests/test_rest_health.py`, `.flow42/health-endpoint/evidence.md`.
- Proof: run `python -m unittest discover -s tests -p 'test_*.py' -v` from `evcc_evopt_scheduler/`; capture the expected pre-implementation failure caused by the absent app factory/health route.
- Branch/worktree: current isolated `flow42/health-endpoint` worktree only; no parallel worker.
- Integration order: first, before product code.
- Rollback: delete the new test and its evidence row; no runtime behavior has changed.

### Slice 2 — Additive application and handler (green)

- Outcome: `RestServer.build_application()` returns the configured application, `start()` uses it, and `GET /api/health` returns the exact constant JSON object with explicit status 200. Existing handler bodies remain unchanged.
- Dependencies: Slice 1 red evidence.
- Owned files: `evcc_evopt_scheduler/app/main.py`, `.flow42/health-endpoint/evidence.md`.
- Proof: rerun the identical unittest command to green; run configured `py_compile` plus compilation of the new test.
- Branch/worktree: same worktree, sequential after Slice 1.
- Integration order: second.
- Rollback: remove the factory, route, and health handler, then restore `start()`'s prior inline application construction; the test returns to red.

### Slice 3 — Public contract parity

- Outcome: both REST API tables list `/api/health` first, accurately distinguish liveness from `/api/status`, and the changelog records the unreleased addition and documentation fix.
- Dependencies: Slice 2 green behavior.
- Owned files: `evcc_evopt_scheduler/README.md`, `evcc_evopt_scheduler/DOCS.md`, `evcc_evopt_scheduler/CHANGELOG.md`.
- Proof: targeted text checks confirm both tables and literal payload; diff review confirms only documentation changed for `/api/status`.
- Branch/worktree: same worktree, sequential after Slice 2.
- Integration order: third.
- Rollback: remove the `[Unreleased]` entries and restore the three table rows; runtime behavior is unaffected.

### Slice 4 — Verification and gate handoff

- Outcome: full relevant unittest suite and lint pass; diff proves protected paths and dependencies untouched; Flow42 state reaches `verifying` with the independent security review and change-request approval still pending.
- Dependencies: Slices 1–3 complete.
- Owned files: `.flow42/health-endpoint/evidence.md`, `.flow42/health-endpoint/status.yml`, `.flow42/health-endpoint/history.jsonl`.
- Proof: clean command outputs, `git diff --check`, changed-path allowlist/protected-path audit, and review of the five pre-existing handler bodies.
- Branch/worktree: same worktree; stop before opening a PR or taking any irreversible action.
- Integration order: last.
- Rollback: Flow42 state can record a verification failure and return to building; no PR exists to close.

## Parallelization map

No parallel execution. The red test must precede implementation, product behavior must precede documentation verification, and the task explicitly forbids delegation.

## Integration order

1. Revalidate authenticated configuration, intent, and specification approvals and hashes.
2. Commit no changes; write and execute the complete test contract to capture red.
3. Implement the minimal additive application factory, route, and constant handler; rerun to green.
4. Update both API tables and the unreleased changelog.
5. Run the full relevant suite, lint, diff/path audits, and record evidence.
6. Advance to verification only; stop before the mandatory independent security review/change-request/irreversible-action gates.

## Risks and rollback

- State disclosure: exact whole-object and populated-state tests reject any added or dynamic field.
- Existing-route regression: the real application route table and `/api/status` response shape are characterized; existing handler bodies must remain byte-identical.
- Dependency/readiness coupling: code review confirms the health handler contains only literals and performs no I/O or state access.
- Documentation drift: both tables are updated in one slice and checked together.
- Scope violation: final changed-path audit rejects protected paths, dependency files, CI files, and unapproved product paths.
- Entire runtime change is reversible by deleting one route/handler and inlining the application setup; no persistent data or external state is modified.
