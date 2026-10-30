# DistilBERT benchmark — execution incomplete

**There are no completed DistilBERT classification scores for the 1,100-record synthetic/public benchmark.** This folder supplies the fixed experimental contract and a portable full-fine-tuning runner, not a completed benchmark or a claim of reproducing the paper.

## What happened

The available machine has four CPU cores, no CUDA GPU, and a separate full-parameter DistilBERT sweep already running on different corpora. That sweep has no completed model and is not interchangeable with this dataset's benchmark. It was left untouched.

A new frozen-encoder diagnostic was attempted to obtain a faster comparison. Reduced precision was slow on this CPU; a dynamically INT8-quantized version proceeded through **60 of 1,100 records** before being deliberately stopped to avoid a prolonged competing job. It never fit a classifier or produced evaluation scores. Its partial embeddings are not released as a trained model or benchmark result. This diagnostic is **not** the full fine-tuning method described in the paper.

No DistilBERT number has been added to the existing baseline leaderboard. The prior TF-IDF scores remain unchanged.

## Prepared full-fine-tuning experiment

- **Model:** `distilbert/distilbert-base-uncased`, pinned Hugging Face revision `12040accade4e8a0f71eabdb258fecc2e7e948be`; random binary classification head; all transformer layers trainable.
- **Input:** Exactly the released augmented dataset, with SHA256 checked before training. Only `email_text` is a feature; source and annotation metadata are never inputs.
- **Splits:** 800 synthetic train, 100 synthetic validation, 100 synthetic test, 100 public holdout. Public rows never enter training, threshold tuning or checkpoint selection.
- **Training:** Three epochs, learning rate 5e-5, weight decay .01, float32, maximum 512 tokens, dynamic padding, microbatch 4 with four accumulation steps (effective batch 16), seed 172289201. Accumulation/batch order need not be bitwise equivalent to a single batch of 16.
- **Selection:** Final epoch only; validation loss logged each epoch; no early stopping, best-test checkpoint selection or tuned threshold. Binary predictions use argmax.
- **Metrics:** Accuracy, phishing precision/recall/F1, FPR and all confusion counts, reported separately by split. Individual predictions, training history, resolved model revision, runtime versions and final weights are saved after successful execution.

These settings align with the paper's classification illustration, but use this constructed development dataset rather than the author's private data or checkpoint. No NER, containment safety, analyst workload or response-time claims follow from the classification run.

## Run on dedicated compute

Extract `distilbert_runner.zip` into its own folder. The archive contains the input dataset, full-fine-tuning runner, contract, requirements, source attribution and status documentation.

With the listed dependencies and a compatible CUDA-enabled PyTorch build available, run:

```text
python3 run_full_finetuning.py
```

The script refuses to train without CUDA unless `--allow-cpu` is explicitly supplied. CPU execution may take hours under similar contention. Use `--resume` to continue an existing epoch checkpoint; it fails if no checkpoint exists. `--cache-dir` selects a Hugging Face download/cache location; `--input` and `--out` override paths. A changed input checksum stops execution. There is no scheduler, queued job, automatic GPU provision or background training promise attached to this package.

On successful completion, `results/` will contain `distilbert_scores.csv`, `predictions.csv`, `training_history.json`, `provenance.json`, checkpoints and `final_model/`. **Those outputs do not exist yet.** The runner was syntax-checked and its CLI help executed; the full training/evaluation path has not been execution-tested on a GPU here.

## Interpretation constraints

The synthetic dataset has only 40 base email templates and two independent test lure families. Public labels are source-provided, not independently expert-adjudicated; Nazario supplies all positives and Enron all negatives, confounding source with class. Duplicate-template proxies are not campaign ground truth. Do not describe any eventual scores as campaign-validated, production-ready, or a replication of the paper's reported F1. Attribution and privacy/third-party-rights caveats from the public extension travel with the input dataset.

## Current deliverables

- `status.json` — explicit stopped/incomplete execution status; DistilBERT metrics are null.
- `run_contract.json` — immutable input digest, splits, model revision and proposed training/evaluation settings.
- `distilbert_runner.zip` — portable prepared experiment, including scripts, input data, requirements and attribution.
