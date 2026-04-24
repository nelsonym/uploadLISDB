# Draft SOP Checklist (v0.3)

## Purpose
Provide a repeatable operating procedure for:
- Word specification updates
- Markdown regeneration and validation
- planning and implementation traceability
- automated and manual testing
- version mapping and release readiness

## Roles
- **Author**: owns the Word specification, approves requirement changes, gives go-signal, performs manual testing
- **Cursor/Agent**: regenerates Markdown, validates, plans, implements, tests, and updates traceability artifacts
- **Shared responsibility**: level-off of findings and release signoff

## SOP Checklist

### 1) Spec Change Intake
- [ ] Author updates the active Word specification (`specs/SpecsUploadingLISDatavX.YY.docx`)
- [ ] Change type is classified:
  - [ ] new feature
  - [ ] enhancement
  - [ ] clarification affecting interpretation
  - [ ] editorial only
- [ ] Spec sections affected are listed
- [ ] Go-signal is explicitly given for regeneration
- [ ] Spec version decision is documented

#### Legacy Baseline Check (before opening issues)
- [ ] Review `legacy-audit-findings.md` for known unresolved items still in scope
- [ ] Review `fresh-audit-findings.md` for partial-compliance sections still open
- [ ] Confirm new findings from this cycle do not duplicate existing tracked issues
- [ ] Any overlap with legacy findings is annotated in the new issue body

### 2) Generate and Validate Markdown Snapshot
- [ ] Run `bash specs/convert_spec.sh`
- [ ] Confirm generated Markdown exists (`specs/*.clean.md`)
- [ ] Confirm validation outputs exist in `specs/build/`
- [ ] Confirm validation overall status is pass
- [ ] Review preview/layout mismatches if any remain
- [ ] If needed, run one repair loop and re-validate
- [ ] Freeze the generated Markdown snapshot for the cycle

### 3) Create Traceable Work Items
- [ ] Compare current approved snapshot against prior approved baseline
- [ ] Create or update tracked items for every meaningful delta
- [ ] Each work item contains:
  - [ ] issue type
  - [ ] spec version
  - [ ] spec section(s)
  - [ ] target app version or milestone
  - [ ] acceptance criteria
  - [ ] owner
  - [ ] priority
- [ ] Deferred items are explicitly marked and justified

### 4) Implementation
- [ ] Branch or workstream is linked to the tracked item
- [ ] Code changes are limited to approved work items
- [ ] Tests are added or updated where valuable
- [ ] Regression focus is applied to impacted sections such as summary display and upload flows
- [ ] Work is ready for automated validation

### 5) Automated Testing
- [ ] Cursor or automation test run is completed
- [ ] Test artifacts, input files, logs, and output evidence are captured
- [ ] DB credentials or environment prerequisites used in testing are documented securely
- [ ] Findings are summarized per work item

#### Required Automated-Test Inputs
- [ ] Sample Navicat SQL dumps staged (cover variants observed in production)
- [ ] Sample `.ini` config file staged (both user-defined and default-config scenarios)
- [ ] DB credentials supplied out-of-band and never committed
- [ ] Credential files respect the existing `.gitignore` entries (`*.cred`, `*.pem`) - verified by `git status` showing no tracked credential file
- [ ] Credentials purged from any log or stdout artifact before the evidence is stored

### 6) Manual Testing and Level-Off
- [ ] Author manual test is completed
- [ ] Manual findings are captured with evidence
- [ ] Each finding is classified as:
  - [ ] specification issue
  - [ ] implementation defect
  - [ ] ambiguity requiring clarification
- [ ] Level-off decision is recorded
- [ ] Agreed follow-up action is assigned

#### Mandatory UAT Focus (until resolved)
- [ ] `3.5 Display Summary` renders a paired table-like `Input SQL File` vs `Output` layout
- [ ] `4.3 proc=2` listing reuses the fixed `3.5` formatter
- [ ] `3.3 Log File` header date/time presentation is confirmed against spec examples
- [ ] Startup-phase failures (missing input, bad config) are recorded in `convertnavbak.log`

### 7) Versioning Decision
- [ ] Decide whether the spec version changes
- [ ] Decide whether the app version changes
- [ ] Confirm whether the current build is a new release candidate or a patch against the same spec baseline
- [ ] Update the spec-to-app mapping artifact

### 8) Release Readiness
- [ ] Release notes summarize implemented sections and known gaps
- [ ] Test evidence references are attached
- [ ] Open blockers are resolved or explicitly deferred
- [ ] Release approval is recorded

### 9) Audit Cadence
- [ ] Quarterly legacy audit rerun is scheduled using the prompt template in `legacy-audit-findings.md`
- [ ] A fresh audit is executed on every new approved spec baseline before cutting the corresponding app release candidate
- [ ] Each audit produces a dated file (for example `fresh-audit-findings-<spec-version>.md`) or updates the existing fresh audit with a dated revision header
- [ ] Audit deltas are converted into GitHub issues using the `audit-finding` label

## Operating Rules

### Rule 1: Word Wins
- [ ] Word remains the authoritative requirement source
- [ ] Markdown is a controlled working snapshot only

### Rule 2: No Coding on Unapproved Snapshot
- [ ] Coding does not start until the regenerated Markdown snapshot passes validation

### Rule 3: Every Finding Must Be Classified
- [ ] No defect remains unclassified between spec issue, code issue, or ambiguity

### Rule 4: Version Numbers Must Be Mapped
- [ ] The team never assumes spec version and app version should numerically match
- [ ] Every release must state which spec version it implements

