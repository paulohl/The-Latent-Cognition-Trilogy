# Native Retrieval Diagnostic v1

A paper-derived, fully synthetic task benchmark for **Differentiable Latent Indexing in LLMs: Toward Native Retrieval as a Cognitive Function**, Paulo H. Leocadio, DOI: https://doi.org/10.2139/ssrn.6821299. The supplied 26-page PDF was read, including Appendix A. This is a generated diagnostic, not a replication, author-supplied dataset, or implementation of DLI-LLM.

## What was adapted from the paper

The main text explicitly reports no implementation or empirical validation (§2, pp. 4–5; §2.8, pp. 12–13). It defines projected hidden-state queries, dot-product scores, temperature-softmax memory reads, a sigmoid routing gate and hidden-state fusion (§§2.2–2.5, pp. 6–9). Its joint LM/retrieval loss is conceptual (§2.6, p. 11). Predictions and risks include grounding, adaptation, memory saturation, redundancy, drift and poisoning (§§3.1–3.2, pp. 13–15), plus evolving memory and routing control (§§4.2–4.4, pp. 17–18).

Accordingly, the benchmark tests **observable retrieval-dependent behavior**, not latent representations or gradient flow. The main text's dense softmax and Appendix A's optional top-k/product-quantized implementation are not silently equated. A five-passage budget is a benchmark design choice, not a reported paper parameter. Appendix A proposes 7B/13B implementations and TriviaQA, HotpotQA and BioASQ (pp. 23–24); these are future experiment suggestions, not datasets used in this paper. No such runs are claimed here.

## Dataset and task

**1,200 labeled episodes; 49,920 memory records; train/dev/test = 600/200/400.** Ten equally weighted scenarios contain 60/20/40 examples per split. Memory has 32 documents per episode, except the saturation proxy with 128. Each episode is an isolated memory snapshot, not a query against a shared global corpus. The split field, not line order, determines the split.

Given a query, local context, an as-of date, and a memory snapshot, return an exact answer or `ABSTAIN`, evidence document IDs, and a retrieval decision. Treat registry documents as authoritative, reject `untrusted` documents, exclude facts effective after `as_of`, and use the latest eligible fact for an entity/relation. Those trust and time rules are **benchmark assumptions**, not policies specified by the paper.

| Scenario | Known truth and intended diagnostic |
|---|---|
| single_hop | One eligible entity-to-port fact; direct retrieval |
| paraphrase | Harbor/stationed query wording versus base/port memory wording; limited lexical mismatch |
| two_hop | Entity → base port → beacon color, with competing color facts; evidence composition |
| redundancy | Eight identical trusted supports; any one is sufficient |
| poisoning | Six untrusted, keyword-stuffed contradictory facts compete with one trusted fact |
| update | Old, current and future contradictory facts; choose current as of 2026-06-30 |
| unanswerable | Target entity exists, but its base relation is absent; retrieve to establish absence, then abstain |
| local_only | Correct fact is supplied locally; no lookup needed |
| saturation | Same one-hop task in 128 rather than 32 documents; a small distractor-load proxy only |
| counterfactual | Same query, document IDs/order and distractors as a paired single-hop episode; exactly one correct port value changes |

There are 120 counterfactual pairs, including 40 on test. Pairs remain in the same split and are alternative snapshots, never merged into one index. Entity names and document IDs are randomly generated opaque identifiers, documents are shuffled, and no entity or world crosses splits. Surface templates are shared across splits: this is entity generalization, **not** a held-out-template or natural-language generalization benchmark.

## Schema and inference boundary

`schema.json` is a Draft 2020-12 JSON Schema; `benchmark.jsonl` has one episode per line.

| Field | Type and meaning |
|---|---|
| `id`, `split`, `world_id` | Unique episode ID; train/dev/test; disjoint-world grouping |
| `pair_id` | Counterfactual pair group, or null |
| `scenario` | One of ten diagnostic strata; evaluation-only |
| `query`, `local_context` | User question and optionally sufficient local evidence |
| `as_of` | Inclusive eligibility cutoff, ISO date |
| `memory` | Array of `{id,text,source,effective_date}` documents |
| `labels.answer` | Exact port identifier, beacon color, or `ABSTAIN` |
| `labels.answerable` | Whether eligible evidence/local context determines an answer |
| `labels.retrieval_required` | Whether external memory must be consulted; true even for missing-evidence episodes |
| `labels.hop_count` | 0 for local/absent evidence, 1 for lookup, 2 for composition |
| `labels.acceptable_evidence_sets` | Alternative minimal support sets. `[[]]` means local evidence; `[]` means no answer support exists |
| `labels.reason` | `memory_evidence`, `local_context`, or `missing_evidence` |
| `provenance` | Synthetic status, generator version and seed |

