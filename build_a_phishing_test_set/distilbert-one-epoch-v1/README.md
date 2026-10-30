# Completed DistilBERT benchmark — fixed one-epoch CPU run

**Full all-layer fine-tuning completed** on the original 800 synthetic training emails. This is an actual fitted DistilBERT model, not a frozen encoder, randomly initialized classifier evaluation, prepared-only script or result from the unrelated earlier sweep. The fitted checkpoint was reloaded and reproduced all 380 exported held-out decisions.

**Protocol deviation:** This run uses **one fixed epoch**, chosen from a timing pilot before trained predictions were inspected, rather than the paper's illustrated three epochs. It is a CPU-budget baseline, not a replication of the paper's reported performance. No other epoch/checkpoint was selected by test results.

## Main results

Each synthetic/public evaluation set has 50 phishing and 50 non-phishing examples. The paired challenge has 40 of each. Validation is reported separately and was not used for early stopping or threshold tuning.

| DistilBERT split | Accuracy | Precision | Recall | F1 | FPR | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---|
| Synthetic validation, n=100 | 1.000 | 1.000 | 1.000 | 1.000 | .000 | 50 / 0 / 0 / 50 |
| Synthetic test, n=100 | 1.000 | 1.000 | 1.000 | 1.000 | .000 | 50 / 0 / 0 / 50 |
| Public emails, n=100 | .780 | .719 | .920 | **.807** | **.360** | 32 / 18 / 4 / 46 |
| Hard-negative challenge, n=80 | .800 | .722 | .975 | **.830** | **.375** | 25 / 15 / 1 / 39 |

FPR is FP/(FP+TN), not 1−precision. Here it means an email-classification error, **not a measured automated containment error**.

### Comparison with unchanged earlier baselines

| Model | Synthetic-test F1 | Public F1 | Public FPR | Challenge F1 | Challenge FPR | Both challenge pair members correct |
|---|---:|---:|---:|---:|---:|---:|
| Word TF-IDF + logistic regression | .800 | .645 | .640 | .879 | .275 | .725 |
| Character TF-IDF + logistic regression | .800 | .738 | .300 | .764 | .375 | .500 |
| **DistilBERT, one epoch** | **1.000** | **.807** | .360 | .830 | .375 | .600 |

The TF-IDF values are the archived earlier results using the same 800 training records and unchanged evaluation splits, not newly tuned baselines. Constant and keyword rows also remain in `comparison.csv`.

**Interpretation:** DistilBERT improves public-set F1 by about .069 over character TF-IDF and .162 over word TF-IDF. Its public false-positive rate is lower than word TF-IDF but higher than character TF-IDF. On the authored hard-negative challenge it is worse than word TF-IDF in F1, FPR and pair success. A stronger public F1 therefore does not establish safer handling of legitimate security messages.

## Hard-negative failures

DistilBERT falsely flags **15/40** benign challenge emails and misses **1/40** malicious controls. Both members are correct in **24/40 matched pairs**. It falsely flags both benign examples in each of:

- **First-party MFA number matching** — legitimate verification is confused with code disclosure.
- **Warnings quoting attacker instructions** — quoted credential requests are treated like the requested action.
- **Self-initiated password resets** — real reset workflow language still triggers false alarms.

Other false positives include legitimate statements, delivery notices, signing requests, managed VPN maintenance, payroll callbacks, planned credential rotation, secure-mail notices, forwarded evidence and an inert IOC bulletin. The one missed positive is an executive-purchase control requesting bypass of finance approval and prepaid-card code transfer. `hard_negative_family_scores.csv` inside the archive gives the complete family audit; individual decisions and probabilities are also included.

## Exact method and execution

