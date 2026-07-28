# RFC 0006: Experimental language evidence profiles

- Status: Draft
- Scope: Experimental, non-normative
- Does not modify: MNCS 0.2 or MNCDS 0.1-draft

## Summary

Introduce versioned language evidence profiles that describe how bounded evidence is collected for
a programming language environment. Profiles do not redefine MNCS levels, MNCDS profiles, Provider
Protocol 0.1, or validator interoperability. They make language-specific evidence assumptions and
UNKNOWN conditions explicit while keeping final observations in common categories.

## Decision

Wave One adds C11, Rust, and Python profiles, bounded replaceable providers, a provider conformance
corpus, a shared C11/Rust stream contract, and a CacheForge Python-profile amendment. The model uses
“profile-valid,” “provider-conformant,” and “evidence-supported.” It forbids claims that a language
or analyzer is MNCS certified.

## Compatibility

All additions live under experimental schema identifiers and new evidence identities. Frozen MNCS
and MNCDS schemas and historical case-study evidence are unchanged. Offline validators do not
execute providers. Provider execution remains explicit through existing Provider Protocol commands
or repository developer targets.

## Open questions

- How should macro-expanded and conditionally compiled subjects be packaged?
- Which environment observations are mandatory for accelerator-backed Python evidence?
- How should multiple disagreeing providers be aggregated without erasing disagreement?
- What independent reproduction threshold should promote a language profile from experimental?
