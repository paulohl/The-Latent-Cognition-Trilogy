# Public HotpotQA add-on v1

**100 real HotpotQA development examples**, kept separate from the original 1,200 synthetic episodes. The sample contains 79 bridge and 21 comparison questions, 992 context paragraphs and 243 annotated supporting facts. All 100 have the upstream difficulty label `hard`.

This adds natural questions, Wikipedia passages and human-annotated supporting sentences to the task named in Appendix A of the DLI paper. It does not implement DLI-LLM or evaluate a language model.

## Source, selection and license

The official dataset is described at https://hotpotqa.github.io/ and its schema at https://github.com/hotpotqa/hotpot#json-format. The official download hostname was unavailable during discovery. We therefore used the first 100 complete records from the development distractor file at the revision-pinned mirror:

https://huggingface.co/datasets/namlh2004/hotpotqa/resolve/7e54db4656209750ff487f6fdf8e39a66dba136b/hotpot_dev_distractor_v1.json

**All seven original fields and all paragraph/sentence text and evidence indices were independently cross-checked against the first 100 validation records served by `hotpotqa/hotpot_qa`, and match exactly after schema normalization.** That second service response was live, not revision-pinned; `source_crosscheck.json` records its URL and the saved sample's hash. Byte identity to the inaccessible original-host file was not checked. `hotpotqa_source_sample.json` preserves the original-format 100-record sample for offline reproduction.

Selection is a **nonrandom prefix convenience sample**, not a representative sample or an official test set. No examples were filtered by labels, answer correctness or retrieval results. Upstream validation remains `dev`; none is relabeled as train/test. No overlap guarantee is made across HotpotQA questions or Wikipedia entities. Keep this sample out of model training if using it for evaluation; public development data may already be present in pretrained-model corpora.

**Attribution:** Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W. Cohen, Ruslan Salakhutdinov and Christopher D. Manning. *HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering*. EMNLP, 2018. Dataset and adapted data/preview: **CC BY-SA 4.0**, https://creativecommons.org/licenses/by-sa/4.0/ . Copyright HotpotQA Team. Preserve attribution, the license link and change notices when redistributing; distributed data adaptations remain under that license. No claim is made that upstream data becomes unrestricted synthetic material.

Changes here: prefix subset selection, native-retrieval envelope, paragraph citation IDs, zero-based sentence mappings and derived paragraph support labels. Questions, answers, original paragraph titles, sentence strings and official supporting-fact pairs are unchanged in the saved source. Paragraph `text` concatenates original sentence strings; use `sentences` for exact segmentation.

## What is preserved—and what is not invented

Distractor mode normally provides ten candidate paragraphs, including evidence and distractors. **99 examples have ten paragraphs; one has two**, as present in both checked sources. No artificial distractors were added or records discarded. Retrieval at budget five therefore returns only two passages for that one case.

Each source `supporting_facts` pair `[title, sentence_index]` maps to the corresponding paragraph and original zero-based sentence. All 243 references resolve. Paragraph-level evidence sets contain every distinct paragraph referenced by these annotations. These are annotated supports, not an exhaustive enumeration of every possible sufficient proof. Exact reasoning-hop counts are not inferred from paragraph counts.

We do not fabricate trust labels, effective dates, abstention labels or adversarial attacks for real Wikipedia text. `source=wikipedia` is provenance, **not authenticated trust or a guarantee of truth/currentness**. All examples are labeled answerable and retrieval-required under a context-grounded evaluation protocol; that does not mean a pretrained model cannot already know the answer. This add-on does not test conditional gating or missing evidence.

## Adapted schema and model boundary

`hotpotqa_schema.json` defines a separate format. It intentionally does not satisfy the original synthetic schema's fixed scenario enum, 32-document minimum or temporal metadata requirements. Existing synthetic rule-based decoders cannot answer these natural-language examples and were not run against them.

