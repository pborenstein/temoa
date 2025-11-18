---
gleaned: 2025-11-15
url: https://www.sbert.net/docs/pretrained_models.html
tags: [gleaning, ml, embeddings]
source: "[[2025-11-15-Fr]]"
---

# Sentence Transformers - Pretrained Models

Overview of available embedding models. Key insight: MiniLM is fast (384 dimensions) but MPNet is better quality (768 dimensions).

For personal vault search, MiniLM-L6-v2 is probably sufficient - speed matters more than the last 2% of quality.

Trade-off:
- MiniLM: ~5ms per embedding, good enough for most tasks
- MPNet: ~15ms per embedding, better semantic understanding

[Link](https://www.sbert.net/docs/pretrained_models.html)
