# Regeneration

Regeneration is a controlled replacement, not maintenance by direct source editing.
The human layer MUST document prerequisites, locked tools, content-addressed inputs,
command, expected outputs, evaluation command, rollback, and acceptable
nondeterminism.

At L5, the recorded command and inputs MUST reproduce the certified identity or
produce a new candidate requiring full recertification. A readable rollback
implementation MUST remain buildable.
