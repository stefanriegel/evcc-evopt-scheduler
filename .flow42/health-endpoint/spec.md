# Specification: Add lightweight REST health endpoint

- Work ID: `health-endpoint`
- Derived from `intent.md`, digest
  `a1b4ddc17382df37f0d0899467395575633f223e3dcfa78c13468f419ba13815`, approved by
  `stefanriegel` at 2026-08-27T20:55:10Z and reverified through authenticated `gh` read-back
  at 2026-08-27T21:00:17Z.
- Security trigger `networking` is active, so §7 carries a threat model and verification
  requires an independent security review before a change request is opened.

Approving this specification ratifies decisions D3 through D8 in `decisions.md`.

## 1. Domain model and terminology

- **Liveness** — the process is running and its HTTP server is accepting and answering
  requests. It is proven by the server's ability to answer at all, not by the content of
  the answer.
- **Readiness** — the process can do useful work, which for this add-on would mean EVCC and
  EVOpt are reachable and the scheduler is producing plans. Readiness is a non-goal (see
  intent non-goals and R5); nothing in this specification may probe a dependency.
- **Health payload** — the response body of `GET /api/health`. It is a *constant*: a fixed
  key set whose values are compile-time literals, identical on every request for the life of
  the process and across processes at the same code revision.
- **Scheduler state** — anything reachable from `SchedulerState`
  (`evcc_evopt_scheduler/app/main.py:415-451`): `last_evcc_poll`, `last_evcc_state`,
  `last_poll_error`, and `optimization`. Also treated as scheduler state for this
  specification: configuration values, wall-clock time, uptime, process identifiers, host
  names, add-on version, and library versions.
- **Existing REST surface** — the five routes registered in `RestServer.start`
  (`evcc_evopt_scheduler/app/main.py:373-381`): `GET /api/status`, `GET /api/metrics`,
  `GET /api/optimization/request`, `GET /api/optimization/response`,
  `POST /api/optimization/run`.

## 2. Functional requirements

**F1 — The route exists.** `GET /api/health` is registered on the same
`aiohttp` application as the existing five routes, served by the same `web.TCPSite` on
`0.0.0.0:<api_port>` (default `7060`).

**F2 — Exact response.** A `GET` to `/api/health` returns:

- status `200`;
- header `Content-Type: application/json; charset=utf-8` (the exact value produced by
  `aiohttp.web.json_response`; the intent's shorter `application/json` is refined to this
  literal so the assertion is exact — D3);
- body, as a JSON object with exactly these two keys and exactly these values:

```json
{"status": "ok", "service": "evcc-evopt-scheduler"}
```

`status` is the literal string `ok`. `service` is the literal string
`evcc-evopt-scheduler`, matching the add-on `slug` in `evcc_evopt_scheduler/config.yaml`.
The key set is closed: any additional key is a specification violation, and F6 makes that
a test failure rather than a review opinion.

**F3 — No state, no configuration, no clock.** The handler must not read `SchedulerState`,
`AppConfig`, environment variables, files, or the clock, and must not derive any part of the
response from them. Constructing the payload must not require the handler to hold a
reference to any mutable object.

**F4 — Side-effect free and idempotent.** The handler performs no outbound HTTP, no file
write, no logging of request data, no optimization trigger, and no mutation of any shared
object. `N` sequential requests are indistinguishable from one, in both response and effect.
Unlike `POST /api/optimization/run`, it never calls `trigger_run`.

**F5 — Dependency independence.** The response is identical whether EVCC and EVOpt are
reachable, unreachable, or misconfigured, and whether or not an optimization has ever run.
A failing scheduler must still yield `200` and the same body; this endpoint answers
"is the process alive", never "is the system healthy".

**F6 — Route compatibility.** The change to `RestServer` is purely additive. After the
change, the application's route table is exactly the five existing entries plus
`GET /api/health`. For each existing route the path, HTTP method, handler function, status
code, and response body shape are unchanged. `/api/status` in particular keeps returning
`last_evcc_poll`, `last_poll_error`, and `last_optimization`
(`evcc_evopt_scheduler/app/main.py:435-440`).

**F7 — Method and path discipline.** `/api/health` accepts `GET` only. Other methods yield
aiohttp's default `405`; no custom handling is added. The path is exactly `/api/health` —
no alias, no trailing-slash variant, no unauthenticated `HEAD`-specific behavior beyond
aiohttp's default `GET`-derived handling.

