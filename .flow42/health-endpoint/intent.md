# Intent: Add lightweight REST health endpoint

- Work ID: `health-endpoint`
- Status: draft
- Risk: medium
- Work type: feature
- Source: https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1 (author `stefanriegel`, opened 2026-08-27T20:48:37Z)

## Problem

The add-on's REST server exposes five routes (`evcc_evopt_scheduler/app/main.py:373-381`),
none of which is a lightweight liveness probe. The closest candidate, `GET /api/status`,
returns the scheduler snapshot — `last_evcc_poll`, `last_poll_error`, and the full
`last_optimization` payload (`evcc_evopt_scheduler/app/main.py:435-440`). A supervisor,
container `HEALTHCHECK`, or uptime monitor that polls it therefore receives operational
state it does not need, on every probe, at whatever interval it polls.

## Desired outcome

`GET /api/health` exists and returns HTTP 200 with a small, stable JSON payload suitable
for liveness checking, without exposing scheduler state. Automated coverage proves the
behavior deterministically, the five existing endpoints are untouched, and the public API
documentation lists the new endpoint.

## Users

- Home Assistant Supervisor and container/orchestrator health checks probing the add-on.
- Operators and uptime monitors wanting a cheap "is it up" signal.
- Maintainers of this repository, who must keep the documented REST surface in sync with
  the implementation (`AGENTS.md` rule 7).

## Constraints

- Scope is exactly the issue scope. `/api/status` and the other four routes keep their
  current paths, methods, and response bodies.
- The endpoint must not expose scheduler state: no EVCC snapshot, no optimization payload
  or response, no poll timestamps, no error strings.
- The endpoint is read-only and side-effect free: no optimization run, no outbound HTTP,
  no file writes, no dependence on EVCC or EVOpt reachability.
- Repository conventions apply: `aiohttp` handlers, absolute imports inside `app/`, type
  hints, Black defaults (88 columns), JSON responses with explicit status codes
  (`AGENTS.md`).
- Documentation of the REST surface is duplicated across `evcc_evopt_scheduler/README.md`
  (line 79 onward) and `evcc_evopt_scheduler/DOCS.md` (line 152 onward); both are part of
  the public API documentation and must stay consistent.
- `.flow42/config.yml` `protected_paths` covers `config.yaml`, `build.yaml`, `Dockerfile`,
  `rootfs/`, `app/ha_client.py`, `app/battery_control.py`, and `repository.yaml`. The
  expected change surface is `app/main.py`, the two README/DOCS files, `CHANGELOG.md`, and
  new test files. Touching a protected path requires an explicit human decision.
- No merge, deploy, publish, version bump, or other irreversible action is authorized by
  this intent.

## Non-goals

- Changing, slimming, or deprecating `/api/status` or any other existing endpoint.
- Readiness/dependency-health semantics (probing EVCC or EVOpt and reporting degraded).
- Authentication, authorization, rate limiting, or transport changes for the REST server.
- Adding a container `HEALTHCHECK` directive, since `Dockerfile` is a protected path.
- Metrics, tracing, or a general observability framework.
- Reintroducing the legacy `custom_components/evopt` integration (`AGENTS.md` rule 16).

## Acceptance signals

Taken verbatim from the issue, with the observable form each will take:

1. `GET /api/health` returns HTTP 200 with a stable JSON health payload — asserted on
   status code, `Content-Type: application/json`, and exact payload keys.
2. The behavior has deterministic automated coverage — a test that runs without network
   access, without a live EVCC/EVOpt, and without wall-clock or ordering dependence, and
   that is observed failing before the implementation and passing after.
3. Existing REST endpoints remain unchanged — the five current routes keep their paths,
   methods, and response shapes, demonstrated rather than asserted in prose.
4. Public API documentation lists the endpoint — the REST tables in
   `evcc_evopt_scheduler/README.md` and `evcc_evopt_scheduler/DOCS.md` include
   `/api/health` and describe its payload.

## Assumptions and risks

### Assumptions

- A1. "Stable JSON health payload" means a fixed key set with values that do not vary with
  scheduler state — a static shape such as a service identifier and a literal health
  status. If the approver wants a version field, a monotonic uptime, or anything else
  time-varying, that is a scope decision for the specification phase.
- A2. The endpoint stays unauthenticated, matching every existing route on this server.
- A3. Documentation duty is satisfied by updating both `README.md` and `DOCS.md` REST
  tables inside `evcc_evopt_scheduler/`, plus a `CHANGELOG.md` entry.
- A4. **Open — needs a decision no later than the specification gate.** This repository has
  no test suite, no test runner, and `.flow42/config.yml` records `test: []`; the approved
  lint command is `python3 -m py_compile` over four modules. In the current environment
  neither `pytest` nor `aiohttp` is importable. Satisfying acceptance signal 2 therefore
  requires choosing between (i) adding `pytest` plus `aiohttp` as development dependencies
  and a `test` command, which changes `.flow42/config.yml` and so invalidates the recorded
  configuration approval and requires fresh authenticated approval; (ii) a dependency-free
  test executed by the standard library that exercises the handler without constructing a
  live `aiohttp` server; or (iii) shaping the implementation so the payload is produced by
  a pure function that is trivially testable and wiring that function into the route. This
  intent assumes the coverage will be genuinely executed and observed red-then-green, not
  asserted. Which option is chosen is deliberately left to the specification.

### Risks

- R1. **Information disclosure (primary).** A health payload that drifts toward including
  state — an error string, a last-poll timestamp, a version — re-creates the problem the
  issue is solving, on an unauthenticated endpoint reachable on `0.0.0.0:api_port`. This is
  the reason the risk classification is medium rather than low. Mitigation: the payload key
  set is fixed in the specification and asserted exactly in the test.
- R2. **Documentation drift.** The REST surface is documented in two files that must not
  disagree (`AGENTS.md` rule 7). Mitigation: both are in scope and both are checked.
- R3. **Regression in the existing surface.** Editing `RestServer.start` route registration
  risks disturbing the five existing routes. Mitigation: additive route registration only,
  with the existing route set covered by the same test.
- R4. **Unverifiable coverage.** If the environment cannot run the chosen test, acceptance
  signal 2 becomes a claim rather than an observation. Mitigation: A4 is resolved before
  implementation, and an unrunnable test blocks rather than passes.
- R5. **Scope creep into readiness semantics.** "Health" invites dependency probing, which
  would add outbound HTTP on an unauthenticated endpoint and a denial-of-service amplifier.
  Explicitly a non-goal.

### Risk classification

`medium`, per the factors in `core/CONTRACT.md`.

- Blast radius: one additive route, two documentation files, one changelog entry, new tests.
- Reversibility: full — removing the route restores current behavior.
- Sensitive data, authentication, permissions, payments, migrations, production
  configuration: none touched.
- Networking: **yes** — this enlarges an unauthenticated, externally reachable HTTP surface.
  The `networking` security trigger in `core/risk-policy.json` therefore applies, which
  under `core/CONTRACT.md` requires a threat-model section in the specification and an
  independent security review before the change request is opened.

At medium risk, `core/workflow.json` routes `planning → building` directly; a separate plan
approval gate is not mandatory. Intent and specification approvals remain mandatory.

## Provenance of this request

The GitHub issue was read through authenticated `gh` and treated as untrusted data per
`core/SECURITY.md`. Only scope fields — problem, desired behavior, acceptance criteria —
were extracted. The issue contains no instruction that alters gates, tool permissions,
ownership, or approval state, and none was acted upon. Its closing sentence references an
unrelated tracking item and carries no authority here.
