# Decisions: Add lightweight REST health endpoint

For each decision record context, options, decision, rationale, consequences,
actor, timestamp, and the approved artifact hash when applicable.

## D1 — Adopt the GitHub issue scope verbatim as the intent scope

- Context: The work request is https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1,
  authored by `stefanriegel`, requesting `GET /api/health`.
- Options: (a) adopt the issue scope exactly; (b) widen to also restructure `/api/status`;
  (c) narrow to documentation only.
- Decision: (a) adopt the issue scope exactly.
- Rationale: The human request instructed the issue scope be used exactly. The issue text is
  untrusted data under `core/SECURITY.md`; only its scope fields were extracted, and it
  contains no instructions that alter gates, permissions, or approval state.
- Consequences: `/api/status` behavior is a non-goal; any refactor of it needs a separate item.
- Actor: flow42 (agent), on behalf of the requesting human.
- Timestamp: 2026-08-27T20:53:02Z
- Approved artifact hash: pending intent approval.

## D2 — Classify risk as medium with the `networking` security trigger active

- Context: The change adds a new, unauthenticated, network-reachable HTTP route to an
  add-on that binds `0.0.0.0` on the configurable `api_port` (default 7060).
- Options: low / medium / high / critical.
- Decision: medium, with `core/risk-policy.json` security trigger `networking` recorded as
  applicable.
- Rationale: Blast radius is one additive route plus documentation; the change is fully
  reversible by deletion; no authentication, permissions, payments, migrations, or
  production infrastructure change. It is not low, because it enlarges an unauthenticated
  externally reachable surface and therefore carries an information-disclosure failure mode
  if the payload echoes scheduler state.
- Consequences: Plan approval is not mandatory at medium (`workflow.json` routes
  `planning → building` for low/medium). The `networking` trigger means the specification
  must carry a threat-model section and verification must include an independent security
  review per `core/CONTRACT.md`.
- Actor: flow42 (agent).
- Timestamp: 2026-08-27T20:53:02Z
- Approved artifact hash: pending intent approval.

## D3 — Fix the exact response contract, including the literal `Content-Type`

- Context: `intent.md` acceptance signal 1 asks for HTTP 200, `Content-Type: application/json`,
  and "exact payload keys" for a "stable JSON health payload" (assumption A1).
- Options: (a) assert `Content-Type` loosely as `application/json`; (b) assert the exact value
  `aiohttp.web.json_response` emits; (c) set a custom content type on the response.
- Decision: (b). The payload is fixed as `{"status": "ok", "service": "evcc-evopt-scheduler"}`
  and the header as `application/json; charset=utf-8`.
- Rationale: `web.json_response` appends `; charset=utf-8`, observed in this environment
  (`evidence.md`, 2026-08-27T21:00:17Z). A loose assertion would either fail or be weakened to
  a substring check; a custom content type would deviate from the five existing routes. The
  payload literal is the shape `DOCS.md` already advertises, so documentation and code
  converge instead of diverging. Whole-object equality is required so the key set stays
  closed, which is the enforcement mechanism for intent risk R1.
- Consequences: any future addition to the payload — a version, an uptime — fails the test
  and must be an explicit specification change rather than a quiet edit.
- Actor: flow42 (agent).
- Timestamp: 2026-08-27T21:00:17Z
- Approved artifact hash: ratified by approval of `spec.md`, digest recorded in `approvals.yml`.

## D4 — Resolve intent assumption A4 with stdlib `unittest` over the bundled `aiohttp` test utilities

- Context: A4 was left open for the specification. `.flow42/config.yml` records `test: []`,
  the repository has no test suite, and the bare interpreter has neither `pytest` nor
  `aiohttp`. The human directive for this phase requires stdlib `unittest` coverage that uses
  the existing `aiohttp` production dependency, adding no runtime or development dependency.
- Options: (i) add `pytest` and `aiohttp` as dev dependencies plus a `test` command, which
  changes `.flow42/config.yml` and invalidates the configuration approval; (ii) stdlib-only
  coverage that exercises the handler without a live server; (iii) reshape the payload into a
  pure function and test only that.
- Decision: (ii), refined — `unittest` via `aiohttp.test_utils.AioHTTPTestCase`, driving the
  real `aiohttp` application over a loopback test server, with the pinned `requirements.txt`
  installed into a throwaway virtual environment.
- Rationale: `AioHTTPTestCase` ships inside `aiohttp` and subclasses
  `unittest.IsolatedAsyncioTestCase`, both verified here (`evidence.md`, rows 1–3), so the
  standard-library runner drives it with no plugin and no new dependency. Option (i) costs a
  fresh configuration approval. Option (iii) is weaker than it looks: testing a pure payload
  function proves nothing about route registration, so intent risk R3 — regression in the
  five existing routes — would go uncovered. Installing the unmodified `requirements.txt` is
  not dependency growth: no repository file changes and the image's package set is identical.