**F8 — Testable construction.** Route registration is factored so that the application can
be built without binding a socket: `RestServer` gains a method that returns a configured
`web.Application`, and `start()` calls it before creating the runner and site. This is the
minimum change that lets F6 be *demonstrated* — the test asserts against the real route
table rather than a copy of it (see R3 in `intent.md`). No other behavior of `start()` or
`stop()` changes.

## 3. Non-functional requirements

**N1 — Cost.** Serving one request performs no I/O beyond the socket and no allocation
proportional to scheduler state. The intent's motivating complaint — that probing
`/api/status` serialises the whole optimization payload on every poll — must not reappear
here at any probe interval.

**N2 — Repository conventions** (`AGENTS.md`): `aiohttp` handlers; absolute imports within
`app/`; type hints on the new handler and factory; Black defaults at 88 columns; JSON
response with an explicit status code (rules 3, 4, 13, 18).

**N3 — Documentation parity.** The documented REST surface and the implemented one agree
after the change, in both `evcc_evopt_scheduler/README.md` and
`evcc_evopt_scheduler/DOCS.md` (`AGENTS.md` rules 7 and 21).

**N4 — Determinism.** The test suite passes with no network access beyond loopback, no live
EVCC or EVOpt, no dependence on wall-clock time, test ordering, or ambient environment, and
without binding a fixed port. Repeated runs give identical results.

**N5 — No dependency growth.** `evcc_evopt_scheduler/requirements.txt` is unchanged. No
`requirements-dev.txt`, no `pyproject.toml`, no `setup.cfg`, no lockfile, and no new
third-party import in product or test code. The image built by `Dockerfile` gains nothing.

**N6 — Protected paths untouched.** `config.yaml`, `build.yaml`, `Dockerfile`, `rootfs/`,
`app/ha_client.py`, `app/battery_control.py`, and `repository.yaml`
(`.flow42/config.yml` `protected_paths`) are not modified. Consequence: no version bump,
because `version` lives in the protected `config.yaml` (D6).

## 4. Interfaces and data

### 4.1 HTTP interface

| Property | Value |
| --- | --- |
| Method | `GET` |
| Path | `/api/health` |
| Authentication | none (unchanged from every existing route on this server — intent A2) |
| Request body | none; query parameters ignored and never echoed |
| Status | `200` |
| `Content-Type` | `application/json; charset=utf-8` |
| Body | `{"status": "ok", "service": "evcc-evopt-scheduler"}` |
| Body size | constant, under 64 bytes |

### 4.2 Route table after the change

| Endpoint | Method | Change |
| --- | --- | --- |
| `/api/health` | GET | **new** |
| `/api/status` | GET | unchanged |
| `/api/metrics` | GET | unchanged |
| `/api/optimization/request` | GET | unchanged |
| `/api/optimization/response` | GET | unchanged |
| `/api/optimization/run` | POST | unchanged |

### 4.3 Data flow

Inbound: none — no request field influences the response. Outbound: two string literals.
There is no path from any `SchedulerState`, `AppConfig`, or environment value to the
response bytes. This is the whole security property of the endpoint, and F3 plus the exact
assertion in A-2 are what hold it in place over time.

## 5. Documentation scope

**DOC1 — `evcc_evopt_scheduler/README.md`.** Add a row to the REST API table (line 79
onward): `` `/api/health` `` | `GET` | a description naming it a liveness probe returning a
constant payload. Place it first in the table, above `/api/status`.

**DOC2 — `evcc_evopt_scheduler/DOCS.md`.** Add the equivalent row to the REST API table
(line 152 onward), in the same order, with the literal payload shown as that table already
does for other rows.

**DOC3 — `/api/status` description correction.** `DOCS.md:152` currently documents
`/api/status` as returning `{"status": "ok", "service": "evcc-evopt-scheduler"}`, which the
code has never done — it returns the scheduler snapshot. `README.md` similarly calls it
"High-level health information". Both descriptions are wrong today, and after this change
they would describe `/api/health` while pointing at `/api/status`, which is worse than the
current inaccuracy. Correct both descriptions to state what `/api/status` actually returns:
last EVCC poll timestamp, last poll error, and the last optimization snapshot. This is a
documentation-only correction; `/api/status` behavior is untouched, so the intent's non-goal
is respected (D5).

**DOC4 — `evcc_evopt_scheduler/CHANGELOG.md`.** Add an `## [Unreleased]` section above
`## [0.1.17]` with an `### Added` entry for `/api/health` and a `### Fixed` entry for the
`/api/status` documentation correction, in Keep a Changelog style as the file already uses.
No version number is assigned and no version is bumped (D6).

