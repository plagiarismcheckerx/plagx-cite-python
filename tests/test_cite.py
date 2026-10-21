"""Same cases and expected output as the JavaScript package (plagx-cite on npm)."""
import json
import re

import pytest

from plagx_cite import (
    check_references, cite_in_text, extract_dois, find_duplicates, format_bibliography, format_reference,
    from_crossref, lookup_doi, normalize_doi, parse_bibtex, to_bibtex,
)

ARTICLE = {
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

BOOK = {
    "type": "book",
    "title": "Writing research papers",
    "author": [{"family": "Brown", "given": "Mary"}],
    "issued": {"date-parts": [[2018]]},
    "publisher": "Academic Press",
    "edition": "2",
}

CHAPTER = {
    "type": "chapter",
    "title": "Citing sources well",
    "author": [{"family": "Khan", "given": "Ali"}, {"family": "Ng", "given": "Wei"}, {"family": "Ruiz", "given": "Ana"}],
    "editor": [{"family": "Green", "given": "Paul"}, {"family": "White", "given": "Sara Jane"}],
    "container-title": "Handbook of scholarly writing",
    "page": "101-120",
    "publisher": "Routledge",
    "issued": {"date-parts": [[2019]]},
}

WEBPAGE = {
    "type": "webpage",
    "title": "How to avoid plagiarism",
    "author": [{"literal": "Writing Centre"}],
    "container-title": "University Library",
    "issued": {"date-parts": [[2023, 3, 15]]},
    "URL": "https://example.com/post",
}


def test_apa_reference_list_entries():
    assert format_reference(ARTICLE) == (
        "Smith, J. A., & Lee, K. (2020). Deep learning for text similarity. Journal of Academic Writing, "
        "12(3), 45–67. https://doi.org/10.1234/jaw.2020.045"
    )
    assert format_reference(BOOK) == "Brown, M. (2018). Writing research papers (2nd ed.). Academic Press."
    assert format_reference(CHAPTER) == (
        "Khan, A., Ng, W., & Ruiz, A. (2019). Citing sources well. In P. Green & S. J. White (Eds.), "
        "Handbook of scholarly writing (pp. 101–120). Routledge."
    )
    assert format_reference(WEBPAGE) == (
        "Writing Centre. (2023, March 15). How to avoid plagiarism. University Library. https://example.com/post"
    )


def test_apa_without_author_or_date():
    ref = {"type": "webpage", "title": "Citation basics", "URL": "https://example.com"}
    assert format_reference(ref) == "Citation basics. (n.d.). https://example.com"


def test_apa_many_authors_use_ellipsis():
    author = [{"family": f"A{i + 1}", "given": "B"} for i in range(22)]
    out = format_reference({"type": "article-journal", "title": "T", "author": author, "issued": {"date-parts": [[2021]]}})
    assert re.match(r"^A1, B\., .*A19, B\., \. \. \. A22, B\. \(2021\)", out)
    assert "A20" not in out


def test_mla_works_cited_entries():
    assert format_reference(ARTICLE, style="mla") == (
        "Smith, John Allen, and Kate Lee. “Deep learning for text similarity.” Journal of Academic Writing, "
        "vol. 12, no. 3, 2020, pp. 45-67, https://doi.org/10.1234/jaw.2020.045."
    )
    assert format_reference(BOOK, style="mla") == "Brown, Mary. Writing research papers. 2nd ed., Academic Press, 2018."
    assert format_reference(CHAPTER, style="mla") == (
        "Khan, Ali, et al. “Citing sources well.” Handbook of scholarly writing, edited by Paul Green and "
        "Sara Jane White, Routledge, 2019, pp. 101-120."
    )
    assert format_reference(WEBPAGE, style="mla") == (
        "Writing Centre. “How to avoid plagiarism.” University Library, 15 Mar. 2023, https://example.com/post."
    )


def test_html_and_markdown_output():
    assert format_reference(BOOK, format="html") == "Brown, M. (2018). <i>Writing research papers</i> (2nd ed.). Academic Press."
    assert format_reference(BOOK, format="markdown") == "Brown, M. (2018). *Writing research papers* (2nd ed.). Academic Press."
    assert "<i>Tom &amp; &lt;Jerry&gt;</i>" in format_reference({**BOOK, "title": "Tom & <Jerry>"}, format="html")


def test_in_text_citations():
    assert cite_in_text(ARTICLE, page="50") == "(Smith & Lee, 2020, p. 50)"
    assert cite_in_text(ARTICLE, narrative=True) == "Smith and Lee (2020)"
    assert cite_in_text(CHAPTER, page="101-103") == "(Khan et al., 2019, pp. 101–103)"
    assert cite_in_text(ARTICLE, style="mla", page="50") == "(Smith and Lee 50)"
    assert cite_in_text(CHAPTER, style="mla") == "(Khan et al.)"
    assert cite_in_text({"title": "Citation guide", "year": 2021}) == "(“Citation guide,” 2021)"
    assert cite_in_text({"title": "Citation guide"}, narrative=True) == "“Citation guide” (n.d.)"


def test_bibliography_is_sorted():
    out = format_bibliography([ARTICLE, CHAPTER, BOOK])
    assert [s.split(",")[0] for s in out] == ["Brown", "Khan", "Smith"]


def test_unknown_style_or_format():
    with pytest.raises(ValueError, match="Unknown citation style"):
        format_reference(BOOK, style="xyz")
    with pytest.raises(ValueError, match="Unknown output format"):
        format_reference(BOOK, format="pdf")


def test_invalid_doi_is_not_a_link_and_full_url_not_doubled():
    base = {"type": "book", "title": "T", "author": [{"family": "A", "given": "B"}], "year": 2001}
    assert format_reference({**base, "DOI": "not-a-doi"}) == "A, B. (2001). T."
    assert format_reference({**base, "DOI": "https://doi.org/10.1234/x"}) == "A, B. (2001). T. https://doi.org/10.1234/x"


def test_bibtex_export():
    assert to_bibtex(ARTICLE) == "\n".join([
        "@article{smith2020deep,",
        "  author = {Smith, John Allen and Lee, Kate},",
        "  title = {Deep learning for text similarity},",
        "  journal = {Journal of Academic Writing},",
        "  year = {2020},",
        "  volume = {12},",
        "  number = {3},",
        "  pages = {45--67},",
        "  doi = {10.1234/jaw.2020.045}",
        "}",
    ])
    assert "title = {50\\% of R\\&D}" in to_bibtex({**BOOK, "title": "50% of R&D"})
    assert re.findall(r"@book\{(\w+),", to_bibtex([BOOK, BOOK])) == ["brown2018writing", "brown2018writinga"]


def test_bibtex_round_trip():
    parsed = parse_bibtex(to_bibtex([ARTICLE, BOOK, CHAPTER]))
    for ref, original in zip(parsed, [ARTICLE, BOOK, CHAPTER]):
        ref = {k: v for k, v in ref.items() if k != "id"}
        assert ref == original


def test_bibtex_import_latex_macros_and_organisations():
    [ref] = parse_bibtex(r"""
        @comment{ignored}
        @string{jaw = "Journal of Academic Writing"}
        @Article{muller21,
          author  = {M{\"u}ller, J{\"o}rg and {World Health Organization}},
          title   = "{T}he {\&} problem",
          journal = jaw,
          year    = 2021, month = mar,
          pages   = "1--9",
          doi     = {https://doi.org/10.5555/abc}
        }""")
    assert ref["author"] == [{"family": "Müller", "given": "Jörg"}, {"literal": "World Health Organization"}]
    assert ref["title"] == "The & problem"
    assert ref["container-title"] == "Journal of Academic Writing"
    assert ref["issued"] == {"date-parts": [[2021, 3]]}
    assert ref["page"] == "1-9"
    assert ref["DOI"] == "10.5555/abc"


def test_doi_normalising_and_extraction():
    assert normalize_doi("https://doi.org/10.1234/ABC.5") == "10.1234/ABC.5"
    assert normalize_doi("doi: 10.1234/abc") == "10.1234/abc"
    assert normalize_doi("not a doi") is None
    text = "See (doi:10.1000/xyz123). Also https://doi.org/10.1000/xyz123 and 10.5555/a(b)c."
    assert extract_dois(text) == ["10.1000/xyz123", "10.5555/a(b)c"]


def test_doi_lookup_maps_crossref():
    def http(url, headers):
        assert url == "https://api.crossref.org/works/10.1234%2Fjaw.2020.045?mailto=a%40b.org"
        return 200, json.dumps({"message": {
            "type": "journal-article",
            "title": ["Deep learning for text similarity"],
            "author": [{"given": "John Allen", "family": "Smith"}, {"given": "Kate", "family": "Lee"}],
            "container-title": ["Journal of Academic Writing"],
            "issued": {"date-parts": [[2020]]},
            "volume": "12", "issue": "3", "page": "45-67",
            "DOI": "10.1234/jaw.2020.045",
            "URL": "https://doi.org/10.1234/jaw.2020.045",
            "publisher": "Example Publisher",
        }})

    ref = lookup_doi("doi:10.1234/jaw.2020.045", mailto="a@b.org", http=http)
    assert format_reference(ref) == format_reference(ARTICLE)

    def not_found(url, headers):
        return 404, ""

    with pytest.raises(LookupError, match="DOI not found"):
        lookup_doi("10.1234/none", http=not_found)
    with pytest.raises(ValueError, match="Not a valid DOI"):
        lookup_doi("nope", http=not_found)


def test_doi_lookup_falls_back_to_doi_org():
    calls = []

    def http(url, headers):
        calls.append((url, headers["Accept"]))
        if url.startswith("https://api.crossref.org/"):
            return 404, ""
        return 200, json.dumps({
            "type": "article",
            "title": "Attention is all you need",
            "author": [{"family": "Vaswani", "given": "Ashish"}, {"family": "Shazeer", "given": "Noam"}],
            "issued": {"date-parts": [[2017]]},
            "publisher": "arXiv",
            "DOI": "10.48550/ARXIV.1706.03762",
            "abstract": "ignored",
        })

    ref = lookup_doi("10.48550/arXiv.1706.03762", http=http)
    assert calls[1] == ("https://doi.org/10.48550/arXiv.1706.03762", "application/vnd.citationstyles.csl+json")
    assert "abstract" not in ref
    assert format_reference(ref) == (
        "Vaswani, A., & Shazeer, N. (2017). Attention is all you need. arXiv. https://doi.org/10.48550/ARXIV.1706.03762"
    )
    assert format_reference(ref, style="mla") == (
        "Vaswani, Ashish, and Noam Shazeer. “Attention is all you need.” arXiv, 2017, https://doi.org/10.48550/ARXIV.1706.03762."
    )


def test_crossref_markup_subtitle_and_book_title():
    ref = from_crossref({
        "type": "book-chapter",
        "title": ["Optuna"],
        "subtitle": ["A next-generation <i>hyperparameter</i> framework"],
        "container-title": ["Lecture Notes in Computer Science", "Knowledge Discovery &amp; Data Mining"],
        "author": [{"family": "Akiba", "given": "Takuya"}],
        "publisher": "ACM",
        "DOI": "10.1145/1",
    })
    assert ref["title"] == "Optuna: A next-generation hyperparameter framework"
    assert ref["container-title"] == "Knowledge Discovery & Data Mining"
    assert from_crossref({"type": "journal-article", "container-title": ["Nature", "Nat."]})["container-title"] == "Nature"


def test_duplicate_detection():
    groups = find_duplicates([
        ARTICLE,
        BOOK,
        {**ARTICLE, "title": "A different title", "DOI": "https://doi.org/10.1234/JAW.2020.045"},
        {**BOOK, "title": "Writing Research Papers!"},
        {**BOOK, "author": [{"family": "Someone", "given": "Else"}]},
    ])
    assert groups == [{"indexes": [0, 2], "reasons": ["doi"]}, {"indexes": [1, 3], "reasons": ["title"]}]
    assert find_duplicates([ARTICLE, BOOK]) == []


def test_check_references():
    refs = parse_bibtex("""
        @article{smith2020, author={Smith, John and Lee, Kate}, title={Deep learning for text similarity},
          journal={Journal of Academic Writing}, year=2020, volume=12, number=3, pages={45--67}}
        @book{brown2018, author={Brown, Mary}, title={Writing research papers}, publisher={Academic Press}, year=2018}
        @article{smithdup, author={Smith, J.}, title={Deep Learning for Text Similarity!}, journal={JAW}, year=2020}
        @misc{bad, title={Untitled web page}, doi={not-a-doi}}
        """)
    result = check_references(refs)
    assert (result["references"], result["errors"], result["warnings"]) == (4, 2, 2)
    assert [x["code"] for x in result["issues"]] == ["duplicate", "invalid-doi", "missing-author", "missing-year"]
    assert result["issues"][0]["message"] == "Possible duplicate (title match) of smith2020: smith2020, smithdup"

    missing = check_references(
        [{"title": "X", "author": ["A B"], "year": 2000, "DOI": "10.1234/missing"}],
        check_dois=True, http=lambda url, headers: (404, ""),
    )
    assert [x["code"] for x in missing["issues"]] == ["doi-not-found"]
