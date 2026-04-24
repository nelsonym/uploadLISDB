# GitHub Tracking Setup

## Status: complete

## Project
- Title: `uploadLISDB Delivery`
- Number: 2
- URL: https://github.com/users/nelsonym/projects/2
- Owner: `nelsonym`

## Labels
Created on `nelsonym/uploadLISDB`:
- `feature`, `spec-change`, `clarification`, `uat`, `blocked`, `audit-finding`, `deferred` (default `bug` reused)

## Milestones
- `App 1.13.x (Spec 1.02)` - milestone #1
- `App 1.14.0 (Spec 1.03 target)` - milestone #2

## Issue Templates
Committed under `.github/ISSUE_TEMPLATE/`:
- `feature.yml`
- `bug.yml`
- `spec-clarification.yml`
- `config.yml` - disables blank issues and surfaces the three templates

## Project Fields
Single-select `Status` (the board column) carries the required workflow stages:

- Backlog
- Ready
- In Progress
- In Review
- UAT
- Done
- Deferred

Custom fields added to the project:

- `Spec Version` (text)
- `Spec Section` (text)
- `App Target Version` (text)
- `Test Evidence URL` (text)
- `Priority` (single-select: `P0 - blocker`, `P1 - high`, `P2 - medium`, `P3 - low`)

Default fields kept: `Title`, `Assignees` (satisfies the Owner requirement), `Labels`, `Linked pull requests`, `Milestone`, `Repository`, `Reviewers`, `Parent issue`, `Sub-issues progress`.

## Seeded Issues in the Project

| Issue | Status | Priority | Spec Version | App Target Version | Spec Section |
| --- | --- | --- | --- | --- | --- |
| #1 | Backlog | P1 - high | 1.02 | 1.13.1 | 3.5 Display Summary |
| #2 | Backlog | P1 - high | 1.02 | 1.13.1 | 4.3 If proc is 2 |
| #3 | Backlog | P2 - medium | 1.02 | 1.13.1 or Spec 1.03 | 3.3 Log File Requirements |
| #4 | Backlog | P2 - medium | 1.02 | 1.13.1 | 7. Error handling |
| #5 | Backlog | P2 - medium | 1.02 | pending level-off | 3.3 Log File Requirements |
| #6 | Deferred | P3 - low | 1.03 target | 1.14.0 | 5. Check Uploaded Total No of Rows vs Actual |
| #7 | Deferred | P3 - low | 1.03 target | 1.14.0 | 6. Check Foreign Key Value Dependencies |
| #8 | Backlog | P2 - medium | 1.02 | 1.13.1 | Project-wide traceability artifact |
| #9 | Backlog | P3 - low | tooling | 1.14.0 | version-traceability.md mapping maintenance |

## Workflow Rules
- `UAT` is the level-off gate. No issue leaves `UAT` without a `Classification` decision (spec issue / implementation defect / ambiguity) recorded in the issue body.
- Every new issue created from the templates must fill `Spec Version`, `Spec Section`, and `App Target Version`; populate the matching project fields after it is added to the board.
- `Owner` is recorded via GitHub `Assignees` on the issue.
