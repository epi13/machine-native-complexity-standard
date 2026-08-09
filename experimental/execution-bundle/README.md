# Experimental execution bundle

This directory contains a generic EA-NEXT-002 source manifest and small neutral
inputs used by deterministic tests.  The ZIP is intentionally built during the
tests rather than committed as generated transport.  The logical bundle identity
is content-addressed from the canonical manifest; the archive identity is the
identity of one exact ZIP transport.

This profile establishes bounded package integrity only.  It does not establish
that a runner used the bundle, execution correctness, isolation, custody,
independence, conformance, or promotion.