- **Checkpoint:** `distilbert/distilbert-base-uncased`, pinned revision `12040accade4e8a0f71eabdb258fecc2e7e948be`; randomly initialized two-class head, then all **66,955,010 parameters** trainable.
- **Input/features:** Only `email_text`. Labels, source, pair/family IDs, negative rationales and endpoint context are never model features. Input SHA256: `33c50961cd3531187cd26f9d384eac5f713f52025b38d3c4c6c8d98ee39d021e`.
- **Data:** 1,180 records total: 800 train, 100 validation, 100 synthetic test, 100 public holdout, 80 challenge. Public/challenge records never enter training or model selection.
- **Training:** One epoch, 50 optimizer updates; learning rate 5e-5, linear decay to zero without warmup, weight decay .01, Trainer AdamW defaults and gradient clipping. Float32; microbatch 8, two accumulation steps, effective batch 16; seed 172289201; CPU, four threads. Gradient accumulation and batch order need not be bitwise equivalent to a single batch of 16.
- **Tokenization:** Uncased pretrained tokenizer, maximum 512 tokens, dynamic right padding. No training/validation/synthetic-test/challenge record was truncated; **11/100 public messages were truncated**. TF-IDF has no corresponding 512-token limit.
- **Selection/prediction:** Fixed final epoch, no early stopping, no checkpoint comparison and no threshold tuning; argmax of two logits. Exported probabilities are not shown to be calibrated.
- **Measured runtime:** Training, including periodic checkpointing and epoch validation, took **180.94 seconds** on the now-uncontended CPU. The conservative pilot extrapolation was longer; the actual batched run was faster. Independent checkpoint reload verification took 23.62 seconds for 380 records. These are experiment runtimes, not isolated serving-latency benchmarks.
- **Versions:** Python 3.12.3, PyTorch 2.6.0+cpu, Transformers 4.49.0, Accelerate 1.4.0, scikit-learn 1.9.1, NumPy 2.5.4.

## Checks performed

All 380 prediction IDs and labels were matched back to the input; none belongs to training. Every confusion count was recomputed from per-record predictions. Final weights/tokenizer were reloaded independently, and all 380 decisions matched exactly. Model/data revision and hyperparameters are recorded. The final training history records 50 optimizer steps and epoch 1.0. This validates execution and bookkeeping, not real-world label quality or safety.

This completed run is separate from the earlier stopped frozen diagnostic and prepared three-epoch runner. Their earlier incomplete-status files are historical; no three-epoch completion is claimed here.

## Files and reproduction

- `benchmark.png` — F1 and benign false-positive rates for the three learned models on all three evaluation splits.
- `comparison.csv` — 15 comparison rows: the prior four baselines on three splits plus DistilBERT on those splits; validation is in the archive's raw score table.
- `distilbert_benchmark.zip` — completed experiment, **including fitted model weights/tokenizer**, 1,180-record input, scripts, contract, raw scores, 380 predictions, training history, provenance, family audit, verification results and public-email attribution. Intermediate optimizer checkpoints are omitted.

Extract the archive and, with its recorded dependencies available, run:

```text
python3 verify_checkpoint.py
```

This reloads the fitted model and checks all recorded decisions without retraining or downloading a new model. To repeat training on CPU, use:

```text
python3 run_benchmark.py --allow-cpu
python3 summarize_results.py
```

The training runner downloads the pinned base revision if it is not cached; `--cache-dir` can point to an existing Hugging Face cache. The default output is `results/`; move existing results or choose another `--out` before a fresh training run. The summary and verification scripts target the included `results/` directory. Hardware/platform changes can alter numerical results; this is one seed, not a reproducibility study across devices.

## Limits on the conclusion

The paper's DOI is https://doi.org/10.22541/au.177446759.98281679/v1, but this uses the authored development benchmark, not the author's private data. Synthetic emails contain only 40 base templates overall, with two test lure families. The public set is source/class-confounded, historical, transformed, not independently adjudicated and possibly present in model pretraining. Challenge topics partly overlap training topics, variants are correlated and all released tests are visible.

One seed and one epoch do not establish general superiority. No significance test, reliable campaign-level uncertainty, campaign-disjoint claim, operational workload saving, NER score or containment-safety result is provided. Do not deploy automated email purging or host isolation based on these scores; legitimate-message false positives remain substantial. Public email licensing/third-party rights and partial-redaction caveats still apply; see the included attribution and data card.
