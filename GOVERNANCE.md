# Governance

MNCS is a lightweight, open, community-developed standard.

## Roles

- **Maintainers** administer the repository and releases.
- **Editors** integrate approved normative text and schemas.
- **Contributors** submit code, evidence, issues, and documentation.
- **RFC authors** own a proposed change through review.
- **Reviewers** provide technical, security, compatibility, and user feedback.

The initial repository owner acts as bootstrap maintainer. The active maintainer and
editor list is recorded in release notes until a dedicated roster RFC is adopted.
Roles are earned through sustained public contribution and may be removed for
inactivity, misconduct, or unmanaged conflict by the same consensus process.

For a release candidate, the editor assembles text, schemas, corpus, implementation
reports, migration material, and the evidence index. The release authority verifies
the checklist and authorizes creation of a tag; the signing authority controls the
release key and signs only that authorized artifact. One person MAY hold more than one
bootstrap role only when the overlap is disclosed. An author or editor MUST recuse from
the independent-review approval of their own contested normative change.

Current bootstrap assignments are deliberately not inferred from commit access:

- active maintainer roster: **OPEN**;
- active editor roster: **OPEN**;
- independent reviewer pool: **OPEN**;
- release authority: **OPEN**; and
- signing authority and custody procedure: **OPEN**.

These OPEN fields block final authorization, but they do not block preparation or
testing of a release candidate.

## Decisions

Work is public and consensus-seeking. Maintainers summarize objections and try to
resolve them with evidence. Normative changes require an RFC, at least two weeks of
public review, and approval from two non-conflicted reviewers when the project has
that many active reviewers. If consensus is impossible, maintainers may record a
reasoned decision and minority view; a single maintainer cannot both author and
finally approve a contested normative change.

## Releases and versions

Editors assemble releases after approved RFCs and passing CI. Standard versions
identify normative semantics; validator packages use semantic versioning. Patch
validator releases preserve schema meaning. Compatible additive standard changes
increment the minor version. Breaking meaning increments the major version.
Experimental extensions do not become core without an RFC and multiple
implementations.

Deprecations require rationale, replacement, transition period, and a stated removal
version. Archived schemas remain addressable. Release tags are annotated and release
notes list accepted RFCs, compatibility, known limitations, and artifact hashes.

## Bootstrap completion

Bootstrap governance is complete only after the project publicly records:

- an active maintainer and editor roster;
- succession, inactivity, removal, and emergency-access rules;
- release and signing authorities;
- an independent reviewer pool or a disclosed inability to form one;
- namespace and project-mark stewardship without a technical veto;
- conflict, funding, employment, and tool-ownership disclosures material to decisions;
- a durable process for changing assurance semantics; and
- an explicit rule that reference validators, analyzers, and providers are
  non-normative implementations.

Until those records exist, the repository owner remains the bootstrap maintainer and
contested normative changes wait when independent review requirements cannot be met.

## Appeals and conflicts

An appeal identifies the decision, process defect, and requested remedy. An
uninvolved maintainer convenes public reconsideration; conduct or security-sensitive
facts may remain private. Participants disclose employment, funding, tool ownership,
or other interests material to a decision and recuse when impartiality is reasonably
in doubt.

A release disclosure records participant, role, employer or sponsor when material,
tool or implementation ownership, financial interest, affected decisions, and
recusal/mitigation. “None known” is an affirmative disclosure; silence is not.

## Succession and inactivity

An active role holder SHOULD respond to role-related public requests within 30 days.
After 90 days without response, another maintainer MAY propose inactive status through
the normal public decision process. Succession requires a public nominee, conflict
disclosure, at least two weeks of review, and the approvals otherwise required for a
governance change. Emergency repository access MAY preserve availability but MUST NOT
approve normative text, sign a release, or bypass recusal. Until an eligible successor
is approved, the affected authority remains OPEN and releases requiring it wait.

## Security and independence

Security reports follow [SECURITY.md](SECURITY.md). Vendor-specific tools may
implement MNCS but receive no privileged normative position. No company may hold a
permanent seat, unilateral veto, trademark veto over technical text, or majority of
required approvals. If participation is too small to meet independent-review rules,
the limitation is disclosed and contested normative changes wait.
