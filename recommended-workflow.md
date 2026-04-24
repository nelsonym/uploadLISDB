# Recommended Workflow (Word Source + Generated Markdown)

## Status
- Status: Ratified
- Ratified Date: 2026-04-24
- Approver: Author (nelsonym)
- Supersedes: prior draft recommendation

## Decision
Use a hybrid workflow:
- **MS Word (`.docx`) remains the source of truth**
- **Generated Markdown (`.clean.md`) becomes the controlled AI working snapshot**
- **Markdown regeneration runs only on explicit author go-signal**

This is the ratified workflow for the project. It keeps the author's preferred editing format while still giving Cursor a fast, diff-friendly artifact for analysis, planning, implementation, and review.

## Recommended Operating Model

### 1) Source of Truth
- The authoritative requirements live in `specs/SpecsUploadingLISDatav1.02.docx` or its next approved version.
- The generated file `specs/SpecsUploadingLISDatav1.02.clean.md` is not the source of truth. It is a controlled projection of the Word spec for AI and repo traceability.
- If Word and Markdown differ, Word wins until the Markdown snapshot is regenerated and validated.

### 2) When to Regenerate Markdown
Regenerate only when all three are true:
- the author finished a meaningful batch of updates
- the author gave the go-signal
- the team is ready to plan, implement, audit, or retest against that baseline

Do not regenerate on every Word edit. That creates churn and weakens traceability.

### 3) Snapshot Discipline
Every regeneration should produce a named baseline for the cycle:
- active spec version
- generated markdown snapshot
- validation report
- implementation backlog derived from that snapshot

Treat the generated Markdown like a release input, not a casual scratch file.

## Why This Is Better Than Word-Only
- Word stays natural for the author and remains the legal/business requirement baseline.
- Markdown is much easier for Cursor to search, diff, cite, and compare during implementation.
- Git history becomes useful at the snapshot level even if the original authoring stays in Word.
- Reviews become faster because requirements, findings, and implementation tasks can point to stable sections in the generated snapshot.

## Standard Workflow

### Phase A: Authoring and Go-Signal
1. The author updates the Word spec.
2. The author classifies the update:
   - requirement or behavior change
   - enhancement or new feature
   - clarification that changes interpretation
   - editorial cleanup only
3. The author decides whether the change is significant enough to regenerate the Markdown snapshot.
4. The author gives the explicit go-signal.

### Phase B: Generate and Validate Snapshot
1. Run `bash specs/convert_spec.sh`.
2. Confirm the expected outputs exist:
   - `specs/SpecsUploadingLISDatav1.02.clean.md`
   - `specs/build/spec.validation.md`
   - `specs/build/spec.validation.json`
3. Confirm validation passes.
4. If preview or structure mismatches still exist, repair the conversion and regenerate.
5. Freeze that generated snapshot as the active implementation baseline for the cycle.

### Phase C: Delta Review and Task Creation
1. Compare the newly approved snapshot with the prior approved snapshot.
2. Convert the delta into tracked work items:
   - feature
   - bug
   - clarification
   - test/update task
3. Every work item must include:
   - spec version
   - spec section(s)
   - target app version or release
   - acceptance criteria
   - owner

### Phase D: Implementation
1. Implement changes on a branch linked to the tracked work item.
2. Keep code changes tied to approved spec sections or approved defect findings.
3. Update tests and regression coverage for impacted behavior.

### Phase E: Testing and Level-Off
1. Cursor runs automated or assisted testing.
2. The author runs manual testing.
3. Every finding must be classified as one of:
   - specification issue
   - implementation bug
   - ambiguity requiring clarification
4. Level-off happens before release so the team agrees whether the fix belongs in the spec, the code, or both.

### Phase F: Release and Traceability Update
1. Release the app change.
2. Update the version mapping record.
3. Record which spec version and sections were implemented, deferred, or partially implemented.
4. Store test evidence references for the release cycle.

## Versioning Policy

### Core Recommendation
Do not try to force the spec version and app version to match numerically. They represent different things and should evolve independently.

