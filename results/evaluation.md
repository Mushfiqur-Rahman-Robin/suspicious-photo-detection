# Synthetic-Golden Evaluation

Method: embeddings generated as tight unit-sphere clusters with known injected outliers, then flagged by the configured detector. The real dataset is unlabeled, so these numbers are the only precision/recall/F1 measure available.

| Scenario | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| single_fake | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| tight_clique | 3 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| multi_cluster_legit | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| uniform_outlet | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)
| small_outlet | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | (PASS)

All scenarios pass the configured gates (precision>=0.8, recall>=0.8, f1>=0.8).
