For additional context about project rules, read `.specify/memory/constitution.md`
first.

## Original Assignment

For more details on the original assignment, read `original_assignment.md`.

<!-- SPECKIT START -->

For the active feature's technologies, project structure, shell commands, and
implementation details, read `specs/005-invoice-matching/plan.md`.

<!-- SPECKIT END -->

## Git workflow — follow on every change

### Before writing any code

- Confirm a GitHub Issue exists. If not, stop and ask.
- Create branch from `main`:
  - New capability → `feat/NNN-short-description`
  - Bug fix → `fix/NNN-short-description`
  - NNN = GitHub Issue number, zero-padded to 3 digits (e.g. `feat/001-po-lifecycle`)

### Commits

- One conventional commit type per commit — never mix
- Format: `<type>(<scope>): <description>`
- Allowed types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
- Examples:
  ```
  feat(po): add partial goods receipt accumulation
  fix(invoice): correct received_value calculation on 3-way match
  chore(deps): pin fastapi to 0.115.0
  docs(readme): add MCP server setup instructions
  refactor(gl_service): extract account lookup to helper function
  test(invoice): add match endpoint contract test
  ```
- Commit after each logical unit — never batch unrelated changes in one commit

### Every PR must include

- `CHANGELOG.md` entry under the correct version heading (merge gate — no exceptions)
- PR title: `<type>(<scope>): <description> [#NNN]`
- Squash merge if more than one commit

### CHANGELOG.md format (Keep a Changelog)

```markdown
## [Unreleased]

### Added

- POST /invoices/{id}/pay to complete PO lifecycle and transition PO to CLOSED [#NNN]

### Fixed

- 3-way match now correctly accumulates partial receipts across multiple GoodsReceipts [#NNN]
```

### Milestone tags — on `main` after merge only

```
v0.1.0  Phase 1 complete — vendor management working
v0.2.0  Phase 2 complete — PO lifecycle working
v0.3.0  Phase 3 complete — invoice matching working
v1.0.0  All phases green, interview-ready
```

Never tag on a feature branch. Tags go on `main` after the squash merge.

### Release tag bump rule

- After a PR is squash-merged to `main`, decide whether that merge earns a release tag.
- If it earns a release tag, create the tag on the `main` merge commit only.
- Bump the tag using Semantic Versioning:
  - `MAJOR` for breaking or interview-reset milestones that intentionally redefine the public contract
  - `MINOR` for the next completed feature phase or materially new capability
  - `PATCH` for post-release fixes, corrections, or non-breaking behavior changes on an already tagged phase
- Do not skip or reuse version numbers. If a tag was placed on the wrong commit, move it immediately and document the correction in the PR or follow-up commit.
- Current phase mapping in this repo is fixed as:
  - `v0.1.0` vendor management
  - `v0.2.0` PO lifecycle
  - `v0.3.0` invoice matching
