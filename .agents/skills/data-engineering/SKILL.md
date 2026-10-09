# Data Engineering and AI Training Data

- Keep the data/training pillar fully supported; it is not being replaced by agent features.
- Inspect existing ingestion, cleaning, schema validation, PII masking, deduplication, split and export code before adding modules.
- Prefer deterministic transforms, reproducible splits, manifests, lineage and quality reports.
- Validate schema, missingness, duplicates, leakage and privacy risks before training export.
- Make large-data dependencies optional and avoid loading full datasets when streaming/chunking is feasible.
- Keep training backend claims precise: data preparation does not itself guarantee that a model was trained successfully.
