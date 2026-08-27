# Evidence: Add pull-request CI gates

## Intent-stage read-only evidence

- Timestamp: `2026-08-27T21:41:13Z`
- Environment: local checkout `/tmp/flow42-dogfood.nEB0XC/evopt`, branch
  `flow42/health-endpoint`, HEAD `626c929536ff059b7331d123b6879b83cf718129`.
- Check: `gh auth status --hostname github.com`
  - Expected: an active authenticated GitHub account for the repository.
  - Actual: authenticated as `stefanriegel`; no credential value is persisted here.
- Check: `shasum -a 256 .flow42/config.yml`
  - Expected: `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793`.
  - Actual: exact match.
- Check: authenticated read-back of
  `https://github.com/stefanriegel/evcc-evopt-scheduler/issues/1#issuecomment-5445071720`
  with `gh api repos/stefanriegel/evcc-evopt-scheduler/issues/comments/5445071720`.
  - Expected: author `stefanriegel`, configuration digest matching the current file,
    canonical comment URL, and recorded approval time.
  - Actual: matched; comment created and last updated `2026-08-27T20:51:20Z`.
- Check: `gh issue view 3 --repo stefanriegel/evcc-evopt-scheduler --json
  number,title,body,author,createdAt,state,url,labels`
  - Expected: open canonical maintenance request at issue 3.
  - Actual: open issue authored by `stefanriegel`, titled "Add pull-request CI for
    deterministic tests", created `2026-08-27T21:39:42Z`.
- Check: `gh pr checks 2 --repo stefanriegel/evcc-evopt-scheduler --json
  name,state,link,bucket,workflow`
  - Expected: determine current PR check state without mutation.
  - Actual: command reported no checks on branch `flow42/health-endpoint`.
- Check: `gh api
  repos/stefanriegel/evcc-evopt-scheduler/commits/626c929536ff059b7331d123b6879b83cf718129/check-runs`
  - Expected: independently count check runs for the current PR head.
  - Actual: `total_count` is `0`; `check_runs` is empty.
- Check: `gh api
  repos/stefanriegel/evcc-evopt-scheduler/commits/626c929536ff059b7331d123b6879b83cf718129/status`
  - Expected: independently count commit statuses for the current PR head.
  - Actual: aggregate state `pending`, `total_count` is `0`, and `statuses` is empty.

No behavior command was run and no red/green claim is made at the intent stage.

## Known gaps

- Specification approval is not yet recorded; no planning or implementation is authorized.
- No CI run exists yet, so red-green CI evidence is necessarily absent.

## Specification-stage read-only evidence

- At `2026-08-27T21:44:00Z`, authenticated `gh api` read-back of comment `5445569991` found author `stefanriegel`, association `OWNER`, canonical issue 3 URL, identical creation/update time `2026-08-27T21:42:54Z`, and digest `3997c3c53877bd7602489de15c6e24bc03bc8ca77729cb84af985de8155c3381`; local SHA-256 matched exactly.
- `.flow42/config.yml` remained at approved digest `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793`.
- Authenticated official tag reads resolved `actions/checkout` v4 to `11d5960a326750d5838078e36cf38b85af677262` and `actions/setup-python` v5 to `a26af69be951a213d495a4c3e4e4022e16d87065`; the specification pins the full SHAs, not moving tags.
- Repository inspection confirmed Python 3.11 in every base image, exact version requirements, the four-module configured compile argv, and the focused standard-library unittest location.

No workflow was created or edited, no CI command was executed, and no red/green CI claim is made at the specification gate.

## Implementation and local verification evidence

- At `2026-08-27T21:48:35Z`, authenticated read-back of specification approval
  comment `5445612927` confirmed author `stefanriegel`, association `OWNER`, canonical
  issue 3 URL, identical creation/update time `2026-08-27T21:47:44Z`, and approved
  digest `ce3f43cf682d186acdb2ad7914ddcbd38350c5e392d8f344b414255dded30537`.
  The local specification hash matched exactly before approval was persisted.
- Plan digest is `7183e161e06c8f937e18fcba3c9cb2db6dd45e3c22357c7f55f4d5342f343301`.
  Medium risk requires no separate plan-approval gate; the single owned implementation
  slice adds only `.github/workflows/ci.yml` plus this work item's lifecycle artifacts.
- Workflow digest is `572e3ac046c5950c4382eca9d6a908f56140376b87e0217d892f7d0a87e551fe`.
  `actionlint .github/workflows/ci.yml` and `git diff --check` both exited 0. A static
  audit found exactly two `uses:` references, both full 40-character SHAs, and no
  `pull_request_target`, write permission, secret reference, dynamic shell command,
  push, schedule, or manual trigger.
- Authenticated reads of the official repositories resolved `actions/checkout` tag `v4`
  to `11d5960a326750d5838078e36cf38b85af677262` and `actions/setup-python` tag `v5` to
  `a26af69be951a213d495a4c3e4e4022e16d87065`, exactly matching the workflow pins.
- A fresh uv-provisioned CPython 3.11.15 virtual environment at
  `/tmp/flow42-ci-gates-seeded.nTjBaN` ran the literal pip install command successfully,
  installed the four unchanged direct requirement pins, ran focused unittest discovery
  with 5 of 5 tests passing in 0.016 seconds, and ran the exact four-module `py_compile`
  argv with exit 0. Generated `__pycache__` directories were removed afterward.
- Integrity hashes remained unchanged: `.flow42/config.yml`
  `f552cbdb894bb35239a6a3134a6803a8ffb5b4adc4b6bf3e60de33ffe8191793` and
  `evcc_evopt_scheduler/requirements.txt`
  `a94141d0a38ca44994a5d50cc15ee69268b809f3e08a632404e8df9c905f5f3e`.
  Pre-existing `.flow42/health-endpoint/` modifications were preserved and are not part
  of this work item.

## Independent security review handoff

Review `.github/workflows/ci.yml` against `spec.md` sections 2 and 4, specifically the
`pull_request` trust boundary, exact `contents: read` permission, absence of secrets and
permission widening, both immutable Action SHAs, `persist-credentials: false`, literal
commands, per-PR concurrency, and the unchanged requirements digest above. No independent
security-review result is claimed yet.

## Independent review and live change-request reconciliation

- At `2026-08-27T22:23:59Z`, independent Orca review task `task_231969fd6920`
  passed with no blocker. The reviewer independently confirmed five tests,
  `py_compile`, `actionlint`, YAML parsing, immutable Action pins, least-privilege
  permissions, and absence of secrets and cache use.
- Authenticated read-only `gh pr view`, pull-review API, `gh pr checks`, and
  head check-runs API reads confirmed PR #2 is open and non-draft at current head
  `17a98ebb85581e0820b54833f6fbeaf002b229fc`. Its sole `Python 3.11` check in
  workflow `CI` completed successfully (Actions run `33120146155`, job
  `98684717028`); GitHub PR reviews remain exactly `[]` and the review decision is
  empty.
- Revision 8 records the independently verified `verifying → pr-ready` transition.
  Because the same PR was already open, revision 9 records `pr-ready → ci-running`
  without any Forge write; `change_request` points to PR #2, `ci_state` is `green`,
  and the next action is `awaiting-current-review`.

## Remaining verification gaps

- The current-head green pull-request run is now independently observable. The earlier
  requirement for an observed temporary red run remains historical specification debt;
  no temporary failure was introduced during this read-only reconciliation.
- GitHub PR reviews are still empty, so review remains pending.
- No commit, push, pull-request creation/update, merge, deployment, release, publication,
  or other Forge write was performed in this implementation run.