**DOC5 — out of scope.** Root `README.md`, `AGENTS.md`, `docs/`, container `HEALTHCHECK`
(protected `Dockerfile`), and Ingress or supervisor configuration are not touched.

## 6. CI and test strategy

### 6.1 Resolution of intent assumption A4

A4 is resolved as option (ii) refined, per the human directive: **standard-library
`unittest` exercising the real `aiohttp` application through `aiohttp`'s own bundled test
utilities, adding no runtime and no development dependency** (D4).

This is viable because `aiohttp.test_utils.AioHTTPTestCase` ships inside `aiohttp`, which is
already a pinned production dependency (`requirements.txt`, `aiohttp==3.9.5`), and because
it is a subclass of `unittest.IsolatedAsyncioTestCase` — so the standard-library runner
drives it with no plugin. Both facts were verified in this environment, not assumed; see
`evidence.md` rows dated 2026-08-27T21:00:17Z. `pytest` is not installed, not required, and
not added.

Installing the already-pinned `requirements.txt` into a throwaway virtual environment is
**not** a new dependency: no repository file gains an entry, and the set of packages the
add-on image installs is unchanged. The intent's earlier observation that "`aiohttp` is not
importable" described the bare interpreter, not a provisioned environment; a fresh venv
built from the unmodified `requirements.txt` resolves and imports cleanly on the local
Python 3.14.3 (evidence row 2).

