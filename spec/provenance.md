# Provenance

Provenance binds the generator name, locked version and hash; all input hashes; exact
regeneration command; generation time; generated source and artifact hashes;
evaluator name, version and hash; and post-certification modification status.

Claims MUST avoid secrets, credentials, private paths, and raw paid transcripts.
Provider output SHOULD be reduced to the minimum evidence needed for review.
Schema 0.1.1 provenance binds indexed generator, evaluator, toolchain, and
environment identities; generator and evaluator inputs; candidate and optional
built-artifact hashes; generation/evaluation commands; four ordered timestamps;
handwritten-change status; and regeneration lock state.

A syntactically valid hash with no matching indexed identity record is insufficient.
L5 requires no handwritten change after generation and locked regeneration.
