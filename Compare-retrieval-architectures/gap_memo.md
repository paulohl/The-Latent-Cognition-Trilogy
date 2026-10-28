# DLI-LLM: retrieval architecture gap memo

**Prepared 28 October 2026 • Focused evidence map, not a benchmark or exhaustive review**

## Bottom line

DLI-LLM is a **conceptual transformer-integrated associative key–value memory proposal**, not an evaluated retrieval system. Its strongest testable distinction is the proposed combination of trainable retrieval, a content-dependent fusion gate, and a shared token/document memory space. Transformer-layer memory integration alone is already present in close predecessors. The most informative first comparisons are **Product-Key Memory (PKM), Memorizing Transformers, and REALM**, rather than only an externally orchestrated RAG pipeline.

The accompanying workbook maps DLI-LLM and nine related architectures. It separates architecture, gradient boundaries, data, reported findings, code assumptions, and untested conditions. These are heterogeneous studies; their reported metrics are **not a cross-paper leaderboard**.

## What this paper actually establishes

The supplied 26-page manuscript explicitly disclaims empirical implementation and benchmark validation (pp. 2–4, 12–13, 19). It defines a hidden-state query, dot-product memory scores, temperature-scaled dense softmax, a weighted value read, and sigmoid-gated fusion (pp. 6–9). It proposes inserting retrieval blocks after self-attention, with a joint objective `L_LM + lambda L_retrieval` whose retrieval term is not operationally defined (pp. 10–11).

Appendix A proposes, but does not report, 7B/13B prototypes and evaluation on TriviaQA, HotpotQA and BioASQ, measuring latency, GPU memory, retrieval recall and hallucination (pp. 23–24). Those datasets and model sizes are **planned conditions**, not observed data. The main text predicts improved efficiency, grounding, adaptation and long-context coherence (pp. 13–15); no numerical effect estimate can be extracted. No implementation or repository is identified in the supplied manuscript.

Accordingly, the requested comparison was adapted into an architectural evidence map plus a falsifiable evaluation plan. No sample scores were invented, and no models were run.

## Priority gaps and the experiments that resolve them

### P0 — Correct the closest-prior-work comparison

Table 1 calls Memorizing Transformers “Learnable memory tokens” and says it has “No unified latent retrieval pathway” (p. 12; table checked in the page image). Wu et al. instead describe cached hidden-state key–value pairs, approximate nearest-neighbor lookup, attention over selected values, and learned gated fusion within a transformer layer (§3.1). The differentiating issue is the **non-differentiable stored memory**, not absence of an internal retrieval pathway. RMT, by contrast, does introduce special memory tokens.

PKM is absent from DLI-LLM’s comparison despite being a close mathematical precedent: learned queries, trainable keys/values, sparse softmax-weighted reads, and transformer-layer integration (Lample et al., §§3–4). Its product-key construction should not be conflated with compression by product quantization. REALM also shows that an external document index need not imply independently optimized retrieval: the language-model objective trains the retriever, with explicit index-refresh machinery (§3.3).

**Action:** Replace binary “internal versus external” labels with the workbook’s separate axes: memory location, memory content, selection operation, gradient destination, update policy, and evidence provenance. Test DLI against PKM and a stopped-gradient memory with the same backbone, memory capacity and training budget. This is a positioning correction, not a finding that the proposed combination has no contribution.

### P0 — Resolve the dense/sparse gradient contract

The main equations read all N memories with dense softmax (p. 7). Appendix A instead proposes top-k lookup into a product-quantized table and cross-attention fusion (p. 23). These are materially different computational specifications. Dense reads are differentiable with respect to continuous keys, values and query projections when these are trainable. Hard top-k membership and quantization assignment do not inherit that property merely because selected scores pass through softmax.

**Action:** Specify which memory tensors are parameters, which are encoder outputs, where gradients stop, how keys are refreshed, and whether sparse selection uses a relaxation, estimator, or ordinary selected-score gradients. Compare dense read on a small bank, exact top-k, ANN top-k, and quantized ANN. Log retrieval recall against exact search, LM loss, QA accuracy, gradient norms, and training failures. Include a stopped-gradient ablation to isolate whether differentiability itself adds value.

