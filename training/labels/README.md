# Annotation mapping

Training-only, standard-library Python implementation of
[the versioned annotation mapping contract](../../docs/taxonomy/annotation-mapping-v1.md).
The existing production Rust classification API is unchanged.

```python
from map_annotations import map_normalized_record

# record comes from verified, rights-admitted private normalized ingestion.
metadata = map_normalized_record(record)
# Use metadata["dimensions"] with metadata["training_mask"] for independent heads.
# metadata["classification"] is the safe advisory runtime projection.
```

This API returns private annotation metadata; callers must retain source rights
and receipt checks and must not print or commit actual labels or message data.
Run `powershell -NoProfile -File training/labels/test-mapping.ps1` locally.
