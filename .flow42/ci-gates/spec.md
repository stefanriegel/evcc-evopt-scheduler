# Specification: Add pull-request CI gates

- Work ID: `ci-gates`
- Derived from `intent.md`, digest `3997c3c53877bd7602489de15c6e24bc03bc8ca77729cb84af985de8155c3381`, approved by OWNER `stefanriegel` at 2026-08-27T21:42:54Z and reverified through authenticated `gh` read-back at 2026-08-27T21:44:00Z.
- This specification defines the workflow but does not authorize creating it. Approval is required before planning or implementation.

Approving this specification ratifies decisions D1 through D8 in `decisions.md`.

## 1. Functional requirements

**F1 — Owned change.** The eventual implementation adds exactly `.github/workflows/ci.yml`. Product code, tests, requirements, runtime configuration, documentation, existing Flow42 configuration, and other workflows remain unchanged.

**F2 — Trigger.** Name the workflow `CI`. Trigger only on `pull_request` types `opened`, `synchronize`, `reopened`, and `ready_for_review`. Do not configure `push`, `pull_request_target`, `workflow_dispatch`, schedule, release, deployment, or publication triggers. Provide no secrets.

**F3 — One deterministic job.** Define one job, id `python`, name `Python 3.11`, on `ubuntu-latest`, with `timeout-minutes: 10`. No matrix, service, container, cache, artifact, coverage, release, or deployment behavior is allowed.

**F4 — Runtime and dependencies.** Check out the pull-request merge commit, set up CPython `3.11`, and install only the existing pinned requirements from repository root:

```text
python -m pip install --disable-pip-version-check -r evcc_evopt_scheduler/requirements.txt
```

Do not upgrade pip, add a package, use another requirements source, or modify a dependency file. Python 3.11 matches all current base images in `build.yaml`.

**F5 — Focused tests.** From `evcc_evopt_scheduler`, run exactly:

```text
python -m unittest discover -s tests -p 'test_*.py' -v
```

**F6 — Compilation.** From repository root, run the exact argv represented by `.flow42/config.yml` `commands.lint`:

```text
python3 -m py_compile evcc_evopt_scheduler/app/__init__.py evcc_evopt_scheduler/app/battery_control.py evcc_evopt_scheduler/app/ha_client.py evcc_evopt_scheduler/app/main.py
```

No glob or generated file list may replace these arguments.

**F7 — Direct commands.** F4–F6 are separate literal `run` steps. No `eval`, command substitution, environment-derived command, `sh -c`, `bash -c`, pipe, redirection, `&&`, or `;` is allowed. GitHub's step shell may launch each literal command but must not interpret command composition.

**F8 — Cancellation.** Use workflow-level concurrency:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

This cancels a superseded run for the same pull request without cancelling another pull request.

## 2. Supply-chain and permission requirements

**S1 — Least privilege.** Declare workflow-level permissions exactly:

```yaml
permissions:
  contents: read
```

No job or step may widen permissions. There is no write permission for contents, pull requests, checks, issues, packages, deployments, attestations, or OIDC.

**S2 — Immutable Actions.** Use only these first-party Actions, pinned to the full commit SHAs authenticated from their official repositories on 2026-08-27:

```yaml
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
  with:
    persist-credentials: false
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
  with:
    python-version: "3.11"
```

Moving tags, branches, shortened SHAs, local Actions, Docker Actions, and additional Actions are prohibited. Comments are informational; the SHA is authoritative.

**S3 — Checkout hardening.** `persist-credentials: false` prevents checkout from retaining the job token in Git configuration. Default checkout depth is sufficient.

## 3. Canonical workflow shape

The implementation must be semantically equivalent to this binding structure; only human-readable step names may vary:

```yaml
name: CI

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  python:
    name: Python 3.11
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version: "3.11"
      - run: python -m pip install --disable-pip-version-check -r evcc_evopt_scheduler/requirements.txt
      - run: python -m unittest discover -s tests -p 'test_*.py' -v
        working-directory: evcc_evopt_scheduler
      - run: python3 -m py_compile evcc_evopt_scheduler/app/__init__.py evcc_evopt_scheduler/app/battery_control.py evcc_evopt_scheduler/app/ha_client.py evcc_evopt_scheduler/app/main.py
```

## 4. Threat model

Protected assets are repository contents, the GitHub token, maintainer secrets, and the integrity of the required-check signal. The trust boundary is an untrusted pull request whose code and dependency pins execute on a GitHub-hosted runner.

| Threat | Control | Residual risk |
| --- | --- | --- |
| Pull-request code gains repository write authority | `pull_request`, never `pull_request_target`; only `contents: read`; no widening | Test code executes with the read token needed for checkout |
| Test code reuses checkout credentials | `persist-credentials: false` | GitHub runner internals still broker the read-only token; no secrets are provided |
| A moving Action tag is retargeted | Authenticated full 40-character SHAs | Pinned upstream commits and the hosted runner remain trusted dependencies |
| Dependency install executes compromised code | Only four existing exact version pins | Versions are not hashes; package-index or maintainer compromise remains residual |
| Stale run supersedes contributor feedback | Per-PR concurrency and cancellation | Cancellation is best effort; completed history remains visible |
| Green workflow omits validation | Exact discovery, compile argv, working directory, and red/green evidence | Future tests outside `tests/test_*.py` require a new approved spec |

No repository, organization, or environment secret may be referenced. Independent security review must confirm trigger, permissions, Action SHAs, checkout credential handling, and absence of command construction before change-request readiness.

## 5. Acceptance criteria and evidence

**A1 — Static audit.** Record the workflow digest and parse it to verify only the trigger, permission, concurrency, job, Actions, and commands specified here. Every `uses:` ends in an approved 40-character SHA. `git diff --name-only` contains only `.github/workflows/ci.yml` plus authorized Flow42 artifacts.

**A2 — Integrity.** Record SHA-256 of `requirements.txt` before and after and prove equality. Prove `.flow42/config.yml` remains byte-identical at approved digest `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793`.

**A3 — Local viability.** In a clean Python 3.11 environment, execute the literal install, unittest, and compilation commands and record exit codes and test counts. Local success does not substitute for GitHub CI.

**A4 — Observed red.** On a pull request, make an authorized temporary test-only failure without changing the workflow. Record run URL, run ID, head SHA, workflow path, event `pull_request`, failing job/check, failing command, and conclusion `failure`. Revert it before final review. Cancelled or local failure is insufficient.

**A5 — Observed green.** On the corrected pull-request head, record run URL, run ID, exact head SHA, workflow path, event `pull_request`, job/check `Python 3.11`, and conclusion `success`. Authenticated GitHub read-back must show the check belongs to the same head SHA. Another branch, SHA, event, or workflow is insufficient.

**A6 — Security and scope.** Confirm the event is not `pull_request_target`, no secret is referenced, permissions are read-only, checkout credentials are not persisted, and no product/dependency/config file changed. Record independent security review.

**A7 — Gate discipline.** CI success permits later lifecycle evaluation only after separate intent, specification, implementation, verification, and change-request gates. It does not authorize self-approval, commit, push, PR creation/update, merge, deployment, release, publication, or any Forge write.

## 6. Verification strategy

1. Parse and review YAML; reject any extra trigger, permission, job, Action, or command.
2. Recompute workflow, requirements, config, intent, specification, and plan digests at applicable gates.
3. Run the three literal commands locally on Python 3.11 and preserve concise output.
4. Obtain independently observed red and corrected green pull-request runs from A4/A5.
5. Perform independent security and scope reviews before change-request readiness.
6. Treat absent, queued, skipped, neutral, cancelled, stale-SHA, or unauthenticated CI as not green and stop safely.