| Field | Meaning |
|---|---|
| `id`, `split`, `scenario` | Original question ID, `dev`, and `hotpotqa_bridge`/`hotpotqa_comparison`; evaluator metadata |
| `query`, `local_context` | Original question and empty local context |
| `memory[]` | `{id,title,text,sentences,source}`; IDs `p00`… are scoped to an episode |
| `labels.answer` | Unchanged official answer, including yes/no where applicable |
| `labels.acceptable_evidence_sets` | One paragraph-ID set derived from annotated supporting facts |
| `labels.supporting_facts[]` | `{document_id,title,sentence_index}` preserving source annotations |
| `labels.question_type`, `difficulty` | Original bridge/comparison and difficulty strata |
| `provenance` | Source URL/revision reference, original ID/index, upstream split, license and adaptation version |

**Only pass `query`, `local_context` and `memory` to a model.** Hide IDs at episode level, scenario, labels and provenance. Paragraph IDs and sentence indices may be exposed as citation handles. Models must not receive `supporting_facts` or official answers.

For future QA evaluation, request `{answer, evidence_ids, supporting_facts, retrieve}`. Export answers under the official `answer` map and sentence citations under `sp`, keyed by original question ID; translate paragraph IDs back to titles. Use the official HotpotQA evaluator for answer/support/joint metrics. This add-on currently measures retrieval only: no LLM endpoint or prototype is connected, and no answer accuracy is reported.

## Executed retrieval baselines

Four methods rank the original episode-local candidate paragraphs: original context order, seeded random order, BM25 (k1=1.5, b=0.75), and scikit-learn default TF-IDF cosine similarity. BM25 and TF-IDF index title plus paragraph text. TF-IDF and BM25 corpus statistics are fitted to the supplied episode memory, not gold labels. Random order uses a reproducible per-question seed. No parameter tuning or training was performed.

| Method | Paragraph recall @2 | Complete support @2 | Paragraph recall @5 | Complete support @5 |
|---|---:|---:|---:|---:|
| Original context order | 14.5% | 1% | 49.0% | 21% |
| Seeded random | 27.0% | 7% | 59.0% | 35% |
| BM25 | 60.5% | 31% | 85.5% | 72% |
| TF-IDF | 60.0% | 30% | 81.0% | 63% |

Scores are macro averages over 100 questions, measured at up-to-two or up-to-five passages. **Paragraph recall** is the fraction of distinct annotated support paragraphs retrieved. **Complete support** requires all such paragraphs to be present. **Support sentence availability**, included in the CSV, is the fraction of annotated supporting sentences whose entire parent paragraphs were retrieved: it is not predicted sentence accuracy, evidence precision or official supporting-fact F1.

The difference between BM25's 85.5% paragraph recall and 72% complete-support recovery at five passages leaves a useful evidence-composition challenge for a DLI prototype. These retrieval-only development-sample scores must not be averaged with the synthetic answer-accuracy scores or compared directly with official HotpotQA leaderboard answer/support scores. One observed seeded random ranking is not an expected-chance calculation or a significance test. Gold supports serve only for scoring after ranking.

## Reproduce and files

The ZIP contains source data, adapted data, schema, script, pinned dependencies, scores, traces, audits and this guide. With dependencies available, reproduce offline after unpacking:

```bash
python3 add_hotpotqa.py --source-json hotpotqa_source_sample.json --out rerun --n 100
```

Omit `--source-json` to stream only enough of the revision-pinned mirror for the prefix sample; the parser stops after the requested count and caps transfer at 8 MiB. Offline reproduction does not repeat the independently recorded live-service cross-check.

- `hotpotqa_episodes.jsonl`: 100 adapted evaluation episodes.
- `hotpotqa_source_sample.json`: original-format public sample, also usable with the official evaluator.
- `hotpotqa_schema.json`: separate JSON Schema for the add-on.
- `EXAMPLES.md`: readable first five questions, gold answers and exact supporting sentences; evaluator-only.
- `retrieval_scores.csv`: 24 overall/type/method/budget score rows.
- `retrieval_predictions.jsonl`: 800 ranking outputs with paragraph/support coverage.
- `provenance_and_validation.json`: source, license, sample composition, integrity checks and content hashes.
- `source_crosscheck.json`: exact-match check against `hotpotqa/hotpot_qa` validation data.
- `add_hotpotqa.py`, `requirements.txt`: adaptation/scoring script and package versions.

Programmatic validation checks IDs, source context/title integrity and every supporting sentence index. This is not new human adjudication. The original synthetic dataset, its scores and provenance-poisoning experiments remain unchanged.
