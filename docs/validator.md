# Validator

`mncs-validator` is the reference offline validator. It:

- validates Draft 2020-12 schemas;
- confines relative references to the bundle;
- verifies local SHA-256 identities;
- detects missing and stale evidence;
- checks level/status consistency and UNKNOWN propagation;
- validates canonical layout; and
- performs explicit Pareto comparison.

It never imports or executes a referenced source file, script, binary, or provider.
Use `--json` on commands for automation. Exit 0 means the document or bundle is
internally valid; consult `final_status` to learn whether the candidate passed.
