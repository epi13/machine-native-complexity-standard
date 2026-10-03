# Experimental repository manifest binding

The evolving `v0alpha1` manifest admits `projection_inventory` (a relative
inventory path), `structure_profile` (MNCDS owner/path/content identity), and
explicit artifact classes on organization surfaces. Projection meaning stays
with Commons and the selected semantic owners; the manifest schema owns the
reference boundary only. Unknown top-level fields remain rejected.

The schema now recognizes provider invocation, native policy, artifact,
resident-adapter and selected-toolchain transport fields already used by the
family. Existing version-only Forge consumptions migrate to exact version
envelopes. This is an additive experimental binding, not a change to released
MNCS evidence or MNCDS development-record schemas.

Declaring a projection or capability does not establish execution health.
Mixed/derived files remain compatibility surfaces, never authoritative inputs.
