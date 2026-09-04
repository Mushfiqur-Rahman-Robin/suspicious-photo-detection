# Synthetic-Golden Evaluation

Method: embeddings generated as tight unit-sphere clusters with known injected outliers, then flagged by the configured detector. The real dataset is unlabeled, so these numbers are the only precision/recall/F1 measure available.

Test-set strategy: these scenarios are the held-out synthetic TEST set (SPEC §16). The pipeline trains nothing (pretrained embeddings only, SPEC §2.2), so the unlabeled real photos need no train/test split. The set is deterministic from the configured seed; a different seed (`scripts/run_evaluation.py --seed <n>`) samples a fresh held-out test set, which is how any parameter tuning must be validated - never on the seed that gates the release.

| Scenario | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| single_fake | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| tight_clique | 3 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| multi_cluster_legit | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| uniform_outlet | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| small_outlet | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)

All scenarios pass the configured gates (precision>=0.8, recall>=0.8, f1>=0.8).
