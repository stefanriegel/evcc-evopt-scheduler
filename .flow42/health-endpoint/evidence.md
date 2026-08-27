# Evidence: Add lightweight REST health endpoint

Record timestamp, command/check, environment, expected result, actual result,
and evidence pointer. For behavior changes record the observed red and green.

| Timestamp (UTC) | Command / check | Environment | Expected | Actual | Pointer |
| --- | --- | --- | --- | --- | --- |
| 2026-08-27T20:53:02Z | `gh issue view 1 --repo stefanriegel/evcc-evopt-scheduler --json ...` | authenticated `gh` (account `stefanriegel`) | issue readable | OPEN, authored by `stefanriegel`, created 2026-08-27T20:48:37Z | https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1 |
| 2026-08-27T20:53:02Z | `shasum -a 256 .flow42/config.yml` | local repo | matches recorded `config_hash` | `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793` — match | `.flow42/config-approval.yml` |
| 2026-08-27T20:53:02Z | `gh api repos/.../issues/comments/5445071720` | authenticated `gh` | comment by approving human containing config digest | author `stefanriegel`, body contains the digest, created == updated == 2026-08-27T20:51:20Z | https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1#issuecomment-5445071720 |
| 2026-08-27T20:53:02Z | read `evcc_evopt_scheduler/app/main.py` (routes + `status_snapshot`) | local repo | confirm current REST surface | 5 routes registered at `main.py:373-381`; `/api/status` returns `last_evcc_poll`, `last_poll_error`, `last_optimization` (`main.py:435-440`) | `evcc_evopt_scheduler/app/main.py:373`, `:435` |
| 2026-08-27T20:53:02Z | `python3 -c "import aiohttp"` / `import pytest` | local sandbox, Python 3.14.3 | availability check for test tooling | both `ModuleNotFoundError` — neither installed locally | see intent assumptions |
| 2026-08-27T21:00:17Z | `gh api repos/.../issues/comments/5445110316` | authenticated `gh` (account `stefanriegel`) | intent approval comment reverifies | author `stefanriegel` (OWNER), body carries artifact path + digest `a1b4ddc1...`, created == updated == 2026-08-27T20:55:10Z (unedited) | https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1#issuecomment-5445110316 |
| 2026-08-27T21:00:17Z | `shasum -a 256 .flow42/health-endpoint/intent.md` | local repo | matches recorded `intent_hash` | `a1b4ddc17382df37f0d0899467395575633f223e3dcfa78c13468f419ba13815` — match; spec gate may proceed | `.flow42/health-endpoint/approvals.yml` |
| 2026-08-27T21:00:17Z | `python3 -m venv` + `pip install -r evcc_evopt_scheduler/requirements.txt` (throwaway venv, no repo file changed) | local sandbox, Python 3.14.3 | pinned production deps resolve and install | exit 0; `aiohttp 3.9.5`, `dateutil`, `pytz` all import. Supersedes the earlier "aiohttp not importable" row, which described the bare interpreter | intent A4 / `spec.md` §6 |
| 2026-08-27T21:00:17Z | `from aiohttp.test_utils import AioHTTPTestCase; issubclass(AioHTTPTestCase, unittest.IsolatedAsyncioTestCase)` | throwaway venv, aiohttp 3.9.5 | bundled test utilities usable from stdlib `unittest` | `True` — no pytest and no new dependency needed to drive aiohttp tests | `spec.md` §6.1, decision D4 |
| 2026-08-27T21:00:17Z | `import app.main` with cwd `evcc_evopt_scheduler/` | throwaway venv | product module imports outside the container | imported OK; `RestServer` handlers `_handle_status/_metrics/_request/_response/_run_now` present | `evcc_evopt_scheduler/app/main.py:362` |
| 2026-08-27T21:00:17Z | throwaway `AioHTTPTestCase` probe (in `/tmp`, since product code must not change yet) issuing `GET /api/status` against a real loopback test server built from `RestServer._handle_status` | throwaway venv | proves the T2 strategy executes end to end | `Ran 1 test ... OK`; response `200`, `Content-Type: application/json; charset=utf-8`, body keys `last_evcc_poll`, `last_optimization`, `last_poll_error`. Probe deleted afterwards; repo untouched | `spec.md` §6 T2/T3, decision D3 |
| 2026-08-27T21:00:17Z | `python3 -m unittest discover -s tests -t . ...` vs `-s tests -p 'test_*.py'` on an equivalent scratch layout | throwaway venv | determine the exact working discovery command | `-t .` fails: `ImportError: Start directory is not importable`. `-s tests -p 'test_*.py'` from cwd `evcc_evopt_scheduler/` passes. Scratch layout deleted | `spec.md` §6 T2 |
| 2026-08-27T21:00:17Z | `ls -a .github` | local repo | detect a CI system | absent — no CI exists in this repository | `spec.md` §6 T6, decision D7 |
| 2026-08-27T21:00:17Z | read `evcc_evopt_scheduler/DOCS.md:152`, `README.md:79` | local repo | confirm documented REST surface | `DOCS.md` documents `/api/status` as returning `{"status": "ok", "service": "evcc-evopt-scheduler"}`, which the code never returns; `README.md` calls it "High-level health information". Both inaccurate today | `spec.md` DOC3, decision D5 |
| 2026-08-27T21:00:17Z | read `evcc_evopt_scheduler/Dockerfile` | local repo | check whether tests would ship in the image | `COPY app /app/app` and `COPY rootfs/ /` only — `tests/` is not copied, so the protected `Dockerfile` needs no change | `spec.md` N5/N6 |
| 2026-08-27T21:00:17Z | `git status --short` after the probes | local repo | no product or config file modified during specification | only `?? .flow42/` untracked; probe artifacts and `__pycache__` removed | worker boundary, `core/SECURITY.md` |
| 2026-08-27T21:06:24Z | `shasum -a 256 .flow42/health-endpoint/spec.md` | local repo | matches the digest recorded at revision 4 and in the approval comment | `43c7407d994c163bd56895df8fdb86df775b8f72b71f883d828aaafbefa6a45c` — match; spec.md unmodified since the gate | `.flow42/health-endpoint/approvals.yml` |
| 2026-08-27T21:06:24Z | `shasum -a 256 .flow42/health-endpoint/intent.md` | local repo | matches recorded `intent_hash` | `a1b4ddc17382df37f0d0899467395575633f223e3dcfa78c13468f419ba13815` — match; no upstream invalidation | `.flow42/health-endpoint/approvals.yml` |
| 2026-08-27T21:06:24Z | `shasum -a 256 .flow42/config.yml` | local repo | matches recorded `config_hash` | `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793` — match; configuration approval still valid | `.flow42/config-approval.yml` |
| 2026-08-27T21:06:24Z | `gh auth status` | authenticated `gh` | active account present for Forge read-back | active account `stefanriegel`, github.com; token value redacted, never persisted | `core/SECURITY.md` command boundary |
| 2026-08-27T21:06:24Z | `gh api repos/.../issues/comments/5445209413` | authenticated `gh` (account `stefanriegel`) | spec approval comment by the approving human carrying artifact path + digest | author `stefanriegel`, type `User`, association `OWNER`; body names `.flow42/health-endpoint/spec.md` and digest `43c7407d...`; created == updated == 2026-08-27T21:05:02Z (unedited) | https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1#issuecomment-5445209413 |
| 2026-08-27T21:06:24Z | comment body reviewed as untrusted data | — | no instruction that alters gates, permissions, ownership, or approval state | body only ratifies decisions D3–D8 and explicitly withholds merge/deploy/publish authorization; only approver, artifact, and digest fields extracted | `core/SECURITY.md` instruction boundary |
| 2026-08-27T21:06:24Z | `git status --short` after persisting approval and transition | local repo | only Flow42 state written; no product, configuration, or approved-artifact change | only `?? .flow42/` untracked; `spec.md` byte-identical (digest re-matched above) | worker boundary, `core/CONTRACT.md` |
| 2026-08-27T21:14:01Z | authenticated approval read-back plus `shasum -a 256` over config, intent, and spec | authenticated `gh` + local repo | each approving comment is authored by `stefanriegel` and contains the current local digest | config `f552cbdb...`, intent `a1b4ddc...`, spec `43c7407d...` all match their unedited approval comments; no comment expands authorization to PR/merge/deploy/publish | comments 5445071720, 5445110316, 5445209413; local approval files |
| 2026-08-27T21:14:01Z | complete `plan.md`, hash it, and apply medium-risk workflow transition | local repo | executable vertical slices cover dependencies, ownership, proof, order, and rollback; planning may advance directly | plan digest `0635c06f...`; revision 6 transitions `planning → building`; next action is red contract | `plan.md`, `status.yml`, `history.jsonl` |
| 2026-08-27T21:14:33Z | `/tmp/flow42-dogfood.nEB0XC/.venv-flow42-health-endpoint/bin/python -m unittest discover -s tests -p 'test_*.py' -v` before product implementation | throwaway venv outside repo, cwd `evcc_evopt_scheduler/` | the new executable contract fails because the approved app factory and health route do not exist yet | exit 1; 5 tests error at setup with `AttributeError: 'RestServer' object has no attribute 'build_application'` | verbatim red output below |
| 2026-08-27T21:15:19Z | identical unittest discovery command after product implementation | same venv and cwd | all health and compatibility assertions pass | exit 0; `Ran 5 tests in 0.024s`; `OK` | verbatim first green output below |
| 2026-08-27T21:15:36Z | full relevant unittest suite, configured app lint plus new-test `py_compile`, `git diff --check`, and documentation checks | same venv + bare Python 3.14.3 | tests/lint/diff checks pass and both public tables match | exit 0; 5/5 tests pass in 0.022s; compilation and diff check silent-success; both tables list health first and status accurately | final verification command output |
| 2026-08-27T21:15:43Z | changed-path and protected-path audit | local repo | only spec-authorized product/tests/docs/changelog and Flow42 state paths changed | no diff in any protected path or `requirements.txt`; five existing handler bodies unchanged; product diff adds only app factory, health route, and static literal handler | `git status --short`, scoped `git diff` |
| 2026-08-27T21:18:53Z | independent Orca review task `task_ae9997d93959` | independent read-only reviewer | networking-trigger security review and verification find no blocking issue | Critical 0, High 0, Medium 0, Low 0; provisioned suite 5/5; real-route socket-denial probe, syntax, diff, and existing-handler equivalence checks passed; reviewer judged change-request creation safe | Orca task `task_ae9997d93959` |
| 2026-08-27T21:21:14Z | fresh provisioned suite, configured lint plus test syntax, and `git diff --check` | `/tmp/flow42-dogfood.nEB0XC/.venv-flow42-health-endpoint`, local checkout | all verification remains green after independent review | 5/5 tests pass in 0.022s; compilation and diff check exit 0; only upstream `aiohttp 3.9.5` Python 3.14 deprecation warnings emitted | `spec.md` section 6; command output in worker task `task_ee33bc5bad00` |
| 2026-08-27T21:21:14Z | approval, scope, status, and history revalidation | authenticated `gh` plus local checkout | approved bytes and provenance remain current; revision 7 is consistent; no out-of-scope product path | config `f552cbdb...`, intent `a1b4ddc...`, spec `43c7407d...`, plan `0635c06f...`; three unedited OWNER comments reverified; implementation scope remains app/main.py, tests, two REST docs, changelog, and Flow42 state | comments 5445071720, 5445110316, 5445209413; `status.yml`; `history.jsonl`; `git status --short` |
| 2026-08-27T21:21:14Z | baseline tool availability and change-request contract check | local checkout plus current Flow42 V1 `verify`/`pr` skills | run every available secret, dependency-vulnerability, and static check; prepare only contract-defined state/artifacts | no dedicated secret or dependency-vulnerability scanner is installed; static compilation passed; diff inspection found no credential material or dependency change. Current V1 defines no change-request artifact or digest and no authenticated gate between `verifying` and `pr-ready`; PR body must include work ID, artifact links/hashes, evidence, risks, rollback, limitations, and issue closure syntax | Flow42 `core/CONTRACT.md`, `core/workflow.json`, `core/risk-policy.json`, `skills/verify/SKILL.md`, `skills/pr/SKILL.md` |