### Spec Version
Increment the Word spec version when:
- behavior changes
- requirements change
- a new feature is approved
- a clarification changes expected implementation or testing

Do not increment the spec version for minor wording, formatting, or editorial fixes that do not affect implementation or validation.

### App Version
Increment the application version when released code changes are made, including:
- implementing a new approved requirement
- fixing an implementation bug
- correcting a missed interpretation
- improving an existing feature after test feedback

If code is still being repaired inside the same unfinished working session and no new release candidate is being established, you may keep the same temporary working version. Once you produce the next release candidate or accepted build, increment the app version.

### Recommended Version Format
- Keep the spec version in the document's business format, for example `1.02`, `1.03`, `1.04`.
- Move the app version to a clearer release format, ideally semantic versioning such as `1.13.0`, `1.13.1`, `1.14.0`.

This removes confusion between requirement revisions and code release revisions.

### Required Mapping Rule
Maintain an explicit mapping artifact. Example:
- `Spec 1.02` -> implemented by `App 1.13.0`
- `App 1.13.1` -> bug-fix release against `Spec 1.02`
- `Spec 1.03` -> target baseline for `App 1.14.0`

Without this mapping, future audits will continue to question why the numbers differ.

## Recommended Tracking Platform
Use **GitHub Issues + GitHub Projects** as the default workflow platform.

This is the best starting point because your source code already lives in GitHub, and it keeps requirements, implementation branches, pull requests, and releases in one place.

### Recommended GitHub Setup
- `GitHub Issues` for features, bugs, clarifications, and test findings
- `GitHub Projects` for board and roadmap tracking
- `Milestones` for target app releases
- labels such as `feature`, `bug`, `spec-change`, `clarification`, `uat`, `blocked`
- issue templates for feature, bug, and spec clarification entries

### Required Fields for Every Tracked Item
- Type
- Spec Version
- Spec Section
- App Target Version
- Priority
- Status
- Owner
- Test Evidence link
- Release or milestone

### When to Consider a Different Tool
If later you need cross-team portfolio planning, heavier workflow automation, or non-developer stakeholders managing many parallel initiatives, then evaluate `Jira` or `Linear`. For your current setup, start with GitHub native tools first.

## Minimum Artifacts to Keep in Repo
- `recommended-workflow.md`
- `draft-sop-checklist.md`
- `version-traceability.md`
- generated validation reports in `specs/build/`

Optional but useful later:
- `traceability-matrix.md`
- `release-notes/`
- issue templates for spec clarifications and UAT defects

## Reusable Prompt / Task Templates

### Prompt: Regenerate and Validate Spec Snapshot
```text
Use the Word document as source of truth.
Regenerate markdown and validate automatically:
1) Run specs/convert_spec.sh
2) Confirm validation outputs in specs/build
3) Report pass/fail and blocking issues only
4) If pass, confirm the generated markdown is the active working snapshot
5) If fail, run one repair loop and re-validate
Do not proceed to coding until validation passes.
```

### Prompt: Build Implementation Backlog from Spec Delta
```text
Compare the latest approved markdown spec snapshot with the previous approved baseline.
Generate implementation work items grouped by section:
- Feature tasks
- Bug-fix tasks
- Clarification tasks
- Test/update tasks
Each item must include Spec Version, Section, acceptance criteria, target App Version, and release priority.
```

### Prompt: Classify Test Findings
```text
Review automated and manual test findings and classify each as:
1) specification issue
2) implementation bug
3) ambiguity requiring clarification
For each item, recommend whether to update the spec version, the app version, or both.
```

## Release Cycle Checklist
- [ ] Go-signal received
- [ ] Markdown regenerated
- [ ] Validation pass confirmed
- [ ] Active snapshot frozen for the cycle
- [ ] Work items linked to spec sections
- [ ] Code and tests completed
- [ ] Automated test evidence captured
- [ ] Manual author test completed
- [ ] Findings classified and level-off completed
- [ ] Version mapping updated

