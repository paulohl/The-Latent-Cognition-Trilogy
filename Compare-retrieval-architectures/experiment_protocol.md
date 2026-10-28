# DLI-LLM experiment protocol

**Version 1.0 · 28 October 2026 · Proposed experiments; no runs performed**

## 1. Objective and scope

Test whether DLI-LLM's trainable latent memory and content-dependent fusion improve evidence-dependent answers relative to matched memory controls, and whether sparse/conditional access reduces measured cost without materially degrading answer quality. Treat the dense formulation in Sections 2.2–2.5 separately from Appendix A's top-k/product-quantized implementation.

This is an implementation and evaluation protocol, not a report of completed Methods. All numerical settings below are **proposed design choices**, not values reported in the paper or established optimal settings. The first stage is a small-model mechanism pilot. The paper's proposed 7B/13B experiments follow only after the mechanism and data pipeline pass their checks.

## 2. Hypotheses and decision rules

| ID | Gap addressed | Primary contrast | Endpoint and interpretation |
|---|---|---|---|
| H1 | Value of gradients into document memory | Dense DLI versus identical dense DLI with detached document representations | HotpotQA answer F1, in percentage points. Evidence of a gradient benefit requires an adjusted positive difference; practical target: at least +2 points. Report latency/memory even if accuracy improves. |
| H2 | Value of content-dependent fusion | Dense DLI versus the same architecture with learned content-independent fusion | Answer F1. Same training budget and starting weights. A positive difference supports content dependence, not the claim that retrieval can be skipped. |
| H3 | Conditional retrieval rather than post-read suppression | Pre-read policy versus always-read sparse DLI | At least 20% lower measured end-to-end p95 latency, with F1 loss bounded above by 1 point and audited unsupported-claim rate increase bounded above by 2 percentage points. All bounds must satisfy the criterion. |
| E1 | Dense-to-sparse implementation gap | Exact top-k, ANN top-k, quantized ANN versus dense DLI | Report quality–cost curves and ANN recall versus exact top-k. No automatic equivalence assumption. |
| E2 | Shared token/document space | Document-only, mixed aligned, mixed unaligned, and separate-bank routing | Gold-evidence recall and answer F1 at matched total capacity. A shared embedding width alone is not a successful alignment result. |
| E3 | Adaptation and integrity | Clean versus updated, contradictory, duplicated or poisoned memory | Paired changes in answer correctness, evidence use and attack success. These are separate claims from H1–H3. |

H1–H3 are the planned confirmatory family, but the pilot is **feasibility and effect-size estimation only**. Thresholds express practical requirements; they are not power calculations. Before confirmation, freeze the final sample size and the thresholds without inspecting held-out outcomes. Failure to clear a threshold means the corresponding benefit is not established, not that the architecture has no possible use.

## 3. Launch manifest and fixed configuration

Complete and archive the following before training. A run with an incomplete manifest is exploratory.

- **Backbone** — one downloadable, license-compatible **base** decoder in the 0.3–1B parameter range; record model ID, immutable revision, tokenizer revision and checkpoint checksum. Do not substitute an instruction-tuned model in only one arm.
- **Hardware** — record GPU model/count, VRAM, CPU/RAM, storage, interconnect, driver and framework versions. Profile the small dense configuration before committing a run budget; no GPU availability is assumed here.
- **Input/output** — maximum 512 input tokens and 64 generated tokens; greedy decoding; identical question/instruction template and answer normalization. External-text RAG has its retrieved context counted within the same input cap. Count latent read traffic separately rather than pretending vectors and text tokens are equivalent budgets.
- **DLI block** — insert one retrieval block after self-attention at layer `floor(2L/3)`, using zero-based layer numbering. Preserve the original residual/normalization order and document its exact location. One layer tests the mechanism; it does not validate retrieval at every layer.
- **Memory** — start with a 16,384-record document bank, projected to retrieval width 256 and value width equal to the backbone hidden width. Use a fixed-capacity masked bank; do not pad with answer-bearing material. If the available corpus exceeds capacity, use the predeclared deterministic selection rule in Section 4.
- **Training** — freeze backbone weights in the mechanism pilot; train the retrieval block and document adapters. Use AdamW, learning rate 1e-4, weight decay 0.01, gradient clipping 1.0, effective batch size 16 questions, five passes over training questions, 5% linear warm-up then cosine decay. Use bf16 only if supported, otherwise record fp32. No per-arm precision changes.
- **Seeds** — 17, 29 and 43 for initialization, minibatch order and stochastic components; use matched seeds across arms. Log actual processed examples and optimizer steps.
- **Selection** — the primary analysis uses the final fixed-step checkpoint. Intermediate checkpoints are diagnostics, not test-selected winners. One development-only learning-rate rescue is allowed if *all* arms diverge; restart the full comparison and document the change.