**Do not expose `id`, `split`, `world_id`, `pair_id`, `scenario`, `labels` or `provenance` to the evaluated model.** IDs contain scenario names. Pass only `query`, `local_context`, `as_of` and document-level memory fields. Document IDs are citation handles, not semantics. For training, labels can supervise retrieval, answering and gate classification; test labels must remain evaluator-only. A caller should define the trust/time policy in the system instruction. A real DLI adapter may encode these documents into keys/values; the gold labels remain document-level, not fabricated latent-vector targets.

Expected response: `{answer: string, evidence_ids: string[], retrieve: boolean}`. Normalize answer whitespace/case if evaluating a free-form model; the supplied extractive decoder already emits canonical strings. Preserve port identifiers exactly.

## Executed baselines

All results below are **measured on the generated test set, n=400**, without model training, network access, pretrained embeddings or LLM calls. All retrieval baselines use a shared deterministic decoder that understands the synthetic fact grammar. They are retrieval diagnostics, **not external-RAG LLM performance estimates**. The grammar and temporal/provenance policy are known in advance, not learned from test labels.

| Baseline | Answer EM | Grounded EM | Complete evidence* | Mean passages read |
|---|---:|---:|---:|---:|
| No memory, local-only decoder / otherwise abstain | 20.00% | 20.00% | 0.00% | 0.0 |
| BM25 top-5, naive decoder | 70.00% | 70.00% | 69.69% | 4.5 |
| BM25 top-5, policy decoder | 75.75% | 75.75% | 69.69% | 4.5 |
| TF-IDF top-5, policy decoder | 80.00% | 80.00% | 75.00% | 4.5 |
| Iterative BM25, policy decoder, total budget 5 | 85.75% | 85.75% | 82.19% | 4.5 |
| Full-memory reference, policy decoder | 100.00% | 100.00% | 100.00% | 38.4 |

*Complete evidence is measured only on 320 memory-answerable episodes; success means any acceptable support set is fully retrieved. The full-memory reference reads all available memory, violates the five-document baseline budget, and is a label-consistency ceiling, not a competitive system. All retrievers skip local-only memory. BM25 uses k1=1.5, b=0.75 with local document-frequency statistics; TF-IDF uses scikit-learn defaults fit on the episode memory. Using the test memory to build its index is necessary access to the evaluated corpus, not supervised fitting to test answers. No thresholds or parameters were selected on test or dev.

Iterative BM25 retrieves three documents, extracts a first-hop port if present, then uses that discovered value with “beacon color” to retrieve two further distinct documents. Otherwise it completes the original top-5. It never uses the gold hop count or scenario. The naive decoder chooses the first matching fact without trust/time checks; the policy decoder rejects untrusted/future facts and prefers the latest eligible date. Neither uses labels during prediction.

### Findings to act on

- **Second-hop evidence:** single-pass BM25 and TF-IDF each score 0/40 on two-hop answers; iterative BM25 scores 40/40 at the same total passage budget. This supports a useful task for studying internal query refinement, not a finding about DLI itself.
- **Poisoning before decoding:** all budgeted methods score 0/40 on poisoning. Naive BM25 cites untrusted evidence in all 40 cases; the policy variants abstain instead. Filtering after top-k prevents unsafe citations but cannot recover trusted evidence excluded from the shortlist. Provenance-aware candidate filtering is the next baseline to add.
- **Temporal policy:** naive BM25 scores 17/40 on updates versus 40/40 with policy checks. Memory access alone does not define which conflicting fact should govern an answer.
- **Paraphrases:** BM25 scores 23/40 versus TF-IDF 40/40. This is a narrow lexical perturbation; it is not evidence of broad semantic understanding.

These are descriptive deterministic scores from one seed. No significance or architecture-superiority claim is made. Since paired snapshots are dependent, any future confidence intervals should resample by `world_id`, not episode.

## Metrics and gate interpretation