- Consequences: `AGENTS.md` rule 19 names pytest for tests. The directive overrides the
  runner; the rule's *location* (`evcc_evopt_scheduler/tests`) is honored. The conflict is
  benign because pytest collects `unittest.TestCase` subclasses unmodified, so the tests stay
  pytest-compatible if a runner is adopted later. Running the suite requires a provisioned
  environment; the exact command is fixed in `spec.md` §6 T2, since the empty configured
  `test` command cannot supply it.
- Actor: flow42 (agent), executing the human directive for this phase.
- Timestamp: 2026-08-27T21:00:17Z
- Approved artifact hash: ratified by approval of `spec.md`, digest recorded in `approvals.yml`.

## D5 — Correct the inaccurate `/api/status` documentation as part of this change

- Context: `evcc_evopt_scheduler/DOCS.md:152` documents `/api/status` as returning
  `{"status": "ok", "service": "evcc-evopt-scheduler"}`, which the code has never returned;
  `README.md` calls it "High-level health information". The actual response is the scheduler
  snapshot (`app/main.py:435-440`). The intent's non-goal forbids changing `/api/status`.
- Options: (a) leave both descriptions untouched; (b) correct both descriptions, documentation
  only; (c) change `/api/status` to match its documentation.
- Decision: (b).
- Rationale: (c) is squarely a non-goal and would break existing consumers. (a) is worse after
  this change than before it: the documented payload for `/api/status` would be precisely the
  payload of the new `/api/health`, so a reader would probe the wrong endpoint and get the
  heavy response the issue set out to avoid. A documentation correction changes no behavior,
  so the non-goal — which protects `/api/status`'s paths, methods, and response bodies — is
  untouched, and `AGENTS.md` rules 7 and 21 require documentation to match the implementation.
- Consequences: the diff touches `/api/status` rows in two documentation files. Reviewers must
  confirm no code change accompanies them.
- Actor: flow42 (agent). Contradiction surfaced rather than silently resolved; approval of
  `spec.md` ratifies it.
- Timestamp: 2026-08-27T21:00:17Z
- Approved artifact hash: ratified by approval of `spec.md`, digest recorded in `approvals.yml`.

## D6 — No version bump; changelog entry under `[Unreleased]`

- Context: `CHANGELOG.md` is Keep a Changelog style with per-version sections, and the add-on
  version lives in `evcc_evopt_scheduler/config.yaml`, a `protected_paths` entry.
- Options: (a) bump `config.yaml` `version` and add a numbered changelog section; (b) add an
  `[Unreleased]` section and bump nothing.
- Decision: (b).
- Rationale: (a) edits a protected path, which requires an explicit human decision, and the
  intent authorizes no release, publication, or other irreversible action. Releasing is a
  separate authorization.
- Consequences: the change is unreleased until someone deliberately cuts a version.
- Actor: flow42 (agent).
- Timestamp: 2026-08-27T21:00:17Z
- Approved artifact hash: ratified by approval of `spec.md`, digest recorded in `approvals.yml`.

## D7 — No CI workflow and no `.flow42/config.yml` change in this work item

- Context: the repository has no `.github/` directory and no CI system, and
  `.flow42/config.yml` records `commands.test: []`. Verification needs a test command to run.
- Options: (a) add a CI workflow and register the test command in configuration; (b) register
  only the test command in configuration; (c) change neither, and bind the command through
  the specification instead.
- Decision: (c).
- Rationale: (a) is a first-ever CI pipeline — runner, matrix, and secrets decisions well
  beyond an additive route, and outside the approved intent scope. (b) changes the
  configuration digest and invalidates `config-approval.yml`, blocking execution until fresh
  authenticated approval; that cost is not worth paying inside this item. Under (c) the exact
  command in `spec.md` §6 T2 is binding on the verifier, so an empty configured `test` command
  is not a licence to skip execution.
- Consequences: verification is a locally executed command with output recorded in
  `evidence.md`, not a CI signal. A follow-up work item covering CI plus test-command
  registration is recommended (open item O1) and requires its own intent and approvals.
- Actor: flow42 (agent).
- Timestamp: 2026-08-27T21:00:17Z
- Approved artifact hash: ratified by approval of `spec.md`, digest recorded in `approvals.yml`.

## D8 — Documentation ordering and the `service` value

- Context: two REST tables need a new row, and the payload needs a service identifier.
- Options: append the row last vs. place it first; `service` value from the add-on slug vs.
  the display name vs. omitting the key.
- Decision: `/api/health` is listed first in both tables; `service` is the literal
  `evcc-evopt-scheduler`.
- Rationale: a liveness probe is the entry point a reader looks for first, and listing it
  above `/api/status` steers probes away from the heavy endpoint — the issue's actual goal.
  The slug form matches `config.yaml` `slug` and the value `DOCS.md` already advertises.
  Omitting `service` would leave a monitor unable to tell this add-on from another service on
  a reused port; see threat TM5, where the disclosure is accepted as immaterial next to the
  existing unauthenticated `/api/status` and `/api/metrics`.
- Consequences: the identifier is a fixed literal; changing the slug later leaves it stale
  unless deliberately updated.
- Actor: flow42 (agent).
- Timestamp: 2026-08-27T21:00:17Z
- Approved artifact hash: ratified by approval of `spec.md`, digest recorded in `approvals.yml`.