Freezing the backbone deliberately isolates the module under a limited budget. A positive pilot does not establish the behavior of joint full-model pretraining. A negative pilot may motivate an explicitly labeled backbone-adaptation study, not a hidden change of protocol.

## 4. Data, splits and leakage controls

### Stage A: controlled HotpotQA pilot

Use a pinned HotpotQA **distractor** release and its supplied paragraph text. This is a controlled evidence-access test, not full-Wikipedia open-domain retrieval.

1. Select 1,000 training questions from the official training split. Select 200 development and 400 held-out evaluation questions from the official development split, with no question overlap. Use deterministic hashing of question IDs with selection seed 101. Save the ID lists before training.
2. Construct split-specific banks from **all supplied paragraphs**, not only gold-support paragraphs. Chunk into at most 128 backbone-token units, retaining sentence boundaries, titles and sentence IDs. Deduplicate normalized identical chunks and map each original sentence to its chunk(s).
3. Keep each split's complete set of supplied chunks if it fits the 16,384-record capacity. If it does not, reduce the number of selected questions by a predeclared hash-order prefix until their complete paragraph union fits. Do not use gold labels to retain only helpful chunks. Log the reduction before training; this changes the effective sample size.
4. Allow an evaluation bank to contain evaluation evidence because that is the inference input being tested. **Never use evaluation answers or support labels for adapter updates, retrieval supervision, hyperparameter selection, index construction priorities or poisoning selection.** Initialize evaluation records by the frozen encoding/adapters of that run, not by training per-record evaluation parameters.
5. Detect duplicate questions and answer-bearing near-duplicate passages across training and evaluation. Report their frequency and a sensitivity analysis excluding overlapping source passages. The primary controlled test permits source-document overlap; it does not claim unseen-document generalization. Add a separately constructed document-disjoint test only if enough data remain.
6. Publish answerability and coverage checks: whether every annotated supporting sentence survives chunking, truncation and capacity limits. Keep failures in the denominator and identify them; do not silently exclude difficult cases.

The pilot cannot establish absence of contamination in the backbone's original pretraining data. Its paired comparisons use the same checkpoint to limit that confound.

### Stage B: confirmation and transfer

After Stage A, preregister a larger HotpotQA held-out set from unused examples and its exact IDs. Do not reuse pilot evaluation outcomes as confirmatory data. Estimate required sample size from development/pilot variance and a +2 F1-point target, accounting for training-seed variation. If the available held-out set or compute is insufficient, label confirmation underpowered rather than claiming that three seeds or an arbitrary question count guarantees power.

Add version-pinned TriviaQA for factual QA and BioASQ **factoid** questions for biomedical transfer. Freeze the task release, permitted abstracts/corpus snapshot, answer synonyms and official task-specific scorer before launch. Use official released train/evaluation partitions where available; if gold test labels are unavailable, partition released labeled data in advance and describe it as an internal held-out evaluation. These extensions are not prerequisites for the mechanism pilot.

## 5. Memory representation and gradient contract

For the document pilot, encode each chunk with the same frozen backbone in a separate, non-causal document-encoding pass only if the architecture supports it; otherwise use the normal causal forward pass. Record this choice and keep it fixed. Mean-pool its last-layer token states, excluding padding, to obtain a frozen base embedding `e_i`. Cache these base embeddings once per split. **Do not imply that these are the learned keys or that an ANN index remains fresh when adapters change.**

Define `k_i = A_k(e_i)` and `v_i = A_v(e_i)` using trainable linear adapters. Define queries `q_t = W_q h_t`, scaled scores `s_ti = q_t^T k_i / (sqrt(256) tau)`, softmax weights, weighted value `r_t`, and fusion `g_t = sigmoid(W_g[h_t; r_t] + b_g)`. Set initial temperature `tau=1`; initialize fusion bias to -2. Query scaling, adapters and initialization are proposed implementation specifications added here, not quoted manuscript equations.

| Arm component | Trainable in DLI | Detached-memory counterpart | Gradient test |
|---|---|---|---|
| Query projection and fusion gate | Yes | Yes | Both receive nonzero gradients on a known-answer training batch. |
| Document key/value adapters | Yes | No; use their common initial weights | DLI adapter gradients nonzero; detached arm adapter gradients absent/zero. |
| Cached base document embeddings | No | No | Cache checksum unchanged. |
| Backbone | No in pilot | No in pilot | No backbone gradients. |
| Dense read | Differentiate scores and values | Differentiate query-dependent scores, not stored representations | Finite-difference check on a tiny bank. |
| Hard top-k | Gradients through selected scores/values only | Same selection rule | Do not claim gradients through changes in discrete membership. |

