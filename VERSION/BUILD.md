# Build and Edition Integrity

**Project:** The Latent Cognition Trilogy  
**Source language:** LaTeX + BibTeX  
**Authoring:** Overleaf / GitHub  
**Current print target:** 6 × 9-inch hardcover, no-bleed PDF

## Build configuration

The project has been maintained with **pdfLaTeX** (the existing notes specify TeX Live 2025). The repository entry point is `main.tex`; the bibliography database is `master.bib`.

For a local environment with TeX Live and `latexmk`:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Alternatively, use the explicit BibTeX sequence:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

**Important:** `bibtex main` operates on `main.aux`. `master.bib` is the reference database—not the BibTeX job name. Run from the project root. These commands document the expected build procedure; this documentation refresh does not certify that the checked-in source reproduces the KDP-submitted PDF.

## Production targets

| Target | Intended process | State as of 2026-11-07 |
| :-- | :-- | :-- |
| Hardcover PDF | Overleaf/pdfLaTeX → KDP preview → physical proof | Submitted to KDP; physical proof ordered |
| Kindle EPUB | Separate LaTeX-derived EPUB build → KDP online preview | Planned; not released |

### Hardcover validation record

The submitted hardcover has ISBN **979-8-234-29378-7** and was priced at **USD 35.99** at submission. The KDP Print Previewer reported no blocking errors after repairs to oversized figures and exclusion of a source-verification manifest; the remaining non-printable-markup notices were review-only. A downloaded PDF proof and a physical proof order exist. **KDP review approval and physical print quality were pending on 2026-11-07.**

## Source-to-edition parity: outstanding

The GitHub `main.tex` inspected on 2026-11-07 still contains the line:

```tex
\include{sections/backmatter/10_hyp1_manifest}
```

That manifest was excluded from the final hardcover build. Some hardcover-specific front matter also differs from the GitHub working tree. Consequently:

1. Preserve the submitted KDP PDF and proof as a separately identified production artifact.
2. Synchronize the final Overleaf source into a controlled release branch, **without replacing or silently rewriting historical research records**.
3. Recompile from the synchronized source and compare page count, identifiers, figure placement, and front/back matter with the submitted proof.
4. Record a source commit, exact compiler configuration, and SHA-256 of the approved production PDF in a release manifest after parity is verified.
5. Tag the release only when source-to-PDF parity and publication state are verified; avoid implying KDP approval before it occurs.

Do not silently treat the June 2026 `main.tex` architecture freeze as proof of final November hardcover reproducibility.

## Source-change policy

`main.tex` is the build orchestrator. Its June 2026 architectural freeze is a version-control milestone, **not** a prohibition on essential publication corrections. Keep new scientific prose in imported `sections/` files; review any necessary orchestrator changes as explicit release-engineering changes. Retain legacy/Pandoc compatibility only where required by the current build.

The hardcover and future eBook should draw from the same reviewed scientific content but use **separate formatting/build targets**. PDF margins, forced page breaks, running headers, and non-reflowable table dimensions must not be blindly copied into EPUB.
