# Threat model

MNCS addresses accidental or adversarial substitution of sources and evidence,
silent post-certification edits, incomplete claims, hidden UNKNOWN results, invalid
performance victories, unsafe evidence execution, path traversal, provider
overclaiming, and irreproducible generation.

It does not eliminate compromised compilers, kernels, hardware, generator services,
or maintainers. Those belong in the declared trust and environment model. Higher
criticality needs independent methods and domain assurance beyond the minimum level.

Bundle readers should treat every file as untrusted. The reference validator parses
JSON and hashes bytes; it does not execute evidence.
