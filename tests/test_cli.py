"""Command line tests (same behaviour as `npx plagx-cite`)."""
import io
import json

import pytest

from plagx_cite.cli import main

BIB = """
@article{smith2020, author={Smith, John and Lee, Kate}, title={Deep learning for text similarity},
  journal={Journal of Academic Writing}, year=2020, volume=12, number=3, pages={45--67}}
@book{brown2018, author={Brown, Mary}, title={Writing research papers}, publisher={Academic Press}, year=2018}
@article{smithdup, author={Smith, J.}, title={Deep Learning for Text Similarity!}, journal={JAW}, year=2020}
@misc{bad, title={Untitled web page}, doi={not-a-doi}}
"""


@pytest.fixture
def files(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(BIB, encoding="utf-8")
    clean = tmp_path / "clean.json"
    clean.write_text(json.dumps([{"type": "book", "title": "T", "author": [{"family": "A", "given": "B"}], "year": 2001}]))
    return {"bib": str(bib), "clean": str(clean), "dir": tmp_path}


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(args), out, err)
    return code, out.getvalue(), err.getvalue()


def test_format(files):
    assert run("format", files["clean"]) == (0, "A, B. (2001). T.\n", "")
    code, out, _ = run("format", files["bib"], "--style", "mla")
    assert out.split("\n")[0].startswith("Brown, Mary. Writing research papers.")


def test_check(files):
    code, out, _ = run("check", files["bib"])
    assert code == 1
    assert "4 reference(s), 2 error(s), 2 warning(s)" in out
    assert "error   smithdup: Possible duplicate (title match)" in out
    assert 'error   bad: Invalid DOI "not-a-doi"' in out
    assert run("check", files["clean"])[0] == 0


def test_check_json_and_strict(files):
    [report] = json.loads(run("check", files["bib"], "--json")[1])
    assert [x["code"] for x in report["issues"]] == ["duplicate", "invalid-doi", "missing-author", "missing-year"]
    warn = files["dir"] / "warn.json"
    warn.write_text(json.dumps([{"title": "No author here", "year": 2020}]))
    assert run("check", str(warn))[0] == 0
    assert run("check", str(warn), "--strict")[0] == 1


def test_bibtex(files):
    code, out, _ = run("bibtex", files["clean"])
    assert code == 0 and out.startswith("@book{a2001,")


def test_usage_errors(files):
    assert run()[0] == 2
    assert run("format")[0] == 2
    assert run("format", str(files["dir"] / "missing.bib"))[0] == 2
    assert run("format", files["clean"], "--style", "chicago")[0] == 2
    assert run("nope")[0] == 2
    code, out, _ = run("--version")
    assert code == 0 and out.strip().count(".") == 2
