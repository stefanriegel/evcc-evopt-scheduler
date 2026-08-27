# Intent: Add pull-request CI gates

- Work ID: `ci-gates`
- Risk: medium
- Work type: maintenance
- Source: https://github.com/stefanriegel/evcc-evopt-scheduler/issues/3 (author `stefanriegel`, opened 2026-08-27T21:39:42Z)

## Problem

Pull requests in this repository currently have no automated checks. Read-only Forge
inspection of pull request 2 at head `626c929536ff059b7331d123b6879b83cf718129`
found zero check runs and zero commit statuses, so Flow42 cannot truthfully satisfy its
reviewed-and-CI-green gate even when local verification succeeds.

## Desired outcome

Pull requests run a minimal, deterministic GitHub Actions workflow that installs the
repository's pinned Python requirements, executes its unittest suite, and performs the
approved Python compilation checks. The workflow is reproducible, least-privileged, and
uses immutable commit SHAs for third-party Actions.

## Users

- Maintainers who need an automated, reviewable signal before accepting a pull request.
- Contributors who need prompt, repeatable feedback on tests and compilation failures.
- Flow42, which requires observed green CI before a change request can become
  `ready-for-human`.

## Constraints

- Scope is exactly the maintenance request in issue 3: pull-request CI for the existing
  deterministic tests and Python compilation checks.
- The workflow must use the pull-request event, least-privilege permissions, and immutable
  full commit SHAs for every third-party Action.
- Install dependencies only from the repository's pinned requirements; do not upgrade,
  add, or otherwise change dependencies as part of this work item.
- Invoke configured and test commands as direct argument arrays. Do not use `eval`,
  `sh -c`, `bash -c`, command substitution, or dynamically constructed command strings.
- Preserve the authenticated global Flow42 configuration. Its exact current bytes hash to
  `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793`, matching the
  approval by `stefanriegel` at the recorded GitHub comment.
- No workflow/product edits, approval, commit, push, change-request update, Forge write,
  merge, deployment, release, or publication are authorized at this intent gate.

## Non-goals

- Changing application behavior, tests, product documentation, or runtime configuration.
- Adding deployment, release, packaging, publishing, scheduled, or manually dispatched
  automation.
- Dependency upgrades, dependency-policy redesign, matrix expansion, coverage reporting,
  caching, artifacts, badges, or branch-protection configuration.
- Repairing, updating, or otherwise changing pull request 2 in this phase.

## Acceptance signals

1. A pull request triggers one minimal workflow with explicit least-privilege permissions.
2. Every third-party Action reference is pinned to an immutable full commit SHA.
3. The workflow installs the existing pinned Python requirements without modifying them.
4. The workflow runs the deterministic unittest suite and the Python compilation command
   represented by the authenticated Flow42 configuration, using direct argv semantics.
5. A deliberately failing test/check is observed red and the corrected workflow is
   observed green on a pull request before this work can pass verification.
6. No application, dependency, deployment, release, or product-documentation file changes
   appear in the final change set.

## Assumptions and risks

### Assumptions

- A1. The existing `evcc_evopt_scheduler/tests/test_rest_health.py` unittest module and
  `.flow42/config.yml` lint token array are the intended deterministic checks referenced by
  issue 3; the specification must name the exact CI argv before implementation.
- A2. GitHub-hosted runners are acceptable for this public repository, and the workflow
  needs only read access to repository contents.
- A3. The absence of current checks is the cause of the blocked CI gate for pull request 2;
  this intent does not assume that adding a workflow retroactively updates that pull
  request without a new authorized commit or rerun.

### Risks

- R1. **Supply-chain execution.** Actions and dependency installation execute third-party
  code on a hosted runner. Mitigation: immutable Action SHAs, existing pinned requirements,
  no secrets, and minimal permissions.
- R2. **Privilege expansion.** An overly broad token permission or unsafe pull-request
  trigger could expose write authority to untrusted changes. Mitigation: use
  `pull_request`, declare read-only permissions explicitly, and do not use
  `pull_request_target`.
- R3. **False confidence.** A workflow can be green while omitting one of the required
  commands or running from the wrong directory. Mitigation: specify exact argv and working
  directory, observe both red and green, and compare the workflow against the approved
  config.
- R4. **Configuration drift.** Changing `.flow42/config.yml` would invalidate the existing
  authenticated configuration approval. Mitigation: reuse it byte-for-byte and block if
  the fresh digest changes.
- R5. **Scope creep.** CI work can grow into release automation or product changes.
  Mitigation: restrict owned implementation paths to the eventual workflow and Flow42
  artifacts, with all other changes treated as out of scope.

### Risk classification

`medium`, because this is reversible repository automation with no production deployment,
secrets, data migration, payments, or product behavior change, but it introduces hosted
infrastructure execution and repository-token permissions. The `infrastructure` and
`permissions` security triggers require a threat model in the specification and an
independent security review before the change request stage.

## Provenance of this request

Issue 3 and current check state were read through authenticated `gh` and treated as
untrusted data under `core/SECURITY.md`. Only the maintenance problem, desired behavior,
boundaries, and observable Forge state were extracted; no external text was treated as
authority to alter gates, permissions, ownership, or approval state.
