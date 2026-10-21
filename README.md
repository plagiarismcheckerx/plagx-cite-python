# Plagx Cite for Python

*A free academic writing tool by Plagiarism Checker X.*

**Plagx Cite for Python is a free, open-source citation generator and reference checker for Python, Jupyter and the command line.** It turns sources into correct APA 7 and MLA 9 references and in-text citations, so researchers and students can build a clean reference list in seconds. It also checks BibTeX files for duplicate references, broken DOIs and missing details before you submit.

Use it as an **APA citation generator** or **MLA citation generator**: create a **reference list, bibliography or works cited** page, generate **in-text citations**, turn a **DOI into a citation**, import and export **BibTeX**, and find **duplicate references**.

- No dependencies, Python 3.9+
- Works in scripts, Jupyter notebooks, Django and Flask apps, and from the command line
- Uses [CSL-JSON](https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html), the reference format used by Zotero, Mendeley and Crossref
- Plain text, HTML or Markdown output
- Same output as the JavaScript version, [plagx-cite on npm](https://www.npmjs.com/package/plagx-cite)

**[Try the live demo →](https://plagiarismcheckerx.github.io/plagx-cite/)**

Need a quick citation online? Use the [free citation generator](https://plagiarismcheckerx.com/citation-generator?utm_source=plagx-cite-python&utm_medium=readme&utm_campaign=plagx&utm_content=citation-generator).

> Plagx Cite is a free academic writing utility by Plagiarism Checker X. It is a citation generator that builds and checks APA and MLA reference lists. Plagiarism checking and AI-generated text detection are available in Plagiarism Checker X, linked at the end of this page.

## Install

```bash
pip install plagx-cite
```

## Command line

```bash
plagx-cite format references.bib --style apa
plagx-cite check references.bib --check-dois
plagx-cite doi 10.1038/nature14539 --style mla
plagx-cite bibtex references.json > references.bib
```

| Command | What it does |
|---|---|
| `format <file>` | Prints the formatted reference list (`--style apa\|mla`, `--format text\|html\|markdown`) |
| `check <file>` | Reports duplicates, invalid DOIs and missing fields (`--check-dois`, `--strict`, `--json`) |
| `doi <doi> [...]` | Looks up DOIs and prints formatted references |
| `bibtex <file>` | Converts a CSL-JSON or BibTeX file to BibTeX |

`<file>` is a `.bib` or CSL-JSON `.json` file, or `-` for stdin. Exit codes: `0` OK, `1` problems found, `2` usage or input error. `python -m plagx_cite …` works too.

## Quick start

```python
from plagx_cite import format_reference, cite_in_text

ref = {
    "type": "article-journal",
    "title": "Deep learning for text similarity",
    "author": [{"family": "Smith", "given": "John Allen"}, {"family": "Lee", "given": "Kate"}],
    "issued": {"date-parts": [[2020]]},
    "container-title": "Journal of Academic Writing",
    "volume": "12",
    "issue": "3",
    "page": "45-67",
    "DOI": "10.1234/jaw.2020.045",
}

format_reference(ref)
# Smith, J. A., & Lee, K. (2020). Deep learning for text similarity. Journal of Academic Writing, 12(3), 45–67. https://doi.org/10.1234/jaw.2020.045

format_reference(ref, style="mla")
# Smith, John Allen, and Kate Lee. “Deep learning for text similarity.” Journal of Academic Writing, vol. 12, no. 3, 2020, pp. 45-67, https://doi.org/10.1234/jaw.2020.045.

cite_in_text(ref, page="50")               # (Smith & Lee, 2020, p. 50)
cite_in_text(ref, narrative=True)          # Smith and Lee (2020)
cite_in_text(ref, style="mla", page="50")  # (Smith and Lee 50)
```

References are plain dicts in CSL-JSON form, so a Zotero or Crossref export works with `json.load()`.

## API

### Formatting references and citations

| Function | Returns |
|---|---|
| `format_reference(ref, style="apa", format="text")` | One reference-list entry |
| `format_bibliography(refs, style="apa", format="text")` | Sorted list of entries |
| `cite_in_text(ref, style="apa", page=None, narrative=False)` | In-text citation |
| `sort_references(refs)` | New list sorted by author, year, title |
| `styles` | `["apa", "mla"]` |

- `style`: `"apa"` (default) or `"mla"`
- `format`: `"text"` (default), `"html"` (titles in `<i>`, text escaped) or `"markdown"` (titles in `*…*`)

Supported reference types: `article-journal`, `article-magazine`, `article-newspaper`, `book`, `chapter`, `paper-conference`, `report`, `thesis`, `webpage`. Other types fall back to a sensible general layout.

### BibTeX import and export

```python
from plagx_cite import parse_bibtex, to_bibtex

refs = parse_bibtex(open("library.bib", encoding="utf-8").read())
print(to_bibtex(refs))
```

`parse_bibtex` handles `@string` macros, `#` concatenation, common LaTeX accents (`{\"u}` → ü), organisation names in braces, and BibLaTeX `date` / `journaltitle` fields.

### DOI lookup

```python
from plagx_cite import lookup_doi, normalize_doi, extract_dois

ref = lookup_doi("10.1038/nature14539", mailto="you@example.com")

normalize_doi("https://doi.org/10.1038/NATURE14539")  # '10.1038/NATURE14539'
extract_dois(text)                                    # every DOI found in the text
```

`lookup_doi` calls the free public [Crossref API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/). If a DOI isn't registered with Crossref, such as arXiv or Zenodo DOIs from DataCite, it falls back to [doi.org content negotiation](https://citation.doi.org/). No API key is needed. It raises `ValueError` for an invalid DOI and `LookupError` when the DOI can't be found. To use your own HTTP client (for example `requests` or `httpx`), pass `http=lambda url, headers: (status, body)`.

### Duplicate references

```python
from plagx_cite import find_duplicates

find_duplicates(refs)
# [{'indexes': [0, 4], 'reasons': ['doi']}, {'indexes': [2, 7], 'reasons': ['title']}]
```

References count as duplicates when they share a DOI, or the same title and first author. Case, accents and punctuation are ignored.

### Checking a reference list

```python
from plagx_cite import check_references

result = check_references(refs, check_dois=True)
# {'references': 4, 'errors': 2, 'warnings': 1, 'issues': [{'level': 'error', 'code': 'duplicate', 'ref': 'smith2020b', ...}]}
```

Errors are duplicates, invalid DOIs and DOIs that can't be found (with `check_dois=True`). Warnings are missing titles, authors or years.

## Good to know

- Titles are used exactly as you give them. APA wants sentence case for article and book titles, and MLA wants title case. Plagx Cite does not change capitalisation automatically, because doing so would break names and acronyms.
- The output follows the main APA 7 and MLA 9 rules for common reference types. Always check the final list against your institution's or publisher's guidelines.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e . pytest   # on Windows: .venv\Scripts\pip
.venv/bin/pytest
```

<h2>Plagx Cite - Free Citation & Reference Toolkit</h2>

<p>
 An open-source citation utility for students, researchers and developers.
 Format references, organize citations and manage bibliographies.
 </p>

<p>
 Developed by Plagiarism Checker X.
 </p>

<p>
 Plagx Cite helps with source attribution; it does not detect plagiarism
 or AI-generated text. For full document checks, explore
 <a href="https://plagiarismcheckerx.com/?utm_source=plagx-cite-python&utm_medium=readme&utm_campaign=plagx&utm_content=about-cta">Plagiarism Checker X</a>
 and its
 <a href="https://plagiarismcheckerx.com/ai-content-detector?utm_source=plagx-cite-python&utm_medium=readme&utm_campaign=plagx&utm_content=about-ai-detector">AI Content Detector</a>.
 </p>

## License

MIT © Plagiarism Checker X
