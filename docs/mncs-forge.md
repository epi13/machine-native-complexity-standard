# MNCS Forge MCP integration

> Experimental, non-normative integration. MNCS Forge is not required for MNCS
> conformance and is not an accredited certification system.

[MNCS Forge](https://github.com/epi13/mncs-forge-mcp) is a separate local stdio MCP
server and CLI. It can orchestrate bounded providers and development checks, but it
does not replace the offline MNCS/MNCDS validators and cannot create independent
evaluation, protected custody, witnessing, governance approval, certification, or
promotion.

The standards repository owns the normative validator, schemas, conformance corpus,
and interoperability checks. Empirical case-study implementations, evidence, provider
fixtures, and their project-specific Forge configuration are maintained in the
[`mncs-reference-studies` repository](https://github.com/epi13/mncs-reference-studies).
Use that repository's configuration and workflow documentation for empirical work.

Forge is not an analyzer or a universal Code Property Graph implementation. Compilers,
analyzers, mutation tools, sanitizers, benchmarks, and runtime harnesses remain
replaceable providers. Missing or unsupported capability remains `UNKNOWN`; source
reading, grep, and line counts do not establish independent structural evidence.

Ordinary standards validation never launches Forge and does not require a sibling
checkout:

```bash
make check
```

Historical provider and Forge results remain frozen in the repository that owns their
study epoch. Migration does not rewrite them or promote a bounded development result
into an MNCS or MNCDS claim.
