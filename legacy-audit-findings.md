# Legacy Audit Run Findings

## Context
- Spec source of truth: `specs/SpecsUploadingLISDatav1.02.docx`
- Working markdown snapshot: `specs/SpecsUploadingLISDatav1.02.clean.md`
- Implementation reviewed: `convertnavbak.py`
- Conversion pipeline: `specs/convert_spec.sh`
- Latest validation report: `specs/build/spec.validation.md` (`Overall status: Pass`)

## Audit Scope Used
- Requirement-to-code alignment review for the available spec baseline (`v1.02`).
- Behavioral review of configuration flow, input validation, conversion, logging, and batch script generation.
- Gap identification for unimplemented or partially aligned items.

## Key Findings

### 1) Version Traceability Ambiguity (High)
- The spec baseline is `Version: 1.02` while code metadata still reports `convertnavbak_v1.13.py`.
- This is valid in your process, but currently not formalized in a mapping artifact, which can confuse audits.

### 2) Config Decision Flow Mostly Compliant (Pass)
- The decision branches in section `1.2 Input` are implemented:
  - user-defined config handling
  - default config update/use
  - no-input + no-default behavior raises clear error/help path

### 3) Input Validation Requirements Mostly Compliant (Pass/Partial)
- `.sql` extension validation is implemented.
- Navicat header tolerance and MySQL source checks are implemented.
- Insert-required rule is enforced (files without inserts fail and processing continues per file).
- Partial: some narrative-level distinctions are collapsed into shared error messages.

### 4) Core Conversion and Output Requirements Largely Compliant (Pass)
- Struct/data split logic present.
- Insert regrouping by `tot_rows` present.
- Struct normalization includes integer/date length cleanup and charset/collate normalization.
- FK check wrappers, commit, and row-count select are present in generated outputs.

### 5) Logging/Status/Excel Flow Compliant (Pass)
- Fixed log filename and rotation behavior implemented.
- Per-file table-like log entries with TI/totrow/new totrow/duration/status implemented.
- Live single-line status overwrite behavior implemented.
- Optional log-to-excel conversion implemented.

### 6) SQL Batch Upload Script Flow Compliant with Minor Interpretation Differences (Pass/Partial)
- `proc=0` and `proc=2` branching flows implemented.
- DB connection test path + bypass path implemented.
- Script generation with mysql restore + error log capture implemented.
- Partial: some interaction wording/order is optimized in code vs prose wording in spec.

### 7) Known Functional Risk to Re-verify
- `3.5 Display Summary` is historically error-prone and should remain a regression target in author UAT.
- Structural validation passes for section shape, but UX formatting expectations should be checked in runtime output tests.

### 8) Deferred Scope is Explicitly TBD
- Spec sections `5` and `6` are still TBD in `v1.02`; no full implementation expected yet.

## Recommended Immediate Actions
1. Create a version mapping record (`Spec -> App`) to remove ambiguity during future audits.
2. Add traceability matrix file for section-level compliance status.
3. Add focused regression tests for `3.5`, `4.2`, and `4.3` interactive/script flows.
4. Keep spec snapshot generation as a release gate before implementation cycles.

## Reusable Prompt / Task Templates

### Prompt: Legacy Audit Run
```text
Run a legacy requirements-vs-code audit using:
- Spec source: specs/SpecsUploadingLISDatav1.02.docx
- Generated markdown: specs/SpecsUploadingLISDatav1.02.clean.md
- Code: convertnavbak.py

Deliver:
1) Findings grouped by severity with compliant/partial/gap status.
2) Concrete recommendations.
3) Action plan with phases and effort.
4) Explicit note of version mapping (spec vs app) and any ambiguity.
```

### Task Checklist: Audit Execution
- [ ] Confirm active spec and code baselines
- [ ] Review each major spec section against code behavior
- [ ] Classify each item: Compliant / Partial / Gap / TBD
- [ ] Capture evidence and risk notes
- [ ] Publish findings and recommendations

## Tracked As
Each finding is now tracked as a GitHub issue under `nelsonym/uploadLISDB`:

- Finding 1 - Version Traceability Ambiguity: addressed by `version-traceability.md` plus issue #9 (mapping-update automation)
- Finding 7 - `3.5 Display Summary` regression risk: issue #1 (and cascading issue #2 for `proc=2`)
- Finding 8 - Deferred sections `5` and `6`: issues #6 and #7 against Spec 1.03 / App 1.14.0
- Recommended action "add traceability matrix file": issue #8 (artifact now at `traceability-matrix.md`)
- Recommended action "regression tests for 3.5, 4.2, 4.3": exercised by SOP v0.3 UAT focus list and `tests/evidence/<app-version>/` scenarios

Other findings (2-6) resolved as compliant in `fresh-audit-findings.md` and recorded in `traceability-matrix.md`.

