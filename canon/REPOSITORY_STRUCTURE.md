# Repository Structure

**Snapshot reviewed: 7 November 2026.** This is a navigational map of the public GitHub working tree, not a claim of source-to-hardcover parity.

```text
The-Latent-Cognition-Trilogy/
├── README.md                 Research overview and publication identity
├── LICENSE.txt               Software license (scope review needed)
├── main.tex                  LaTeX build orchestrator
├── master.bib                Bibliography database
├── trilogy_macros.sty        Local LaTeX style/macros
├── sections/
│   ├── frontmatter/          Preface, prologue, program orientation
│   ├── 04_trilogy_overview.tex
│   ├── 05_vol1.tex           Memory Fields
│   ├── 06_vol2.tex           Symbol Fields
│   ├── 07_vol3.tex           Routing Fields
│   └── backmatter/           Conclusion and appendices
├── figures/                  Diagrams and other assets
├── canon/                    Canon, terminology, works, submission status
├── companion_works/
│   ├── architectural_foundation/
│   └── hypothesis/
│       ├── hypothesis-01/
│       ├── hypothesis-02/
│       └── hypothesis-03/
├── docs/                     Architecture and research documentation
├── VERSION/                  Build notes, version history, changelog
├── archive/                  Historic materials
├── Compare-retrieval-architectures/
├── benchmark-native-retrieval/
├── benchmark_incident_classifiers/
├── benchmark_phishing_response_model/
├── build_a_phishing_test_set/
├── native-retrieval-benchmark/
├── newt_text/
└── provenance-poisoning/    Parallel experiment and audit workspaces
```

The repository also contains top-level audit and comparison outputs (`audit.html`, `comparison.csv`, `comparison.png`, `grouped_tests.csv`, `split_leakage.csv`). **Their ownership and incoming links should be checked before relocating them**; the main README should not mistake benchmark artifacts for the published manuscript.

## Publication source integrity

The inspected `main.tex` still imports `sections/backmatter/10_hyp1_manifest`, which was excluded from the KDP submission. This tree therefore represents the **current repository working copy**, not a verified, complete physical-edition source snapshot. See [submission status](SUBMISSION_STATUS.md) and [build notes](../VERSION/BUILD.md).

## Repository maintenance rules

- Maintain the research canon, versioned scientific source, and publication outputs as distinct records.
- Preserve historic research evidence when moving or restructuring files; avoid silent deletions.
- Build print and digital editions from reviewed content using separate production controls.
- Do not treat experimental benchmarks as validated support for unrelated theoretical propositions.