- **Answer EM:** exact string equality, including correct abstention. The no-memory baseline gets local-only and unanswerable episodes correct, so 20% is an intentionally informative floor.
- **Grounded EM:** correct answer plus cited IDs containing a complete acceptable support set; correct abstention is accepted without positive evidence. Extra citations are not penalized by this metric.
- **Evidence recall:** maximum fraction recovered over acceptable minimal support sets. **Complete evidence:** any set recovered in full. Both exclude local and unanswerable tasks. For iterative retrieval these are recall-at-total-budget, not one-shot recall@5.
- **Gate accuracy:** equality to `retrieval_required`; the baselines' local-context-presence rule gets 100% by construction. No-memory gets 10%. This deliberately easy gate task does not validate a learned sigmoid gate. A continuous integration gate from the paper is not the same as a decision to skip a retrieval call.
- **Poison citation rate:** fraction of all episodes citing an untrusted document; use the poisoning-specific CSV row for the attack-conditional rate.

For an actual DLI implementation, additionally log gate activations by layer/token, softmax support mass/entropy, retrieved document provenance, answer loss gradients reaching Wq/Wg/keys, memory size, retrieval calls and matched end-to-end GPU timings. Those architectural measurements cannot be inferred from text-only outputs and have not been simulated as experimental results.

## Reproduce and validate

From an unpacked bundle, with Python 3.10+ and the versions in `requirements.txt` available:

```bash
python3 generate_and_score.py --out rerun --seed 6821299
```

The script generates the dataset, schema, scores, predictions, heatmap, audit and manifest. No downloads or paid services are needed. `predictions.jsonl` contains 2,400 test episode/method records with predicted answers, cited/retrieved IDs and metric components. The CSV contains overall and ten per-scenario rows for each of six methods (66 rows). `manifest.json` records SHA-256 hashes for the data, schema, scores and validation report. `validation.json` documents passed invariants. Generator checks use Python assertions; do not run with `python -O`.

Checks cover unique episode and per-memory document IDs, support-ID resolution, full-memory recovery of every answer/support, disjoint worlds/entities across splits and changed answers for identical paired queries. Counterfactual snapshots deliberately reuse document IDs within their pair. These are programmatic invariants, not independent human annotation or a full external JSON Schema validator run.

## Scope, realism and omitted experiments

Synthetic facts provide exact truth and prevent pretrained-world-knowledge shortcuts. The fictional station/port domain is a neutral test fixture: the paper does not prescribe a deployment domain. No public example data was necessary or mixed in; no third-party data license or download is required. The supplied paper is not redistributed in the bundle. The seed, trust policy, entity layout, templates and attack construction are disclosed, so this is an open diagnostic rather than a contamination-resistant leaderboard.

Limits are substantial: short templated passages, only two relations, an explicit local-context gate cue, fixed trust markers, random opaque entities, at most two hops, 32–128-document memories and a rule-based answerer. Same-entity wrong-relation distractors and cross-entity same-relation distractors add interference, but they do not simulate shared latent-space geometry, trained-key saturation, cross-layer drift, realistic prompt injection, long-context language coherence or natural biomedical QA. The saturation stratum is too small to establish scaling behavior; direct-identifier lookup is intentionally easy. Redundancy is exact duplication, not semantic duplication.

No 7B/13B model, differentiable Transformer block, product quantization, GPU latency/memory experiment, few-shot training, hallucination evaluation or DLI ablation was run. Necessary next experiments are to attach a real DLI model and matched external-retrieval model, add natural QA with audited evidence, and sweep memory size/poison rates with predeclared settings. The benchmark can support those experiments; it does not establish the paper's efficiency or grounding predictions.

## Follow-up: provenance-aware retrieval

The executed follow-up in `../provenance-poisoning/REPORT.md` compares eligibility masking before top-k with the original post-retrieval filter at the same five-passage budget. On the 40 poisoned test episodes, prefiltering recovers 40/40 answers versus 0/40 after filtering. Overall single-pass answer EM rises from 75.75% to 85.75%; iterative retrieval plus prefiltering reaches 95.75%. When attacker documents forge trusted-source tags, every method fails all 40 cases. These synthetic results isolate candidate selection and the trust boundary, not DLI implementation performance. The original dataset and baseline CSV remain unchanged; the new report, script, stress snapshots and scores are in the separate `../provenance-poisoning.zip` bundle. No public HotpotQA examples have been added in this follow-up.

## Bundle contents

- `benchmark.jsonl`: all 1,200 episodes and gold labels.
- `schema.json`: machine-readable schema.
- `generate_and_score.py`: standalone generator, integrity checks, retrievers, decoder and scoring.
- `requirements.txt`: recorded package versions.
- `baseline_scores.csv`: overall and stratum-specific scores.
- `predictions.jsonl`: per-test-episode outputs for every method.
- `baseline_heatmap.png`: test answer EM by method/scenario.
- `validation.json`: integrity audit.
- `manifest.json`: provenance, sizes and content hashes.
- `README.md`: task specification, assumptions and interpretation.
