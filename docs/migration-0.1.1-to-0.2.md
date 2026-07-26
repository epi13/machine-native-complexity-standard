# Migrating 0.1.1 evidence to 0.2

Do not rewrite historical records. Copy the bundle into a new versioned location,
retain hashes or references to the frozen 0.1.1 records, create new 0.2 manifests and
evidence records with current schema/MNCS versions, validate them, and then optionally
create a new attestation over the new subject bytes.

Legacy validation remains available. Migration does not make old evidence signed and
does not convert self-asserted 0.1 acceptance into evidence-derived or trusted
certification.
