# Philosophy

Relocated readability means a future maintainer can answer, without reverse
engineering generated internals:

- What must this component do and never do?
- Which inputs, states, resources, and environments are in scope?
- What benefit justified the generated candidate?
- What independently demonstrated correctness and safety?
- Which facts remain UNKNOWN?
- How is the candidate reproduced, audited, and rolled back?

Machine-native code is a replaceable artifact, not an oracle. Its manifest and hashes
make edits visible. A readable reference remains available. No performance result
can erase a correctness failure, and no tool brand can erase uncertainty.
