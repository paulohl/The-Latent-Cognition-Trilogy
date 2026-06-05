# Build Notes

Compiler:
- pdfLaTeX (TeX Live 2025)

Build sequence:

pdflatex main
bibtex master
pdflatex main
pdflatex main

Notes:
- Pandoc compatibility layer retained intentionally.
- main.tex should not be structurally modified.
- New content belongs under /sections only.
