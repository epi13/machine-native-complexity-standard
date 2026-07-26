# Extension process

New core fields or meanings require an RFC and standard-version review. Experimental
data uses namespaced extension keys. An extension:

1. MUST name an accountable namespace owner;
2. MUST document schema and semantics;
3. MUST preserve core validation;
4. MUST NOT reinterpret PASS, FAIL, UNKNOWN, hashes, or levels; and
5. SHOULD include fixtures and an upgrade path.

Promotion to core considers multiple implementations, public evidence, portability,
security, and vendor neutrality.
