# Plan: Add pull-request CI gates

## Vertical slices

### Slice 1 — Add the approved pull-request workflow

- Outcome: pull requests receive one deterministic, read-only Python 3.11 job matching
  the approved specification.
- Dependencies: approved specification digest `ce3f43cf682d186acdb2ad7914ddcbd38350c5e392d8f344b414255dded30537`;
  existing pinned `evcc_evopt_scheduler/requirements.txt`; existing tests and modules.
- Owned files: `.github/workflows/ci.yml` and `.flow42/ci-gates/` lifecycle artifacts.
- Implementation: create the canonical workflow from `spec.md` sections 1–3, using only
  the two approved immutable Action SHAs, `contents: read`, per-PR concurrency, exact
  dependency install, focused unittest discovery, and exact compilation argv.
- Proving tests: `actionlint .github/workflows/ci.yml`; a structural YAML audit; the
  literal install, unittest, and compilation commands in a fresh Python 3.11 virtual
  environment; `git diff --check`; digest and scope audits.
- Branch/worktree: current isolated checkout `/tmp/flow42-dogfood.nEB0XC/evopt` on
  `flow42/health-endpoint`; do not modify or discard the separate health-endpoint work.
- Integration order: workflow first, local static and runtime validation second,
  independent security review next, then stop at `verifying` before any Forge write.
- Rollback: remove only `.github/workflows/ci.yml` and revert this work item's Flow42
  artifacts; no product data, runtime state, or dependency file is migrated.

## Parallelization map

This single-file implementation is intentionally sequential. Independent security review
may inspect the completed workflow after local validation; it must not edit files.

## Integration order

1. Reverify specification approval provenance and approved configuration digest.
2. Persist approval and this plan; medium risk requires no separate plan approval gate.
3. Add the workflow exactly as specified.
4. Run static, scope, integrity, and fresh-environment local checks.
5. Advance to `verifying` and hand evidence to an independent security reviewer.
6. Stop before commit, push, pull-request update, red/green Forge CI, merge, or deploy.

## Risks and rollback

- Untrusted pull-request code executes on a hosted runner: retain `pull_request`, explicit
  `contents: read`, no secrets, and `persist-credentials: false`.
- Supply-chain drift: allow only the two approved 40-character Action SHAs and unchanged
  exact-version requirements.
- False-green checks: preserve literal command arguments and working directories, validate
  their workflow structure locally, and require later observed red/green PR evidence.
- Scope collision: preserve all pre-existing health-endpoint changes and restrict this
  implementation to the workflow plus `.flow42/ci-gates/`.