Use the same initial adapter weights for the trainable and detached arms. Recompute adapted keys/values inside each dense training step so trainable adapters receive gradients. At evaluation, precompute them from the selected checkpoint. An ANN training variant must declare its refresh interval and recompute selected-record embeddings under current adapters for its backward pass; report staleness and refresh cost. Quantization is a retrieval approximation in the first implementation, **not** an unspecified differentiable quantizer.

Use answer-token negative log-likelihood with teacher forcing as the initial loss; mask all prompt tokens. Do not store gold answer tokens or teacher-forced future states in the retrieval bank. Future-token leakage invalidates the experiment.

An optional supervised retrieval-loss study uses annotated training support chunks: `L_ret = -log(sum of retrieval probability assigned to gold chunks)` at the final question position; if no support chunk survives, omit that term for that example and log it. Tune lambda over {0, 0.1, 1} on development data only. Run this as a separate ablation and grant the same support supervision to any learned retrieved-text control. It is not part of H1's initial LM-loss-only contrast.

## 6. Run order and controls

### A0: verification before any scored run

Require: finite-difference agreement within 1e-3 relative error on a tiny fp32 dense bank for non-negligible derivatives; explicit gradient-detachment checks; exact top-k matches brute force on the toy case; no future-token access; correct split isolation; known source-ID recovery; and measured call counts of zero when pre-read routing disables all reads. Do not apply finite-difference smoothness criteria across hard top-k boundaries. Compare quantized/ANN candidates against an exact reference, not against themselves.

### A1: minimum mechanism comparison — 15 training runs

Train five arms with three seeds each. All use the same cached document data and fixed training steps.

| Arm | Specification | Purpose |
|---|---|---|
| D0 | Frozen backbone, no retrieval; use the identical prompt and decoding | Closed-book reference; repeated seeds are duplicate inference controls, not independent training evidence. No training run is needed for D0. |
| D1 | Dense trainable-memory DLI with content-dependent gate | Target implementation. |
| D2 | D1 with document adapters frozen/detached | H1. |
| D3 | D1 with learned scalar fusion gate instead of content-dependent gate | H2. |
| D4 | D1 with ungated residual fusion `h + r`, scaled to matched initialization magnitude | Fusion-mechanism sensitivity; not a clean gate-only causal contrast because fusion form changes. |
| D5 | Exact top-32 DLI; selected-score/value gradients; content-dependent gate | Dense–sparse bridge; precursor to H3. |

The 15 training runs are **D1–D5 × three seeds**; D0 requires only evaluation. Train D5 from the same initial weights and example order rather than silently fine-tuning the best dense model.

### A2: closest-architecture and retrieved-text controls

Add a PKM-style trainable product-key layer at the same layer and a Memorizing-Transformer-style stopped-gradient token cache. Label both **adapted controls**, not reproductions. Fix trainable-parameter count within 5% where feasible; if that cannot be achieved, report both the parameter mismatch and a capacity-matched secondary comparison. PKM parameter slots and source-linked records are not the same unit of capacity.

The token cache receives only causally available inputs and resets for each evaluation question. Do not preload it with answer targets. Run a second, clearly labeled evidence-ingestion condition in which every method can access the same paragraphs before answering. This tests comparable evidence access rather than attributing a no-evidence handicap to the cache architecture.

For the practical retrieval baseline, use the same decoder checkpoint with retrieved paragraph text and the same initial chunk embeddings. Evaluate frozen-retriever and trained-query versions if feasible. This is a matched **retrieve-then-generate baseline**, not a reproduction of the BART-based original RAG or REALM. Its fine-tuning/adaptation budget must be recorded; frozen generation versus trained internal modules is a system comparison, not isolated evidence for integration location. Use a matched adaptation policy for any claim about location itself. Add an oracle-text condition with gold supporting passages, explicitly excluded from normal retrieval results.

### A3: conditional routing — 6 additional training runs if D5 is viable

Keep D5 as always-read reference. Add a content-independent scalar-fusion sparse arm and a pre-read routing arm, each with three seeds. The pre-read policy uses only the current hidden state, not a retrieved vector: `p_t = sigmoid(w_p^T h_t + b_p)`. During training use a straight-through hard binary decision with a sigmoid surrogate, and add `rho × mean(p_t)` to the LM loss. Record that this is a biased gradient estimator and an extension to the main-paper algorithm.