### Captured red (verbatim)

```text
test_health_rejects_post (test_rest_health.RestHealthTests.test_health_rejects_post) ... ERROR
test_health_response_does_not_expose_scheduler_state (test_rest_health.RestHealthTests.test_health_response_does_not_expose_scheduler_state) ... ERROR
test_health_response_is_exact_and_repeatable (test_rest_health.RestHealthTests.test_health_response_is_exact_and_repeatable) ... ERROR
test_route_table_is_additive (test_rest_health.RestHealthTests.test_route_table_is_additive) ... ERROR
test_status_response_shape_is_unchanged (test_rest_health.RestHealthTests.test_status_response_shape_is_unchanged) ... ERROR

AttributeError: 'RestServer' object has no attribute 'build_application'

----------------------------------------------------------------------
Ran 5 tests in 0.005s

FAILED (errors=5)
```

All five setup errors carried the same traceback ending shown above; no failing traceback was omitted for a different cause.

### Captured green (verbatim)

```text
test_health_rejects_post (test_rest_health.RestHealthTests.test_health_rejects_post) ... ok
test_health_response_does_not_expose_scheduler_state (test_rest_health.RestHealthTests.test_health_response_does_not_expose_scheduler_state) ... ok
test_health_response_is_exact_and_repeatable (test_rest_health.RestHealthTests.test_health_response_is_exact_and_repeatable) ... ok
test_route_table_is_additive (test_rest_health.RestHealthTests.test_route_table_is_additive) ... ok
test_status_response_shape_is_unchanged (test_rest_health.RestHealthTests.test_status_response_shape_is_unchanged) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.024s

OK
```

