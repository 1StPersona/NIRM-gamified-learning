# Статья (IEEE, LaTeX)

`main.tex` — текст статьи в шаблоне IEEEtran (conference), `references.bib` — источники BibTeX, `figures/` — векторные рисунки (строятся `python -m paper.figures` из `bench/results/preliminary_stats.json`).

Локальная сборка: `pdflatex main && bibtex main && pdflatex main && pdflatex main`.
Overleaf: New Project → Upload Project → архив `paper_overleaf.zip` (или содержимое этой папки без `figures.py`).