Choose rho in {0, 0.001, 0.01} and a single inference threshold in {0.25, 0.5, 0.75} using development data. Give the always-read arm the same development search allowance for its gate settings. Execute retrieval only for active positions; using a dense read and multiplying its output by zero does not count as skipping. At inference apply a deterministic threshold and report actual skipped reads, latency and estimator-related training instability. If no configuration satisfies development noninferiority, report that outcome and do not test-select a looser margin.

## 7. Shared-space and sparse-index extensions

Run these after the initial comparisons, not as a full Cartesian sweep.

- **Sparse accuracy** — use k in {8, 32, 128}; compare exact, ANN and quantized ANN with the same checkpoint and bank. Define ANN recall as mean overlap with exact top-k divided by k. Define gold recall separately. Inference-only replacement measures approximation tolerance, not trainability of a quantized index.
- **Memory scale** — test 4,096, 16,384 and 65,536 records by varying distractor count while preserving each evaluated question's gold evidence across sizes. This is a controlled scaling test; report the deliberately fixed answerability. Count duplicate records separately from distinct evidence.
- **Mixed memory** — generate token records from causal hidden states of corpus text, never from QA answers; retain source IDs. Compare document-only, token-only, 50:50 mixed shared-bank and 50:50 separate-bank access. Match the total records, total value bytes and read budget; report when these constraints cannot all be matched.
- **Alignment** — compare learned token/document projection adapters against their frozen initial versions. Train alignment using only same-source training chunk/token pairs. In separate-bank routing, normalize read budgets and report routing weights; a bank containing twice as much evidence is not a fair shared-space control.
- **Placement** — only after the single-layer test, compare one versus three retrieval layers with an explicitly matched total read budget, then a separately reported unconstrained version.

## 8. Endpoints and audit definitions

**Answer quality:** official HotpotQA answer EM/F1 is the primary automated endpoint. On the controlled pilot, report answer scores even when retrieval fails. Gold-support chunk recall@k is secondary. Source IDs from memory are retrieval traces, not proof that generated claims used those sources. Official supporting-fact/joint scores require sentence-level predictions; compute them only if a predeclared sentence-selection head or output schema is implemented consistently across relevant arms. Do not relabel chunk recall as official supporting-fact F1.

**Grounding audit:** select 200 held-out questions by fixed hash before generation and audit every compared system on those same questions. Two blinded raters split each response into factual claims and classify each as supported by the logged available evidence, contradicted, unsupported, or non-factual. Resolve disagreements with a third adjudicator; retain initial labels and agreement rates. Report unsupported factual claims / all factual claims, contradicted-claim rate separately, and answer coverage. Empty answers do not count as perfectly grounded: abstention and correctness are separate outputs. If fewer than 200 questions are evaluated, audit all and state the reduced denominator. For H3, adjudicate all three training seeds and use a question-clustered analysis; do not treat claims from one answer as independent samples.

**Retrieval traces:** record query position/layer, candidate IDs, exact/approximate score, selected IDs, bank version and fusion/routing values. Separate evidence absent from bank, evidence present but not retrieved, retrieved evidence not used, and incorrect answer despite sufficient evidence. The last two require human inspection or controlled interventions, not gate magnitude alone.

**Systems cost:** on one fixed hardware configuration, use batch size 1 as the primary setting, 20 warm-up queries and five randomized repetitions of at least 200 fixed queries. Synchronize device work before/after timing; include retrieval, CPU/GPU transfers, shard communication, prompt processing and decoding. Log per-query end-to-end latency, time to first token, decode tokens/s, output length, read calls/token, peak allocated and reserved GPU memory, host RAM and index bytes. Report p50/p95 across queries and uncertainty clustered by query. Measure a fixed 32-token decoding microbenchmark as well as natural stopping, so short or empty answers cannot manufacture a speed gain. Report cold-load and warm-cache conditions separately. Amortized ingestion/index construction and refresh cost must be shown, not hidden in steady-state latency.

## 9. Integrity and adaptation tests

Use paired clean/modified banks for the same preselected questions. Keep clean test answers unchanged except in the explicitly labeled synthetic-update condition.