### P0 — A fusion gate is not a retrieval-skipping policy

In Algorithm 1, `r_t` is computed before `g_t` (p. 9). A small gate therefore suppresses the retrieved contribution **after paying the read cost**. The auxiliary head predicting when evidence is needed and sparsity loss appear in Appendix A, but do not have a corresponding operational specification in the main algorithm.

**Action:** Add an explicit pre-read routing decision if fewer calls are part of the efficiency claim. Compare always-read, post-read fusion gating, and conditional pre-read routing. Report actual calls per generated token alongside end-to-end p50/p95 latency. A benefit that disappears after including routing, host/device transfer or sharding overhead does not support a latency advantage.

### P1 — Shared dimensions do not establish shared semantics

The main text assumes token states and ingested document embeddings occupy a compatible latent space (pp. 5–6). It does not define alignment supervision, document encoder training, cross-layer adapters, or how old embeddings stay compatible after model updates. A single document vector also need not preserve enough evidence for multi-hop reasoning or source citation.

**Action:** Compare token-only, document-only, and mixed memory; frozen versus jointly trained document encoders; shared versus layer-specific projections. Test newly indexed documents, corpus changes after training, and conflicting old/new facts. Report evidence recall and answer support separately. Retain source document/chunk identifiers so latent retrieval can be audited.

### P1 — Internal retrieval does not establish cheaper retrieval

**Analytical implication, not a reported result:** the dense scoring and weighted-read operations cost O(Nd) per query; using them in L layers over T token positions adds O(LTNd) read work, apart from projections and the original transformer. A raw dense key/value bank uses approximately `2 × N × d × bytes_per_element` storage before optimizer state or activations. As an illustrative calculation, N=1 billion, d=4096 and two-byte elements require about **16.4 TB decimal** for keys plus values; this is not a proposed deployment specification. Quantization, sparse reads and sharding need separate accounting.

Memorizing Transformers reports a relevant counterweight: for an approximately 200M-parameter model, training step time rises from 0.2 s without memory to 0.25 s with 8K memory and 0.6 s with 65K, on TPUv3 (§4.2). These are training-step timings, **not decoding latency** and not estimates for DLI.

**Action:** Sweep memory capacity and retrieval-layer count. Include indexing/ingestion time, peak GPU memory, host RAM, transfer time, and throughput. Match hardware, batch size, prompt/output lengths and retrieved-evidence budget; show quality–cost curves, not a single speed ratio.

### P1 — Grounding, reasoning and safety require distinct endpoints

Lower perplexity or better QA exact match alone does not establish fewer unsupported claims, reliable multi-hop reasoning, or a general cognitive retrieval faculty. The paper identifies poisoning, drift and saturation risks (pp. 13–17), but supplies no tests.

**Action:** Use HotpotQA answer EM/F1 plus supporting-fact/joint scores; TriviaQA for single-hop factual answers; and a version-pinned BioASQ task for domain transfer. Add answerable/unanswerable cases, contradictory evidence, distractors, stale facts, duplicated memories and poisoned chunks. Score unsupported factual claims against retrieved evidence with blinded adjudication; record abstention/calibration and deletion success. Separate absent evidence, failed retrieval, ignored evidence and incorrect reasoning.

## Minimal decisive evaluation

1. **Mechanism pilot:** use a tractable open decoder and small exact-search bank before the appendix’s 7B/13B scale. Train no-memory, PKM-style memory, stopped-gradient cached memory, dense DLI, and sparse DLI variants. This pilot is a recommendation, not an experiment already performed.
2. **Matched QA comparison:** use the same backbone and corpus for retrieve-then-generate and internal-memory variants. Fix the train/dev/test splits and evidence budget; remove answer leakage and near duplicates. Use an oracle-evidence condition to separate retrieval errors from generation errors.
3. **Ablations:** remove the gate; freeze keys/values; disable retrieval loss; separate token/document banks; vary retrieval layers, k and temperature. Use at least three seeds where training variance matters, paired confidence intervals on QA differences, and a held-out split for configuration selection.
4. **Success criterion:** pre-register either higher supported-answer quality at matched latency/memory or lower cost at matched supported-answer quality. Claim joint-training or gate benefits only when their matched ablations improve the relevant endpoint. Treat both a null effect and a Pareto trade-off as useful results.

