# Suspicious Photo Detection - Method Write-up

## Method
- **Embeddings:** dino_v2_small (384-dim), L2-normalized; cosine similarity is computed as a dot product on the normalized vectors. The embedder is model-agnostic (DINOv2 is the default; CLIP is an optional alternative selected by config).
- **Scoring:** per-outlet fusion of three complementary signals - distance to a robust (coordinate-wise median) prototype of the outlet's embeddings, mean similarity to the k nearest neighbours (local-density consensus), and a seeded Isolation Forest anomaly score. The three are weighted equally by default, with the Isolation Forest contribution down-weighted for small outlets where its scores are unreliable.
- **Outlier rule:** an adaptive per-outlet threshold `max(median + k*MAD, score_floor)`; an image is flagged when its fused score exceeds it, and a deterministic human-readable reason is chosen from the signal(s) that dominated the flag.

## Measured run
- Outlets: 159; images: 2042; flagged images: 122 (5.97% of images; 77 outlets had flags).
- Embedding throughput: 4.4 images/sec (0 cache hits / 2042 misses); device: cpu; seed: 42.
- Embedding latency (sec/img, p50/p95/p99): 0.1947 / 0.2695 / 0.3094.
- Stage wall-clock (sec): load=21.60, embed=467.38, detect=35.37, report=0.01.

## Validation
- Synthetic golden set: all five scenarios pass the configured precision/recall/F1 gates (see `evaluation.md`).
- Reproducibility: a re-run on the same dataset yields byte-identical `results.json` (fixed seed + content-addressed embedding cache).
- Qualitative review of real flags: 11 sampled flags across 7 outlets were each more similar to a different outlet's photos than to their own outlet's photos (cross-outlet cosine 0.18-0.84 vs own-outlet mean 0.01-0.54) - i.e. photos of other storefronts, the borrowed-photo failure mode this pipeline targets.

## Rationale & trade-offs
- No single signal catches every fake: centroid distance is confused by multi-cluster outlets, kNN can miss a tight clique of fakes, and Isolation Forest is unstable at low N - fusing three complementary signals raises precision without any labels.
- A global threshold is wrong because outlet appearance variance differs wildly; the robust median + MAD threshold is distribution-free and needs no per-outlet tuning, and the absolute floor prevents noise-level flagging in near-uniform outlets.
- The trade-off is precision vs recall at the margin: conservative flagging minimizes false positives at the cost of missing subtle one-off changes, which is the right bias for triage.

## Scalability
- Linear in image count; embeddings are computed once and cached by content hash, so re-runs and incremental updates are near-free. Pairwise work is bounded O(N^2) per outlet with N <= ~40 here.

## Limitations
- A one-off, sharp appearance change (e.g. a full remodel in a single photo) is statistically indistinguishable from a fake and may be flagged.
- Multi-cluster robustness relies on local density; a sparsely populated legitimate second cluster can still be flagged.
- Isolation Forest requires a minimum image count; very small outlets rely on centroid + kNN only.
- The real dataset has no labels; precision/recall are measured on the synthetic golden set (`evaluation.md`), not on the real photos.
