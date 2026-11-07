# The Latent Cognition Trilogy

**Memory Fields · Symbol Fields · Routing Fields**  
*A theoretical research program in retrieval-native memory, symbolic stabilization, and hierarchical computational coordination.*

**Paulo H. Leocadio** · **Zinnia Labs** · **Zinnia Labs Publishing**  
First Hardcover Edition, 2026 · A research imprint of Zinnia Holdings LLC

> **Research proposition:** Memory, abstraction, and routing should be investigated as coupled architectural mechanisms—not treated solely as isolated model features or independent optimization pipelines.

## Publication identity and provenance

**Earlier research record → Current research record → First hardcover edition**

| Stage | Persistent identifier | Record |
| :-- | :-- | :-- |
| **Previous research DOI** | [10.13140/RG.2.2.32449.11363](https://doi.org/10.13140/RG.2.2.32449.11363) | Earlier ResearchGate research record |
| **Current research DOI** | [10.13140/RG.2.2.29958.74561](https://doi.org/10.13140/RG.2.2.29958.74561) | Current research record, identified in the hardcover |
| **First Hardcover Edition (2026)** | **ISBN 979-8-234-29378-7** | Print-edition identifier; Zinnia Labs Publishing |

**Identification rule:** This chain documents the publication lineage. A DOI identifies a research record; an ISBN identifies a book edition. The ISBN does **not** supersede or redirect either DOI. The related foundational DLI-LLM paper has its **own**, separate SSRN DOI: [10.2139/ssrn.6821299](https://doi.org/10.2139/ssrn.6821299).

**Status — 7 November 2026:** The hardcover manuscript was **submitted to Amazon KDP for review**, and a physical proof was ordered. KDP review, retail availability, and physical-proof acceptance must not be inferred from submission. No Kindle edition has been released.

## What this repository represents

The Trilogy develops a structured, falsifiable architectural investigation into the internal organization of artificial systems. Its core object is a coupled operator configuration:

$$\mathcal{A} = (M, S, R)$$

| Operator | Volume | Research question |
| :-- | :-- | :-- |
| **M — memory** | **I. Memory Fields** | Can retrieval be modeled as an intrinsic, differentiable operation over structured latent memory rather than only as an external service? |
| **S — symbols** | **II. Symbol Fields** | Under what conditions can compressed latent representations become stable, reusable, functionally meaningful primitives? |
| **R — routing** | **III. Routing Fields** | Can hierarchical, context-conditioned routing coordinate specialized computation while preserving locality and coherence? |

The volume order **M → S → R** is an analytical sequence, **not** a claim of a one-way execution pipeline. The program investigates reciprocal coupling, bounded scaling, failure modes, and conditions under which the proposed mechanisms could be falsified.

### Scientific scope

The hardcover is a **theoretical and architectural research work**. Its mathematical formulations, predicted behaviors, and evaluation protocols are **not presented as empirically validated results**. Publication through an independent imprint does not constitute independent peer review. The repository distinguishes hypotheses, architectural specifications, preliminary investigations, and verified experimental evidence.

## The wider research canon

The Trilogy is the **main theoretical sequence** of a larger research program; it is neither the entire canon nor a container for every related paper.

- **Architectural foundation:** *Differentiable Latent Indexing in LLMs: Toward Native Retrieval as a Cognitive Function* (DLI-LLM). This separate paper develops the retrieval-native systems premise and has an SSRN record at [10.2139/ssrn.6821299](https://doi.org/10.2139/ssrn.6821299).
- **Main sequence:** *The Latent Cognition Trilogy* — Memory Fields, Symbol Fields, and Routing Fields.
- **Companion hypotheses:** distinct satellite works that isolate supporting claims, constraints, or extensions; they are not additional volumes or substitutes for the main sequence.
- **Parallel investigations:** the repository also contains benchmarking and applied-research directories. Their results should be interpreted within their own documented datasets, controls, and limitations, not automatically as validation of the Trilogy.

For the formal hierarchy, terminology, and work register, see the [canon](canon/README.md), [canonical definitions](canon/CANON.md), and [works register](canon/WORKS_REGISTER.md).

## Repository navigation

| Path | Purpose |
| :-- | :-- |
| [`main.tex`](main.tex) | LaTeX build orchestrator in the GitHub working tree |
| [`trilogy_macros.sty`](trilogy_macros.sty) | Local LaTeX macros and formatting support |
| [`sections/`](sections/) | Manuscript content and front/back matter |
| [`figures/`](figures/) | Illustrations used by the manuscript |
| [`master.bib`](master.bib) | BibTeX reference database |
| [`canon/`](canon/) | Research-program hierarchy, terminology, and status records |
| [`companion_works/`](companion_works/) | Separate foundational and hypothesis materials |
| [`docs/`](docs/) | Architecture and additional research documentation |
| [`VERSION/`](VERSION/) | Build notes, version record, and change history |
| [`archive/`](archive/) | Historical materials; not the publication master |

**Build documentation:** [VERSION/BUILD.md](VERSION/BUILD.md)  
**Publication status:** [canon/SUBMISSION_STATUS.md](canon/SUBMISSION_STATUS.md)  
**Change history:** [VERSION/changelog.md](VERSION/changelog.md)

### Reproducibility and edition integrity

**The checked-in `main` branch has not yet been confirmed as source-identical to the final PDF submitted to KDP on 7 November 2026.** In particular, the currently inspected `main.tex` still references an archived Hypothesis 1 production manifest that was excluded from the submitted hardcover. Do not label a newly compiled PDF as the *First Hardcover Edition* merely because it builds successfully; source parity, figures, pagination, and the submitted proof must first be verified.

The scientific source is intended to support multiple **publication targets** without conflating them: print-optimized PDF for the hardcover; a future, separately validated reflowable EPUB for Kindle. Kindle conversion is a **planned build**, not a currently published edition.

## How to cite and distinguish records

For the research record, use the **current DOI** above. For the hardcover, use the assigned **ISBN** and its actual publication status. Cite the DLI-LLM foundational paper using its separate SSRN DOI; do not transfer that identifier to the Trilogy.

**Suggested manuscript-stage citation:** Leocadio, Paulo H. (2026). *The Latent Cognition Trilogy*. Zinnia Labs Publishing. First Hardcover Edition, submitted for publication. ISBN 979-8-234-29378-7. Current research record: DOI 10.13140/RG.2.2.29958.74561.

This citation should be updated when the publication is approved and the retail record is live.

## Rights, critical examination, and support

© 2026 Paulo H. Leocadio. The hardcover carries an **all-rights-reserved** notice. The repository also contains [`LICENSE.txt`](LICENSE.txt), an MIT license referring to software and associated documentation. **These notices are not interchangeable; the applicable scope for text, figures, and code requires explicit clarification before reuse.** No assertion of independent peer review or blanket open licensing is implied by repository access.

Constructive scientific criticism, reproducibility questions, and evidence-based corrections are welcome through repository issues. The purpose of independent dissemination is to make claims inspectable and contestable—not to replace external evaluation.

Research support: [GitHub Sponsors — paulohl](https://github.com/sponsors/paulohl)  
Publisher: [Zinnia Labs](https://zinnialabs.science)
