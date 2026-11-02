# Provenance-aware retrieval against poisoning

## Result

**Filtering untrusted documents before top-k selection recovers all 40 poisoned test answers; filtering only after selection recovers none.** The protection disappears when attackers can forge the trusted-source metadata: all 40 forged-tag cases produce incorrect answers and cite attacker documents.

These are synthetic retrieval/decoder experiments on Native Retrieval Diagnostic v1, not DLI-LLM implementation results or a test on public HotpotQA.

## Paired experiment

The unchanged original 400-example test set includes 40 poisoning episodes. Each has 32 documents: one trusted correct fact, six untrusted keyword-stuffed contradictory facts, and 25 other distractors. All methods share the original BM25 formula, the same document ordering, a five-passage total budget, and the same rule-based answer decoder. Local-only episodes do not retrieve.

- **Naive:** rank all documents, take five, then decode without trust/time checks.
- **Postfilter:** rank all documents and take five; decoder rejects untrusted/future facts and selects the latest eligible fact. This reproduces the original `bm25_policy`.
- **Trust prefilter:** mask out non-registry documents before selecting the top five; retain the policy decoder.
- **Trust + time prefilter:** also mask documents effective after the episode's as-of date before selecting five.
- **Iterative + prefilter:** trust/time mask, three first-hop passages, then two distinct second-hop passages if a discovered port enables a beacon-color query; otherwise complete the original top five.

**Scoring is controlled:** full-corpus BM25 document frequencies and similarity scores remain fixed across single-pass conditions. Only eligibility before truncation changes. This is a metadata mask over ranked candidates, not a rebuilt eligible-only index. Poison documents still influence BM25 corpus statistics, and no indexing-cost or timing benefit is claimed. An ANN implementation that obtains only five candidates and then filters them would instead reproduce the failing postfilter condition; it needs a filter-aware search or adequate candidate backfill.

## Measured scores

| Method | All-test answer EM (n=400) | Poison answer EM (n=40) | Poison abstention | Poison attacker citation |
|---|---:|---:|---:|---:|
| Naive BM25 | 70.00% | 0% | 0% | 100% |
| Postfilter BM25 | 75.75% | 0% | 100% | 0% |
| Trust prefilter BM25 | 85.75% | 100% | 0% | 0% |
| Trust + time prefilter BM25 | 85.75% | 100% | 0% | 0% |
| Iterative BM25 + trust/time prefilter | 95.75% | 100% | 0% | 0% |

The prefilter-versus-postfilter single-pass improvement is **40 recovered answers / 400 total = 10 percentage points**. Within poisoning, the paired counts are 40 improvements, zero regressions, zero ties. Every poisoning retrieval under prefiltering includes the trusted support; under postfiltering, attacker passages occupy the shortlist and the decoder can only abstain. The remaining all-test errors are not poisoning errors: single-pass prefiltering still fails two-hop composition and some paraphrases; iterative prefiltering leaves only 17 paraphrase errors.

Time prefiltering adds no answer benefit on this fixture: the policy decoder already handles the available dated facts. This does not establish equivalence at higher distractor loads.

## Forged-metadata stress test

For each of the same 40 poisoning episodes, make an alternative snapshot in which all six attacker documents claim `source=registry` and `effective_date=2026-06-15`, an eligible date later than the authentic 2026-06-01 fact. Keep texts, IDs, ordering and authentic gold answers unchanged. Store the attack IDs separately for evaluation; those annotations and gold labels are never given to the retriever/decoder.

**Every method scores 0/40 and cites attacker evidence in 40/40.** Even the postfilter method now answers incorrectly rather than abstaining.

This intentionally violates the original assumption that registry metadata is authoritative. Gold truth remains the original authenticated-world truth, not a new fact introduced by the forged tag. Thus this condition measures a compromised trust boundary; it is not an ordinary eligible registry update or a new in-distribution benchmark split. It demonstrates that an allowlist predicate on a mutable string is not source authentication. No document signatures, authenticated ingestion or learned authenticity detector were implemented.

## Implication for the proposed DLI architecture

A candidate-selection mask should act before memory values are mixed into the retrieved representation, not only after generation. With verified provenance, a softmax read could mask ineligible scores before normalization; a sparse implementation must prevent excluded records from exhausting the candidate budget. Preserve provenance through ingestion and any document-to-key/value mapping so retrieval traces remain attributable. These are proposed integration requirements, not measurements of a Transformer-layer implementation.

The forged-tag result makes authentication a separate requirement: source labels should come from a controlled ingestion boundary rather than document-authored metadata. A frozen or signed mapping of admitted document IDs to source identity is a possible next experiment, but does not by itself establish factual correctness of a trusted source.

## Reproduce and inspect

The ZIP includes this report, the new experiment script, all new outputs, and the original benchmark JSONL, generator, baseline-score CSV and pinned dependencies. After unpacking with the dependencies available:

```bash
python3 run_provenance_test.py --out rerun
```

From the workspace version, pass `--benchmark-dir user/workspace/co-scientist-outputs/native-retrieval-benchmark` and an output directory explicitly.

- `scores.csv`: 60 rows, covering original overall and ten scenario strata plus forged-tag poisoning, for five methods. Rates are fractions in [0,1]; `retrieved_count` is a mean passage count. `complete_evidence` excludes local-only and unanswerable episodes.
- `predictions.jsonl`: 2,200 records with answers, citations, retrieved IDs, attacker exposure and metric components. `attack_citation` means any cited ID belongs to the known attacker set, even if its displayed source tag is forged.
- `forged_metadata_cases.jsonl`: 40 alternative attack snapshots, with original gold labels and evaluation-only attack annotations. They are not merged into the original dataset or permitted as additional evidence in the original episodes.
- `audit.json`: input-data hash and passed checks, including reproduction of prior naive/postfilter answer scores for every original scenario and enforcement of the five-passage budget.

All 400 test episodes were retained; no parameter sweep, model training or test-set filtering was used. The original dataset and baseline scores are unchanged. These deterministic descriptive results do not establish general attack resistance, natural-language answering ability, GPU efficiency or DLI-LLM architectural superiority.