**T1 — Location and framework.** Tests live in `evcc_evopt_scheduler/tests/`
(`AGENTS.md` rule 19's directory), in files matching `test_*.py`, written as
`unittest`/`AioHTTPTestCase` classes. Rule 19 also names pytest; the directive overrides the
runner choice, and the conflict is benign because pytest collects `unittest.TestCase`
subclasses unmodified, so these tests stay pytest-compatible if a runner is ever adopted
(D4). No `__init__.py` is added to `tests/`.

**T2 — Exact command.** From the repository root:

```
python3 -m venv .venv-flow42
.venv-flow42/bin/pip install -r evcc_evopt_scheduler/requirements.txt
cd evcc_evopt_scheduler && ../.venv-flow42/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

The working directory must be `evcc_evopt_scheduler/` so that `app` is importable as a
top-level package and `main.py`'s relative imports resolve, matching the container layout
(`WORKDIR /app`, `COPY app /app/app`). The `-t` form
(`discover -s tests -t .`) was tried and fails with `ImportError: Start directory is not
importable`; the command above is the verified working form (evidence row 4). The venv
directory must not be committed; if `.gitignore` does not already cover it, the venv is
created outside the repository instead.

**T3 — Required test coverage.**

- `/api/health` returns `200`.
- `Content-Type` equals `application/json; charset=utf-8` exactly.
- The parsed body equals `{"status": "ok", "service": "evcc-evopt-scheduler"}` by whole-object
  equality, not by key subset — this is what enforces the closed key set in F2.
- Two successive requests return byte-identical bodies (F4 idempotence).
- The response is unchanged when `SchedulerState` is populated with a poll timestamp, a poll
  error string, and an optimization snapshot — the direct regression test for R1, proving no
  state leaks into the payload (F3, F5).
- The application's registered route table equals the six expected `(method, path)` pairs,
  read from the application built by the product code, not from a literal copied into the
  test (F6, F8).
- `/api/status` still returns keys `last_evcc_poll`, `last_poll_error`, `last_optimization`
  (F6).
- `/api/health` with a method other than `GET` returns `405` (F7).

**T4 — Red-green evidence.** Because this is a behavior change, `core/risk-policy.json`
requires an observed red and an observed green. The `/api/health` tests are written and run
*before* the handler exists, and the failure output is recorded verbatim in `evidence.md`;
the same command is rerun after implementation and the pass recorded. A test that has only
ever been observed green is not acceptable evidence. The route-table and `/api/status`
tests are characterization tests and are expected green from the start; that is recorded as
such rather than presented as red-green.

**T5 — Lint.** The configured lint command
(`python3 -m py_compile` over the four `app/` modules, `.flow42/config.yml`) is run
unchanged, plus `py_compile` over each new test file.

**T6 — No CI workflow.** This repository has no `.github/` directory and no CI system. This
work item does not add one: a first-ever CI pipeline is a larger decision about runners,
matrix, and secrets than an additive route justifies, and it is outside the approved intent
scope. Verification is therefore the locally executed T2 command with its output recorded in
`evidence.md`. A follow-up work item to add CI is recommended and is explicitly deferred,
not forgotten (D7).

**T7 — `.flow42/config.yml` stays unchanged.** Populating `commands.test` would change the
configuration digest and invalidate the recorded configuration approval
(`config-approval.yml`), blocking execution until fresh authenticated approval is obtained.
That cost is not worth paying inside this work item, so the T2 command is instead binding
through this specification: the verifier runs it explicitly, and "the configured test
command is empty" is not an acceptable reason to skip it. Registering the command in
configuration is folded into the D7 follow-up (D7).

## 7. Security considerations and threat model

Scope: the `networking` trigger in `core/risk-policy.json`. The asset is the add-on process
and any information reachable through its HTTP surface. The trust boundary is the network
interface `web.TCPSite` binds — `0.0.0.0:<api_port>`, default `7060`
(`evcc_evopt_scheduler/app/main.py:384`) — which is unauthenticated today for all five
existing routes. This change adds a sixth route on the same boundary; it does not move,
widen, or authenticate that boundary.

Actors: (1) the Supervisor, an orchestrator, or an operator's monitor on the same
network, the intended caller; (2) any other host that can reach the add-on's port, which on
a flat home LAN, an exposed Docker port mapping, or a misconfigured router is effectively
anyone on the LAN and, in the worst case, the internet.

| # | Threat | Vector | Assessment | Mitigation |
| --- | --- | --- | --- | --- |
| TM1 | **Information disclosure** — the endpoint leaks operational state to an unauthenticated caller | Payload drifts to include an error string, a poll timestamp, a version, a hostname, or a config value | The primary risk (intent R1) and the reason the item is medium, not low. Version and hostname are the realistic drift vectors: both look harmless and both aid fingerprinting | F2/F3 fix a closed two-key literal payload; T3 asserts whole-object equality, so any added key fails the test; T3 also asserts the payload is unchanged with state populated |
| TM2 | **Amplification / resource abuse** — the endpoint is used to burn add-on resources | Unauthenticated high-rate `GET` flood | Materially *lower* than the status quo: the payload is a constant under 64 bytes with no serialization of scheduler state, whereas `/api/status` serialises the full optimization payload per request. This change reduces the cheapest available amplification factor rather than raising it | N1 and F3. No rate limiting is added — it does not exist for the five existing routes, and adding it here only would be inconsistent and out of scope |
| TM3 | **SSRF / dependency amplification** — a probe causes outbound requests | Readiness-style dependency probing (intent R5) | Would turn one cheap unauthenticated request into outbound HTTP to EVCC/EVOpt, an amplifier and a liveness-coupling bug | F4/F5 forbid outbound I/O; readiness is an explicit non-goal; T3's state-populated test would not catch this, so it is a review checkpoint for the independent security reviewer |
| TM4 | **State mutation via an unauthenticated route** | Handler triggers work, as `POST /api/optimization/run` does | `trigger_run` is reachable unauthenticated today; adding a second mutating path under a "health" name would be worse, because monitors poll it automatically and on a schedule | F4 forbids mutation; F7 restricts the route to `GET`; the handler holds no reference to `SchedulerState` (F3) |
| TM5 | **Attack-surface enlargement / fingerprinting** | A new well-known path confirms which software is running | Real but small: `service` names the add-on. However `/api/status` and `/api/metrics` already disclose far more to the same unauthenticated caller, so a constant service name adds no meaningful capability | Accepted, explicitly. The `service` key is retained because it is what `DOCS.md` already advertises and it lets a monitor distinguish this add-on from another service on a reused port |
| TM6 | **Reflection / injection** | Request-controlled data echoed into the response | Not applicable: the response is two literals and no request field is read | F2/F3, enforced by T3's exact-equality assertion |
| TM7 | **Availability coupling** | A monitor treats the endpoint as system health and takes down a functioning add-on, or fails to notice a broken one | A `200` from `/api/health` means the process is alive, *not* that scheduling works. An operator wiring this to a restart policy could ignore a genuinely stuck scheduler | Documented, not coded: DOC1/DOC2 must describe it as a liveness probe with a constant payload, so the semantics are not inferred from the name |

**Residual risk, accepted.** The endpoint stays unauthenticated (intent A2), consistent with
the existing five routes. Authentication for this server is a separate, larger decision
(intent non-goal). Given a constant payload with no state, no mutation, and no outbound I/O,
the residual exposure is the existence of the route itself — TM5 — which is accepted above.

**Independent security review** (`core/CONTRACT.md`) is required before a change request is
opened, and must at minimum confirm: the payload contains only the two literals; the handler
closes over no mutable state; no outbound call or file access is introduced; the five
existing routes' handlers are byte-identical to their pre-change form; and the diff touches
no protected path.

## 8. Contradictions and open decisions

Resolved in this specification and recorded in `decisions.md` — approving this specification
ratifies them:

- **D3** — `Content-Type` refined from the intent's `application/json` to the exact value
  `application/json; charset=utf-8`.
- **D4** — A4 resolved: stdlib `unittest` plus bundled `aiohttp.test_utils`; no new
  dependency; `AGENTS.md` rule 19's pytest mention overridden on runner, honored on location.
- **D5** — the incorrect `/api/status` documentation is corrected in scope, as documentation
  only.
- **D6** — no version bump, because `config.yaml` is a protected path; CHANGELOG entry goes
  under `[Unreleased]`.
- **D7** — no CI workflow and no `.flow42/config.yml` `test:` registration in this item;
  both deferred to a follow-up so the configuration approval is not invalidated here.
- **D8** — `/api/health` is placed first in both documentation tables and `service` uses the
  add-on slug `evcc-evopt-scheduler`.

Open, and **not** decided by this specification:

- **O1 — follow-up CI item.** Whether to open a separate work item for CI plus a registered
  test command is the approver's call. Recommended, but no CI work begins under this item's
  approval.

Nothing here authorizes merge, deployment, publication, a version bump, or any other
irreversible action.

## 9. Acceptance criteria

Each criterion is observable and maps to an intent acceptance signal. All must hold.

**A-1 (signal 1).** `GET /api/health` returns `200` with header
`Content-Type: application/json; charset=utf-8`.

**A-2 (signal 1).** The parsed response body is *equal* to
`{"status": "ok", "service": "evcc-evopt-scheduler"}` — same keys, same values, no extras —
asserted by whole-object equality.

**A-3 (signal 1).** The body is byte-identical across two successive requests, and identical
when `SchedulerState` carries a poll timestamp, a poll error string, and an optimization
snapshot.

**A-4 (signal 2).** The T2 command runs to completion and reports `OK` with every test in
T3 executed, using only the standard library and packages already pinned in
`requirements.txt`.

**A-5 (signal 2).** `evidence.md` records the observed red — the `/api/health` tests failing
before the handler exists, with verbatim output — and the observed green after, from the
same command.

**A-6 (signal 3).** The route table read from the application built by product code equals
exactly the six `(method, path)` pairs in §4.2, and `GET /api/status` still returns
`last_evcc_poll`, `last_poll_error`, and `last_optimization`.

**A-7 (signal 3).** `git diff` shows no change to any protected path, no change to
`requirements.txt`, and no change to the five existing handler bodies.

**A-8 (signal 4).** The REST tables in `evcc_evopt_scheduler/README.md` and
`evcc_evopt_scheduler/DOCS.md` both list `/api/health` with its payload, both describe
`/api/status` correctly per DOC3, and do not contradict each other.

**A-9.** `CHANGELOG.md` has an `[Unreleased]` section covering both changes, and
`config.yaml` `version` is unchanged.

**A-10.** `python3 -m py_compile` passes over the four configured `app/` modules and every
new test file.

**A-11.** The independent security review required by the `networking` trigger is completed
and recorded, with the §7 checklist confirmed.

## 10. Verification strategy

1. **Static.** `git diff --name-only` compared against the allowed change surface
   (`app/main.py`, `evcc_evopt_scheduler/README.md`, `evcc_evopt_scheduler/DOCS.md`,
   `evcc_evopt_scheduler/CHANGELOG.md`, `evcc_evopt_scheduler/tests/*`); any other path
   blocks integration (`core/SECURITY.md` worker boundary). Baseline checks — secrets,
   dependencies, static analysis — per `core/risk-policy.json`; the dependency check is
   trivially satisfied by the unchanged `requirements.txt` (A-7).
2. **Red.** Tests written first; T2 run; failure output recorded verbatim (A-5).
3. **Green.** Implementation added; T2 rerun; pass recorded, both runs from the same command
   in the same environment (A-4, A-5).
4. **Compatibility.** Route-table and `/api/status` characterization assertions (A-6),
   plus the diff review of the five existing handlers (A-7).
5. **Lint.** T5 (A-10).
6. **Documentation.** Read both REST tables and diff them against §4.2 (A-8, A-9).
7. **Security.** Independent security review against the §7 checklist (A-11).
8. **Evidence.** Every command above recorded in `evidence.md` with timestamp, environment,
   expected, actual, and pointer. An unrunnable or unrun check blocks; it never passes by
   assertion (intent R4).
