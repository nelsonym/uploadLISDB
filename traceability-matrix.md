# Traceability Matrix

## Purpose
Canonical per-section compliance snapshot linking the approved spec baseline to the released app, audit evidence, and tracked issues. Regenerate or update whenever the active spec baseline, app version, or audit classification changes.

## Active Baseline
- Spec Version: `1.02`
- Markdown Snapshot: `specs/SpecsUploadingLISDatav1.02.clean.md`
- Snapshot Date: `2026-04-23`
- App Version: `1.13.0`
- Validation Report: `specs/build/spec.validation.md` (Overall status: Pass)
- Companion Audits: `legacy-audit-findings.md`, `fresh-audit-findings.md`

## Matrix

| Section | Title | Compliance | App Version Verified | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Input | Pass | 1.13.0 | `fresh-audit-findings.md` row `1. Input` |
| 2 | Input Validation | Pass | 1.13.0 | `fresh-audit-findings.md` row `2. Input Validation` |
| 3.1 | Table Creation - Struct Output File Naming | Pass | 1.13.0 | `fresh-audit-findings.md` row `3.1 Table Creation - Struct Output File Naming` |
| 3.2 | Insert Statement | Pass | 1.13.0 | `fresh-audit-findings.md` row `3.2 Insert Statement` |
| 3.3 | Log File Requirements | Partial | 1.13.0 | `fresh-audit-findings.md` row `3.3 Log File Requirements`; issues #3 (bug) and #5 (clarification) |
| 3.4 | Processing status display | Pass | 1.13.0 | `fresh-audit-findings.md` row `3.4 Processing status display` |
| 3.5 | Display Summary | Partial | 1.13.0 | `fresh-audit-findings.md` row `3.5 Display Summary`; issue #1 |
| 3.6 | Convert logfile to excel file | Pass | 1.13.0 | `fresh-audit-findings.md` row `3.6 Convert logfile to excel file` |
| 4.1 | proc is 0 | Pass | 1.13.0 | `fresh-audit-findings.md` row `4.1 proc is 0` |
| 4.2 | MySQL DB Connection test | Pass | 1.13.0 | `fresh-audit-findings.md` row `4.2 MySQL DB Connection test` |
| 4.3 | If proc is 2 | Partial | 1.13.0 | `fresh-audit-findings.md` row `4.3 If proc is 2`; issue #2 |
| 4.4 | Generate SQL Batch Upload Script File | Pass | 1.13.0 | `fresh-audit-findings.md` row `4.4 Generate SQL Batch Upload Script File` |
| 5 | Check Uploaded Total No of Rows vs Actual | TBD | n/a | Deferred to Spec 1.03; issue #6 |
| 6 | Check Foreign Key Value Dependencies | TBD | n/a | Deferred to Spec 1.03; issue #7 |
| 7 | Error handling | Partial | 1.13.0 | `fresh-audit-findings.md` row `7. Error handling`; issue #4 |
| 8 | Leveling Off | Not auditable in code | n/a | Process requirement - exercised via SOP level-off flow |
| 9 | Development and Testing Environment | Not auditable in code | n/a | Environment requirement - exercised via SOP handoff protocol |

## Compliance Legend
- `Pass` - implementation matches the spec section for the listed app version.
- `Partial` - implementation covers core behavior but has a presentation or edge-case gap; a tracked issue exists.
- `Gap` - required behavior is missing and a tracked issue exists.
- `TBD` - spec section is explicitly marked `TBD`; no implementation expected yet.
- `Not auditable in code` - process or environment requirement rather than runtime behavior.

## Update Rules
- Update this file at the end of every release cycle before cutting release notes.
- Change the App Version Verified column only after automated tests and author UAT both sign off for that section.
- Add a new snapshot section at the top when the active baseline changes (new spec version or new app minor release).

## Release Statement
`App 1.13.0 implements Spec 1.02. Known deferred sections: 5, 6. Known partial sections: 3.3, 3.5, 4.3, 7.`