## Tracking Setup (GitHub - Concrete Configuration)

### Labels (create once per repo)
- [ ] `feature` - new approved requirement or enhancement
- [ ] `bug` - implementation defect
- [ ] `spec-change` - requires Word spec update and new spec version
- [ ] `clarification` - ambiguity requiring author decision
- [ ] `uat` - finding raised during author manual testing
- [ ] `blocked` - work cannot proceed until another item resolves
- [ ] `audit-finding` - originated from legacy or fresh audit report
- [ ] `deferred` - acknowledged but out of scope for the current release

### Milestones (create per release target)
- [ ] `App 1.13.x (Spec 1.02)` - current maintenance milestone
- [ ] `App 1.14.0 (Spec 1.03 target)` - next feature milestone

### Issue Templates under `.github/ISSUE_TEMPLATE/`
- [ ] `feature.yml` - fields: Spec Version, Spec Section, App Target Version, Acceptance Criteria, Priority, Owner, Test Evidence URL
- [ ] `bug.yml` - fields: Spec Version, Spec Section, App Version Observed, Repro Steps, Classification (spec issue / implementation defect / ambiguity), Evidence
- [ ] `spec-clarification.yml` - fields: Spec Version, Spec Section, Question, Proposed Resolution, Decision

### Project "uploadLISDB Delivery"
- [ ] Columns: `Backlog`, `Ready`, `In Progress`, `In Review`, `UAT`, `Done`, `Deferred`
- [ ] Custom fields mirror the required issue fields (Spec Version, Spec Section, App Target Version, Priority, Status, Owner, Test Evidence URL)
- [ ] `UAT` column is the level-off gate - no issue leaves UAT without a classification decision

### Required Fields for Every Tracked Item
- [ ] Type
- [ ] Spec Version
- [ ] Spec Section
- [ ] App Target Version
- [ ] Priority
- [ ] Status
- [ ] Owner
- [ ] Test Evidence URL

## Reusable Prompt Templates

### Prompt: SOP Run - Intake to Planning
```text
Execute SOP phases 1 to 3:
1) Confirm go-signal and active Word spec version
2) Regenerate markdown via specs/convert_spec.sh
3) Validate outputs and report pass/fail
4) Compare against the prior approved baseline
5) Produce traceable work items linked to spec sections and target app version
Stop for approval before implementation.
```

### Prompt: SOP Run - Implementation to Release
```text
Execute SOP phases 4 to 8:
1) Implement approved work items
2) Run automated testing and capture evidence
3) Record manual testing findings
4) Classify every finding as spec issue, implementation defect, or ambiguity
5) Update spec/app versions and the mapping artifact
6) Produce a release-readiness summary with evidence and open risks
```

### Prompt: Classify a New Finding
```text
Given a failed test or manual finding, determine:
1) whether it is a spec issue, code issue, or ambiguity
2) whether the spec version should change
3) whether the app version should change
4) what evidence should be attached to the tracked item
```

## Weekly Review Checklist
- [ ] Confirm active spec baseline
- [ ] Confirm active app baseline
- [ ] Review open clarifications
- [ ] Review unresolved bugs
- [ ] Review manual test findings awaiting level-off
- [ ] Review readiness for next regeneration go-signal

## Testing Artifact Handoff

### Provided by the Test Sponsor (user/author)
- [ ] Sample `.sql` dumps covering the production Navicat variants:
  - [ ] variant A - standard Navicat export header
  - [ ] variant B - alternative Navicat header variant encountered in production
  - [ ] variant C - insert-only file (no `CREATE TABLE`)
  - [ ] variant D - file with non-`.sql` extension (negative test)
- [ ] Sample `.ini` config file for both scenarios:
  - [ ] user-defined config (fully populated)
  - [ ] empty / missing-field config (to exercise prompt path)
- [ ] Target MySQL connection details (host, port, schema, user) - transmitted out-of-band
- [ ] DB test credentials (password) - transmitted out-of-band via an agreed secure channel

### Credential Handling Rules
- [ ] Credential files are stored under the already-gitignored path patterns (`*.cred`, `*.pem`)
- [ ] Credentials are never echoed to stdout, pasted into commit messages, or included in PR descriptions
- [ ] Evidence artifacts are scrubbed of credentials before archival (grep the text artifact for host/user/password values)
- [ ] A fresh credential rotation is requested after the test cycle closes if any leakage risk is identified

### Scenarios Cursor Runs (Automated)
- [ ] `proc=0` without DB connection test
- [ ] `proc=0` with DB connection test (success)
- [ ] `proc=0` with DB connection test (failure, bypass path)
- [ ] `proc=2` on pre-generated insert files
- [ ] Insert-only input file
- [ ] Navicat header variant A, B, C
- [ ] Bad-extension file (negative test)
- [ ] Missing required input (startup error path)

### Evidence Folder Layout
```
tests/
  evidence/
    <app-version>/
      <scenario>/
        input/
        output/
        logs/
        summary.md
```

- [ ] Each scenario folder contains: inputs used (or references), generated outputs, `convertnavbak.log` (sanitized), console transcript, and a short `summary.md` stating pass/fail and observations
- [ ] The evidence folder root is committed; actual `.sql`, `.ini`, and credential files stay gitignored and are linked or described by hash/filename only

### Scenarios the Author Runs (Manual UAT)
- [ ] Full UAT focus list from section 6
- [ ] Free-form exploratory testing
- [ ] Findings are filed as GitHub issues labeled `uat` with evidence attached or linked

