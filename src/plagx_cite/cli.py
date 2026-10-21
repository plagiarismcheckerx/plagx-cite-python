"""Plagx Cite command line. A free academic writing utility by Plagiarism Checker X."""
from __future__ import annotations

import json
import sys
from typing import List, Optional, TextIO

from . import __version__, check_references, format_bibliography, format_reference, lookup_doi, parse_bibtex
from . import sort_references, styles, to_bibtex

HELP = f"""Plagx Cite {__version__}: format and check references (APA 7 / MLA 9, BibTeX, DOI)

Usage:
  plagx-cite format <file>      Print a formatted reference list
  plagx-cite check <file>       Check for duplicates, invalid DOIs and missing fields
  plagx-cite doi <doi> [...]    Look up DOIs and print formatted references
  plagx-cite bibtex <file>      Convert a reference file to BibTeX

<file> is a .bib (BibTeX) or .json (CSL-JSON) file. Use - to read from stdin.

Options:
  --style apa|mla               Citation style (default: apa)
  --format text|html|markdown   Output format (default: text)
  --check-dois                  check: look up every DOI online
  --strict                      check: treat warnings as errors
  --json                        check: print the result as JSON
  --mailto <email>              Email for the Crossref polite pool (optional)
  -v, --version                 Show version
  -h, --help                    Show this help

Exit codes: 0 = OK, 1 = problems found (check), 2 = usage or input error.

A free academic writing utility by Plagiarism Checker X. It does not check for
plagiarism or AI-generated text: https://plagiarismcheckerx.com/"""


class UsageError(Exception):
    pass


def _parse_args(argv: List[str]):
    opts = {"style": "apa", "format": "text", "check_dois": False, "strict": False, "json": False,
            "mailto": None, "help": False, "version": False}
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]

        def value() -> str:
            if i + 1 >= len(argv):
                raise UsageError(f"{a} needs a value")
            return argv[i + 1]

        if a in ("--style", "--format", "--mailto"):
            opts[a[2:]] = value()
            i += 1
        elif a.startswith("--style="):
            opts["style"] = a[8:]
        elif a.startswith("--format="):
            opts["format"] = a[9:]
        elif a == "--check-dois":
            opts["check_dois"] = True
        elif a == "--strict":
            opts["strict"] = True
        elif a == "--json":
            opts["json"] = True
        elif a in ("-h", "--help"):
            opts["help"] = True
        elif a in ("-v", "--version"):
            opts["version"] = True
        elif a.startswith("-") and a != "-":
            raise UsageError(f"Unknown option {a}")
        else:
            args.append(a)
        i += 1
    if opts["style"] not in styles:
        raise UsageError(f'Unknown style "{opts["style"]}". Use: {", ".join(styles)}')
    return opts, args


def load_references(path: str) -> list:
    try:
        text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    except FileNotFoundError:
        raise UsageError(f"Cannot read {path}: file not found") from None
    except OSError as e:
        raise UsageError(f"Cannot read {path}: {e}") from None
    looks_json = path.lower().endswith(".json") or (path == "-" and text.lstrip()[:1] in ("[", "{"))
    if looks_json:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise UsageError(f"{path} is not valid JSON: {e}") from None
        refs = data if isinstance(data, list) else (data.get("items") or data.get("references"))
        if not isinstance(refs, list):
            raise UsageError(f"{path} must contain a CSL-JSON array of references")
        return refs
    return parse_bibtex(text)


def _print_check(file: str, result: dict) -> str:
    lines = [f"{file}: {result['references']} reference(s), {result['errors']} error(s), {result['warnings']} warning(s)"]
    lines += [f"  {x['level']:<7} {x['ref']}: {x['message']}" for x in result["issues"]]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None, out: TextIO = None, err: TextIO = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = out or sys.stdout
    err = err or sys.stderr
    try:
        opts, args = _parse_args(argv)
    except UsageError as e:
        err.write(f"{e}\n\nRun plagx-cite --help for usage.\n")
        return 2
    if opts["version"]:
        out.write(f"{__version__}\n")
        return 0
    if opts["help"] or not args:
        out.write(HELP + "\n")
        return 0 if opts["help"] or args else 2

    command, rest = args[0], args[1:]
    try:
        if command in ("format", "bibtex", "check"):
            if not rest:
                raise UsageError(f"{command} needs a file (.bib or .json, or - for stdin)")
            failed = False
            reports = []
            for file in rest:
                refs = load_references(file)
                if command == "format":
                    out.write("\n".join(format_bibliography(refs, style=opts["style"], format=opts["format"])) + "\n")
                elif command == "bibtex":
                    out.write(to_bibtex(sort_references(refs)) + "\n")
                else:
                    result = check_references(refs, check_dois=opts["check_dois"], mailto=opts["mailto"])
                    if result["errors"] or (opts["strict"] and result["warnings"]):
                        failed = True
                    reports.append({"file": file, **result})
            if command == "check":
                if opts["json"]:
                    out.write(json.dumps(reports, indent=2, ensure_ascii=False) + "\n")
                else:
                    out.write("\n\n".join(_print_check(r["file"], r) for r in reports) + "\n")
                return 1 if failed else 0
            return 0

        if command == "doi":
            if not rest:
                raise UsageError("doi needs at least one DOI")
            failed = False
            for doi in rest:
                try:
                    ref = lookup_doi(doi, mailto=opts["mailto"])
                    out.write(format_reference(ref, style=opts["style"], format=opts["format"]) + "\n")
                except (ValueError, LookupError) as e:
                    err.write(f"{e}\n")
                    failed = True
            return 1 if failed else 0

        raise UsageError(f'Unknown command "{command}"')
    except UsageError as e:
        err.write(f"{e}\n\nRun plagx-cite --help for usage.\n")
        return 2
    except ValueError as e:  # e.g. unknown --format
        err.write(f"{e}\n\nRun plagx-cite --help for usage.\n")
        return 2


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