## Evidence boundaries and sources

The supplied DLI manuscript was read in full; Table 1 was visually checked. External sources are **primary arXiv pages/full text and repository documentation**, accessed 28 October 2026. Full-text method inspection concentrated on PKM, Memorizing Transformers and REALM. Other rows use verified abstracts and state that limited depth. Repository existence/readme inspection is not an execution, dependency audit, checkpoint check or license clearance. CiteRight report 1672583 completed its comparator search and independently returned PKM, REALM, Memorizing Transformers and Titans, supporting their inclusion. Its separate gradient-distinction query remained unstarted; that part of the cross-check is incomplete. Numerical findings here come from the primary sources, not CiteRight. CiteRight also returned *Transformer Memory as a Differentiable Search Index* (Tay et al., 2022; https://doi.org/10.48550/arxiv.2202.06991), describing a query-to-document-ID model with corpus information encoded in parameters. It is a useful terminology contrast, not evidence that hard discrete selection has smooth gradients; it was not expanded into the matrix.

- **DLI:** Paulo H. Leocadio (2026), *Differentiable Latent Indexing in LLMs: Toward Native Retrieval as a Cognitive Function*. Supplied manuscript; https://doi.org/10.2139/ssrn.6821299.
- **PKM:** Lample et al. (2019), *Large Memory Layers with Product Keys*. §§3–4, https://arxiv.org/html/1907.05242v2. Code: https://github.com/facebookresearch/XLM.
- **Memorizing Transformers:** Wu et al. (2022), *Memorizing Transformers*. §§3–4 and Appendix A.1, https://arxiv.org/html/2203.08913v1. Code: https://github.com/google-research/meliad.
- **REALM:** Guu et al. (2020), *REALM: Retrieval-Augmented Language Model Pre-Training*. §§3–4, https://arxiv.org/html/2002.08909v1. Code: https://github.com/google-research/language/tree/master/language/realm.
- **RETRO:** Borgeaud et al. (2021 preprint; 2022 revision), *Improving language models by retrieving from trillions of tokens*. Abstract, https://arxiv.org/abs/2112.04426v3.
- **RAG:** Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. Abstract, https://arxiv.org/abs/2005.11401.
- **kNN-LM:** Khandelwal et al. (2019 preprint; ICLR 2020), *Generalization through Memorization: Nearest Neighbor Language Models*. Abstract, https://arxiv.org/abs/1911.00172; code/readme: https://github.com/urvashik/knnlm.
- **RMT:** Bulatov, Kuratov & Burtsev (2022), *Recurrent Memory Transformer*. Abstract, https://arxiv.org/abs/2207.06881; code/readme: https://github.com/booydar/recurrent-memory-transformer.
- **Titans:** Behrouz, Zhong & Mirrokni (2025 arXiv identifier; submitted 31 December 2024), *Titans: Learning to Memorize at Test Time*. Abstract, https://arxiv.org/abs/2501.00663. Unofficial implementation only in this check: https://github.com/lucidrains/titans-pytorch.
- **Persistent memory:** Sukhbaatar et al. (2019), *Augmenting Self-attention with Persistent Memory*. Abstract and contextual discussion in Wu et al. §2, https://arxiv.org/abs/1907.01470.

This is a deliberately selected set of close and contrasting architectures, not an exhaustive survey through October 2026. DNC/NTM are acknowledged antecedents already cited by DLI; Perceiver IO and Hyena were not expanded because they are less direct controls for indexed latent-memory access. Missing numbers are marked as not extracted rather than estimated. No inference about DLI superiority follows from another model’s results.
