# DistilBERT same-split sweep — started 29 October 2026

This is a real full-parameter fine-tuning run, not a frozen encoder, shortened smoke test, or evaluation of the author's private checkpoint. At handoff the sweep is RUNNING, with no completed model scores yet. The machine has four CPU cores and no GPU; measured training cost implies several hours for the six-model sweep. The initial pilot performed real optimizer steps but is not scored as an experiment.

## Exact evaluation contract
- Nazario and MixedEmail public releases, seeds 42, 43, 44: six separately initialized models, 1,280 train / 160 validation / 160 test emails per corpus/seed, identical to the original manifest.
- Full original input-file SHA-256 checks plus split hash and label checks run before training. Missing raw data are downloaded; changed source bytes cause failure rather than silently changing splits.
- Public distilbert/distilbert-base-uncased with random binary classification head. Resolved checkpoint commit and package versions are recorded in training_provenance.json. The supplied script resolves the model's default revision on launch; verify the recorded commit before comparing resumed/new runs if upstream changes.
- Three epochs, learning rate 5e-5, weight decay .01, effective batch 16. To fit CPU memory, actual microbatch is 2 with eight gradient accumulation steps, dynamic padding and length grouping. All layers are trainable. Float32 and SDPA attention, maximum 512 tokens following the shared 6,000-character input cap. Default Trainer linear learning-rate schedule and AdamW are used.
- Training examples are length-grouped for efficiency. Gradient accumulation and the different batching order are not guaranteed bitwise-equivalent to a single batch of 16.
- Validation loss is observed each epoch; final epoch is used regardless of results. No test selection, threshold tuning or early stopping.
- Four in-domain conditions (clean, 5% and 15% obfuscation, first 80 words) and cross-corpus clean transfer: 30 planned DistilBERT evaluation rows. DistilBERT's 512-token truncation is an additional input limitation not shared by TF-IDF.

## Running and interruption
The live run writes run_status.html and run_status.json on every optimizer update and completed-job transition. Reopen the HTML to see later updates. It is a status file, not a remote supervisor; it does not guarantee process survival or send notifications. The updated UTC time reveals stale progress. If the session environment stops, so does training.

Completed job directories contain COMPLETE.json; they are skipped when the same script is started again. In-progress jobs save a resumable model/optimizer checkpoint every 40 optimizer steps, keeping the most recent checkpoint only. Restart resumes it if present; otherwise that job restarts. A completed model's fitted weights are retained, and its intermediate optimizer checkpoint is deleted to conserve disk space. This allows continuation but does not by itself schedule a restart.

In this workspace, restart with:

`python3 user/workspace/co-scientist-outputs/phishing-benchmark/distilbert-run/run_distilbert_sweep.py`

Do not launch another worker while the original is still alive. The initial process ID and console log are in user/user-data/tmp/distilbert-run/worker.pid and training.log; these are ephemeral operational files, not research outputs.

To reproduce elsewhere, unpack the runner bundle into a directory with run_distilbert_sweep.py and benchmark_code_and_results.zip, supply the dependencies in requirements.txt, then run:

`python3 run_distilbert_sweep.py --root . --data-dir data-cache`

The bundled inner archive contains only the original public-data benchmark support files required by this runner. It intentionally excludes unrelated synthetic email/workflow material present in the earlier full bundle. Raw public emails are not redistributed. The CPU-specific torch wheel in requirements.txt targets Python 3.12/Linux x86_64; replace it with an appropriate PyTorch build on another platform. This script currently explicitly uses CPU; changing to a GPU requires updating use_cpu and device/thread metadata, then documenting that execution change.

## Outputs as jobs complete
- distilbert_results.csv: one completed-model/target/condition row, reaching 30 rows when finished.
- combined_evaluation_grid.csv: original 180 rows plus completed DistilBERT rows.
- combined_leaderboard.csv: means, SD and n_splits per source/target/condition/model. Partial DistilBERT means must NOT be described as three-seed results.
- jobs/<corpus>-seed<seed>/predictions.csv: per-email SHA-256 identifiers, truths and predictions; no raw text or live URLs.
- training_history.json and model/ under each job: measured training logs and fitted checkpoint.
- After all six models finish, all_paired_tests.csv adds 60 DistilBERT-vs-baseline comparisons to the original 150 tests, using global Holm correction across 210 exact two-sided McNemar tests. Pointwise stratified paired bootstrap intervals for F1 differences use 1,000 resamples. Tests concern different quantities: correctness versus F1.
- Before these paired comparisons, all seed-42 baseline predictions are rerun and every confusion count is checked against archived results. A mismatch halts statistical reporting.
- completed_results_and_code.zip is generated only after successful completion. It excludes large model weights; those remain in their job directories.

The original paper/data caveats remain: overlapping seed samples, no campaign-disjoint split, source/label confounding, and MixedEmail positives including generic spam. This does not measure NER, human analyst performance, containment time, or operational automation safety.