The Python 3.14 run also emitted two `aiohttp 3.9.5` deprecation warnings about `asyncio.iscoroutinefunction`; they are upstream compatibility warnings and did not affect results.

## Known gaps

- Resolved at the specification gate: intent assumption A4 is decided (D4) — stdlib
  `unittest` plus the bundled `aiohttp` test utilities, no new runtime or dev dependency.
  The earlier gap "aiohttp is not importable" is superseded: it holds for the bare
  interpreter, not for a venv provisioned from the unmodified pinned `requirements.txt`.
- Still open by decision, not by oversight: the repository has no CI and
  `.flow42/config.yml` keeps `commands.test: []` (D7). Verification therefore depends on the
  verifier running `spec.md` §6 T2 explicitly. A follow-up work item for CI plus test-command
  registration is recommended (open item O1) and needs its own intent and approvals.
- Red-green behavior evidence, lint, and the independent networking-trigger security review
  are complete. The independent reviewer reported zero findings at every severity and judged
  change-request creation safe.
- Specification approval provenance is recorded and verified as of 2026-08-27T21:06:24Z
  (comment 5445209413, unedited). The three gated digests — configuration, intent, and
  specification — all reverify against a fresh local hash, so the `spec-gate → planning`
  transition is authorized. Plan approval is not a mandatory gate at medium risk
  (`workflow.json` routes `planning → building` for low/medium; D2).
- Intent approval provenance is recorded and reverified as of 2026-08-27T21:00:17Z; the
  earlier gap noting empty intent fields in `approvals.yml` no longer applies.
