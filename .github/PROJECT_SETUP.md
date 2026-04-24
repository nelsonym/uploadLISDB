# GitHub Tracking Setup - Status and Follow-up

## What is already configured (by Cursor)
- Labels: `feature`, `spec-change`, `clarification`, `uat`, `blocked`, `audit-finding`, `deferred` (plus the default `bug`)
- Milestones:
  - `App 1.13.x (Spec 1.02)` - milestone #1
  - `App 1.14.0 (Spec 1.03 target)` - milestone #2
- Issue templates under `.github/ISSUE_TEMPLATE/`:
  - `feature.yml`
  - `bug.yml`
  - `spec-clarification.yml`
  - `config.yml` - disables blank issues, surfaces the three templates
- Seeded audit-finding issues (see `## Seeded Issues` below)

## Author follow-up: create the GitHub Project v2 "uploadLISDB Delivery"
The `gh` CLI token in the current Cursor environment is missing the `project` scope required to create and manage GitHub Projects v2. Two options:

### Option A - refresh the token once, then let Cursor finish
```bash
gh auth refresh -s project,read:project
```
After this, Cursor can run:
```bash
gh project create --owner nelsonym --title "uploadLISDB Delivery"
```
and then configure columns and custom fields via `gh project field-create` / `gh project edit`.

### Option B - one-time manual web setup
1. Go to https://github.com/users/nelsonym/projects and click `New project`.
2. Choose the `Board` template, name it `uploadLISDB Delivery`.
3. Replace the default columns with: `Backlog`, `Ready`, `In Progress`, `In Review`, `UAT`, `Done`, `Deferred`.
4. Add custom fields mirroring the required issue fields:
   - `Spec Version` (text)
   - `Spec Section` (text)
   - `App Target Version` (text)
   - `Priority` (single-select: P0, P1, P2, P3)
   - `Status` (single-select: reuse column values if desired)
   - `Owner` (assignee-style text or GitHub user field)
   - `Test Evidence URL` (text)
5. Link the `nelsonym/uploadLISDB` repository so issues can be added to the project.

## Required workflow rule
`UAT` is the level-off gate - no issue leaves the `UAT` column without a `Classification` decision recorded in the issue body (spec issue / implementation defect / ambiguity).

## Seeded Issues
The initial seed has been created. See the `Tracked As` footers in `legacy-audit-findings.md` and `fresh-audit-findings.md` for the canonical mapping.

| Issue | Title | Milestone |
| --- | --- | --- |
| #1 | 3.5 Display Summary does not render paired table-like layout | App 1.13.x (Spec 1.02) |
| #2 | 4.3 proc=2 listing must reuse the corrected 3.5 formatter | App 1.13.x (Spec 1.02) |
| #3 | 3.3 log header date/time formatting diverges from spec examples | App 1.13.x (Spec 1.02) |
| #4 | Startup-phase errors not persisted to convertnavbak.log | App 1.13.x (Spec 1.02) |
| #5 | 3.3 log textual examples - normative or illustrative? | App 1.13.x (Spec 1.02) |
| #6 | Section 5 TBD - Check Uploaded Total No of Rows vs Actual | App 1.14.0 (Spec 1.03 target) |
| #7 | Section 6 TBD - Check Foreign Key Value Dependencies | App 1.14.0 (Spec 1.03 target) |
| #8 | Section-level traceability matrix file | App 1.13.x (Spec 1.02) |
| #9 | Version-mapping update automation script | App 1.14.0 (Spec 1.03 target) |
