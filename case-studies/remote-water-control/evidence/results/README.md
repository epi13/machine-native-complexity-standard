# Remote Water development evidence

Epoch-2 evidence is committed as deterministic gzip-compressed JSON:

- `scenario-results.json.gz` contains every baseline and candidate observation for the 27 declared development scenarios.
- `study-summary.json.gz` contains hard gates, frozen selection results, per-scenario comparisons, intervention aggregates, identities, and limitations.

The gzip header has a zero modification time and no filename, so identical JSON evidence produces identical bytes across supported environments.

Inspect locally with:

```bash
gzip -dc scenario-results.json.gz | python -m json.tool
gzip -dc study-summary.json.gz | python -m json.tool
```

These files are repository-visible development evidence. They are not the runtime-seeded protected-at-execution artifacts uploaded by GitHub Actions, and neither form constitutes an independent final evaluation or production authorization.
