# Engineering Standards and 5-Batch Standardization Plan

This plan standardizes the repository **folder by folder** so future development and maintenance stay predictable.

## Objectives

- Apply one quality baseline across backend, tests, infra, mobile, and UI.
- Make onboarding easier with explicit standards and done criteria.
- Reduce regressions by requiring checks, ownership, and review gates.

## Global standard practices (apply to every batch)

1. **Definition of Done (DoD)**
   - Code merged with tests and docs updated.
   - Linting and type checks passing.
   - No TODO/FIXME without linked issue.
2. **Documentation first-class**
   - Update docs in same PR when behavior, config, scripts, or architecture changes.
3. **Small, focused PRs**
   - Prefer single-purpose PRs with clear risk and rollback notes.
4. **Quality gates**
   - CI must pass before merge.
   - New behavior requires tests.
5. **Security and secrets hygiene**
   - No secrets in code.
   - Use `.env.example` for config shape only.

## 5-batch rollout (folder-by-folder)

### Batch 1 — Repository governance and automation

**Folders/files in scope**
- `.github/`
- Root-level docs and configs (`README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `.editorconfig`, `.gitignore`)

**Standardization checklist**
- Align contribution flow and review expectations.
- Enforce consistent formatting/lint/type/test jobs in CI.
- Ensure issue/PR templates match expected quality bar.
- Add or verify ownership map (maintainers/reviewers).

**Done when**
- A contributor can follow docs end-to-end without tribal knowledge.
- CI checks are explicit, reproducible locally, and required in PRs.

---

### Batch 2 — Backend application standards

**Folders in scope**
- `src/flipflow/api/`
- `src/flipflow/core/`
- `src/flipflow/infrastructure/`
- `src/flipflow/cli/`

**Standardization checklist**
- Enforce module boundaries (API → core → infrastructure).
- Add docstrings and typing for public interfaces.
- Normalize error handling and logging strategy.
- Consolidate configuration loading and validation patterns.
- Ensure service-level tests cover critical flows.

**Done when**
- Public interfaces are typed and documented.
- Error classes and log format are consistent across modules.
- Critical business paths are covered by tests.

---

### Batch 3 — Data and test reliability standards

**Folders in scope**
- `tests/unit/`
- `tests/integration/`
- `tests/api/`
- `alembic/`

**Standardization checklist**
- Harmonize test naming, fixtures, and directory conventions.
- Define a stable test data strategy (factories/fixtures).
- Verify migration scripts are deterministic and reversible.
- Add guidance for writing integration tests with isolated state.

**Done when**
- Tests are easy to locate by behavior.
- New migrations include upgrade/downgrade checks.
- Flaky tests are tracked and reduced.

---

### Batch 4 — Mobile app standards

**Folders in scope**
- `flipflow-android/app/`
- `flipflow-android/components/`
- `flipflow-android/lib/`
- `flipflow-android/assets/`

**Standardization checklist**
- Standardize component structure and naming.
- Define state, data fetching, and error UI conventions.
- Ensure screen-level loading/empty/error states are consistent.
- Document build, lint, test, and release steps.

**Done when**
- Developers can add a screen with a predictable pattern.
- Common UI states are consistent across app surfaces.

---

### Batch 5 — UI prototypes and design handoff standards

**Folders in scope**
- `ui/`

**Standardization checklist**
- Normalize file naming and screen metadata.
- Keep prototype HTML/CSS structure reusable.
- Add clear mapping from prototype screens to product features.
- Establish screenshot/update workflow for visual changes.

**Done when**
- Prototypes are understandable without verbal context.
- New visual updates follow a repeatable handoff format.

## Execution cadence

- Run batches sequentially (1 → 5).
- Keep each batch as one epic with small sub-PRs.
- Close each batch with a short retrospective:
  - What changed.
  - Remaining gaps.
  - Next batch kickoff decisions.

## Tracking template (use per batch)

- **Owner:**
- **Start date:**
- **Target completion:**
- **Scope:**
- **Checklist status:**
- **Risks/blockers:**
- **Completion notes:**