| Condition | Intervention | Report |
|---|---|---|
| Distractors / duplication | Add non-support chunks; duplicate irrelevant chunks to 10% of record capacity without deleting gold evidence | Change in answer F1, support recall, retrieval diversity and latency. |
| Contradiction | Add a human-reviewed chunk contradicting a gold fact; preserve the original source and its identity | Correct-answer retention, contradictory-source selection, and abstention; do not call authority resolution correct without an explicit authority rule. |
| Text poisoning | Add adversarial instructions or a wrong-answer chunk at 1% and 5% of bank records | Targeted wrong-answer rate and unsupported-claim increase; freeze attacks before evaluation; attacker cannot edit query, checkpoint or gold labels. |
| Latent corruption | Perturb stored keys or values in a separate test with fixed perturbation norm and seed | Degradation curve; label this a different threat model from text poisoning. |
| Knowledge update | In a synthetic, separately scored fact set, replace a fact and regenerate its embeddings without retraining model weights | Accuracy on explicitly updated targets, unchanged-fact retention and refresh time. Synthetic labels are not official benchmark answers. |
| Deletion | Remove designated source records and refresh all indexes/caches | Source-ID disappearance and residual answer recall. Residual correct answers may reflect other evidence or parametric knowledge; they are not by themselves proof of failed deletion. |

Only claim tests at the scales actually run. A small dense-bank integrity result does not establish billion-record behavior or resistance to all attack types.

## 10. Analysis, stopping and reporting

- **Unit of analysis** — question for answer metrics; question-cluster for claim audits and latency repeats; training run for optimization variability. Shared passages can correlate questions; include a source-document-clustered sensitivity analysis where feasible.
- **Uncertainty** — report every seed, the seed mean and standard deviation. Use 10,000 paired bootstrap resamples of questions with matched system predictions; also resample paired seeds for a hierarchical sensitivity interval. With only three seeds, characterize training uncertainty as limited and do not count thousands of questions as thousands of independent training replicates.
- **Multiplicity** — for confirmatory H1–H3 use a preregistered familywise procedure: conservatively use two-sided 98.33% intervals for each of the three hypothesis families. H3 is an intersection criterion: quality noninferiority, grounding noninferiority and speed improvement must all pass their one-sided directional bounds using those intervals. Additional ablations are exploratory, without confirmatory significance language.
- **Run failures** — stop a run for NaN/Inf loss or persistent hardware-memory failure; record all attempted settings. A hardware failure permits a same-configuration restart, but a changed microbatch/precision is a new configuration to apply consistently. Never discard a seed because its score is poor.
- **Compute ceiling** — profile one training step and one complete evaluation first; then freeze a GPU-hour ceiling in the manifest. Run A0 → A1 → A2/A3 → extensions in that priority. Omit extensions when the ceiling is reached; do not reduce seed count selectively in the most unfavorable arm. Wall-clock costs cannot be estimated responsibly before a backbone and hardware are fixed.
- **Report conclusions by mechanism** — separate gradient, gate, sparse-access, alignment and systems findings. A null H1 suggests that memory gradients were not beneficial in this configuration; a positive H1 with higher cost establishes a trade-off, not a speed advantage.

## 11. Required run artifacts and launch checklist

Each run must save: immutable configuration, source/version checksums, split and bank manifests, seed, training loss/gradient logs, complete example-level predictions, retrieval traces, failure log, and raw latency/memory measurements. Aggregate summaries must be reproducible from those records. Keep evaluation answers separate from all training and indexing scripts.

Before execution, lock:

- [ ] Backbone/tokenizer revisions, software environment and hardware.
- [ ] Dataset release/license checks, split IDs, chunking and source mappings.
- [ ] Adapter shapes, placement, gradient contract and loss implementation.
- [ ] Successful A0 leakage, retrieval and gradient checks.
- [ ] Effective bank size and sample count after capacity checks.
- [ ] Development-only tuning allowance, primary checkpoints and compute ceiling.
- [ ] Blinded grounding rubric and raters; final confirmatory sample-size justification.

## 12. Source basis and limitations

The hypotheses operationalize the manuscript's proposed mechanism and the priority gaps in `gap_memo.md`, consistent with `table_1_revised.md`. The source manuscript explicitly reports no implementation or empirical results. This protocol supplies missing design decisions; it does not imply that the paper already specified them.

Architectural comparator sources already checked for this project: Lample et al. (2019), *Large Memory Layers with Product Keys*, https://arxiv.org/html/1907.05242v2; Wu et al. (2022), *Memorizing Transformers*, https://arxiv.org/html/2203.08913v1; Guu et al. (2020), *REALM*, https://arxiv.org/html/2002.08909v1; and Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, https://arxiv.org/html/2005.11401v4. These motivate controls; this protocol does not claim to reproduce their published scores. DLI source: https://doi.org/10.2139/ssrn.6821299.

No dataset was downloaded, checkpoint selected, code executed, package installed or compute job launched to produce this protocol. Dataset availability and checkpoint compatibility remain launch checks, not verified capabilities. A 7B/13B expansion requires a separate resource profile and frozen scaling protocol.
