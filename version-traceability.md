# Version Traceability

## Purpose
Remove ambiguity between:
- the specification version in Word
- the generated Markdown snapshot used by Cursor
- the released application version

This file is the required mapping record for audits, release readiness, and regression planning.

## Core Rule
The specification version and application version are independent and must not be expected to match numerically.

## Recommended Version Rules

### Specification Version
Increment the spec version when the approved Word document changes behavior, requirements, feature scope, or implementation-relevant clarification.

Do not increment the spec version for purely editorial fixes.

### Application Version
Increment the app version when released code changes are made:
- new implementation
- bug fix
- behavior correction after testing
- improvement to an existing implemented feature

Recommended app format: semantic versioning such as `1.13.0`, `1.13.1`, `1.14.0`.

## Mapping Entry Template
Create one entry per approved release candidate or release.

### Entry
- Spec Version:
- Markdown Snapshot:
- Snapshot Date:
- App Version:
- Status: planned / in progress / tested / released
- Implemented Sections:
- Deferred Sections:
- Related Issues:
- Automated Test Evidence:
- Manual Test Evidence:
- Notes:

## Current Working Example

### Example A
- Spec Version: `1.02`
- Markdown Snapshot: `specs/SpecsUploadingLISDatav1.02.clean.md`
- Snapshot Date: `2026-04-23`
- App Version: `1.13.0`
- Status: tested
- Implemented Sections: `1`, `2`, `3`, `4` except explicitly deferred items
- Deferred Sections: `5`, `6` (marked `TBD` in Spec `1.02`)
- Related Issues: filled after initial GitHub Issues seed (see `## Related Issues` footer below)
- Automated Test Evidence: `specs/build/spec.validation.md` (Overall status: Pass)
- Manual Test Evidence: `TBD until author UAT completes`
- Notes: `Version numbers differ because the code release history continued across multiple implementation fixes while the approved spec baseline remained at 1.02.`

### Example B
- Spec Version: `1.03`
- Markdown Snapshot: `specs/SpecsUploadingLISDatav1.03.clean.md`
- Snapshot Date: `TBD`
- App Version: `1.14.0`
- Status: planned
- Implemented Sections: `TBD`
- Deferred Sections: `TBD`
- Related Issues: `TBD`
- Automated Test Evidence: `TBD`
- Manual Test Evidence: `TBD`
- Notes: `Next planned release aligned to the next approved spec baseline.`

## Decision Guide

### If Testing Finds a Spec Issue
- update the Word spec
- increment the spec version if behavior or expected interpretation changes
- regenerate Markdown after go-signal
- create or update the linked issue

### If Testing Finds an App Bug
- fix the code
- increment the app version when the next release candidate or release is produced
- keep the same spec version if the requirement did not change

### If Testing Finds Ambiguity
- level-off with the author
- decide whether the clarification changes expected behavior
- if yes, update the spec and version accordingly

## Minimum Release Statement
Every release note or audit summary should contain a plain statement such as:

`App 1.13.1 implements Spec 1.02 and includes fixes confirmed during automated and manual testing.`

## Release Statement Template
Copy this one-liner into every release note and audit summary, substituting actual values:

`App <semver> implements Spec <X.YY>. Known deferred sections: <comma-separated list or "none">.`

## Related Issues
Populated from the initial GitHub Issues seed against `nelsonym/uploadLISDB`.

- Example A (`Spec 1.02` / `App 1.13.0` maintained into `1.13.1`): issues #1, #2, #3, #4, #5, #8
- Example B (`Spec 1.03` / `App 1.14.0`): issues #6, #7, #9

See `traceability-matrix.md` for the per-section compliance view and the canonical issue linkage per spec section.
