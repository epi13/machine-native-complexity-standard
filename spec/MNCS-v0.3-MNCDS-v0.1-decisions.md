# MNCS 0.3 / MNCDS 0.1 release-candidate decisions

Status: decision-ready evidence for Draft RFCs 0004 and 0005. External review and
governance approval remain required.

| Issue | Alternatives | Selected rule | Compatibility, security, migration, tests | External requirement |
|---|---|---|---|---|
| MNCS core | Every Wave; extend 0.2 manifest; small family | Contract, assurance/lifecycle, threat, measurement | 0.2 frozen; RC corpus and two consumers | RFC 0005 approval |
| MNCDS core | Many subrecords; guidance; aggregate | One offline-resolvable aggregate | Draft preserved; migration creates identity | RFC 0004 approval |
| Experimental scope | Promote language/provider/Waves | Keep language profiles, MNEA, providers, Waves experimental | Tools/cases stay non-normative | Review |
| Contract adequacy | Optional; manifest fields; required | Required for new 0.3 claims | Historical claims unchanged; focused fixtures | Domain review per claim |
| Ambiguity | Always FAIL; always UNKNOWN | Contradiction/violation FAIL; unresolved material ambiguity UNKNOWN | Preserves uncertainty without accepting circularity | RFC approval |
| Contract change | Reuse ID; always new | Changed bytes new content ID; material semantics new logical ID and impact | No historical rewrite | RFC approval |
| Composition | Flat; adopter-only; graph | Acyclic required/optional claim graph | Tests propagation/cycles/shared evidence | Domain policy may be stricter |
| Correlation | Free text; universal taxonomy | Identified group/source/members | Concealment regression fixtures | RFC approval |
| Mixed versions | Normalize | Preserve exact level/profile/version | Prevents downgrade/promotion | RFC approval |
| Revalidation | Always full; unrestricted partial | Partial only over complete impact closure/fresh evidence | Insufficient scope UNKNOWN | Domain freshness policy |
| Invalidation | Artifact only; external | Ten identity dimensions plus custody | Material/non-material and stale fixtures | RFC approval |
| Freshness | Universal duration; none | Explicit expiry or identified no-default policy | Avoids universal unevidenced duration | Domain defaults |
| Lifecycle | Mutate claim; immutable events | Supersession/replacement/rollback/retirement; replacement new ID | Retired claim cannot support current PASS | RFC approval |
| Combined presentation | Score; separate files | One case, separate MNCS/MNCDS, no score | Collapse attempt invalid | RFC approval |
| Disposition | Third score; omit | Separate policy decision with no status | Review-required cannot become PASS | RFC approval |
| Criticality | Universal mapping; prose | Portable facts, external identified mapping | Avoids unsafe universal policy | Adoption evidence |
| Independence | Language difference; assertion | Separate implementation/executable/operator/organization facts | Code proves first two only | External actors |
| Unsupported | FAIL; omit; PASS | `UNSUPPORTED` boundary, required `UNKNOWN` | Both consumers test it | RFC approval |
| Migration | Auto-upgrade; invalidate | Wrap or reevaluate; missing facts UNKNOWN | 0.1/0.1.1/0.2/draft frozen | RFC approval |
| D3 | Organization required; identity only | Authority/executable separation, reviewer, fresh/protected evidence | Technical boundary locally testable | Organization remains external |
| Candidate retention | All bytes; aggregates | Material candidates individual; pre-material audited aggregate | Cycles/parents/disposition/aggregate tests | RFC approval |
| Recursive improvement | Forbid; unrestricted | Versioned epochs, fresh final partition, retained regressions | Two-epoch study | Independent review |

Every selected rule has a local schema, semantic, corpus, migration, or documentation
obligation. External actor and governance obligations remain open.
