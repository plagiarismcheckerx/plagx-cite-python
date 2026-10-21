# Changelog

## 0.2.1: 2026-10-21

First Python release, matching Plagx Cite 0.2.1 for JavaScript.

- APA 7 and MLA 9 reference formatting for journal articles, books, chapters, conference papers, reports, theses and web pages
- In-text citations (parenthetical and narrative)
- Plain text, HTML and Markdown output
- BibTeX export and BibTeX/BibLaTeX import
- DOI normalising, extraction from text, and lookup through Crossref with a doi.org fallback for DataCite DOIs (arXiv, Zenodo)
- Duplicate reference detection by DOI or title + first author
- check_references(): duplicates, invalid DOIs, DOIs not found and missing titles, authors or years
- plagx-cite command line: format, check, doi and bibtex
