# DLI versus stopped-memory-gradient prototype

This is a working NumPy dense-memory forward/backward and training implementation, not a pretrained language model or the full HotpotQA protocol. Both arms have identical initial forward predictions and minibatch schedules. They train query projection, content-dependent sigmoid fusion and a classifier. Only DLI trains the memory key/value adapters; the other arm freezes them.

## Run outside the app

Requires Python 3 and NumPy. In an environment where NumPy is already available:

```bash
python engine.py --output new_run --steps 150 --seeds 3
python engine.py --input example_input.json --output uploaded_run --steps 150 --seeds 1
```

The UI supports 10–500 steps, learning rate 0.0001–0.1, temperature 0.1–5, and 1–3 paired seeds. The standalone CLI supports the same limits. The first seed defaults to 17; additional seeds are 18 and 19, not the separate protocol's 17/29/43 schedule. These are deliberately small synthetic mechanism runs, not that protocol's confirmatory stage.

## Input schema

`memory`: M×D array of frozen base embeddings.
`train_x`, `test_x`: N×D arrays of frozen hidden-state features.
`train_y`, `test_y`: integer labels starting at 0. Training must cover every class.
Optional `train_gold`, `test_gold`: one memory-record index per query, for retrieval recall.

Limits: 2–256 records, width 2–64, 4–2048 examples per split, 2–16 classes. `example_input.json` is a full compatible snapshot of the synthetic run.

Synthetic data uses random associations, four labels and a frozen random two-position causal-attention/FFN feature generator. The backbone is not pretrained. Test queries have independent noise but refer to the same memory IDs as training. This is not unseen-fact or natural-language generalization. Memory embeddings do not directly encode answer labels, but the classifier can learn label associations from query features; high accuracy is not proof of faithful retrieval.

## Checks and outputs

`results.json` records configuration, dataset SHA-256, NumPy version, per-arm results and finite-difference checks. Seven dense parameter tensors are checked at their largest-gradient coordinate in float64. Detachment is separately checked by zero key/value gradients and unchanged adapter weights; both arms must match at initialization.

CSV exports contain learning curves, per-seed summaries, predictions and gradient norms. `checkpoints.npz` stores all final trainable/frozen model arrays by arm and seed. This is no-resume final checkpoint storage; optimizer state is not saved.

Memory-disabled and shuffled-value evaluations are post-training interventions, not independently trained no-memory baselines. Recall is optional for uploads and refers to supplied record IDs, not QA supporting-fact accuracy. DLI has more trainable parameters by construction; no claim of parameter-matched superiority is made.

## Scope relative to experiment_protocol.md

Implemented: dense softmax retrieval, query/key/value projections, content-dependent fusion, paired initialization and batches, stopped adapter gradients, Adam training with clipping, gradient checks, held-out classification and evidence-use interventions.

Not implemented: pretrained decoder, natural-language generation, HotpotQA ingestion, document-disjoint generalization, ANN/PQ, conditional read skipping, language-model loss, clinical/domain transfer or GPU timing. Learning rate, widths, seeds, step budget and fusion initialization differ from the larger protocol and are shown explicitly in each saved run. No significance or LLM latency conclusion follows from these results.

The packaged demo results are measured execution outputs, not fabricated scores. They use one paired seed by default; use three seeds for an exploratory variability check. The app displays the measured outcome even when the two accuracies tie.
