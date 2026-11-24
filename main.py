"""One-line worst AI advice entry for make.fun.

Writes the single advice line to entry.txt in the output directory
($MAKEFUN_OUTPUT_DIR, default /output). Stdlib only, deterministic, no
network, no clock, no randomness.

Gate (from the competition rules): /output/entry.txt must be UTF-8 text
of 1 to 140 characters, not only white space. The entry is written with
no trailing newline so the file holds exactly the judged line.

The advice is judged on funniness, AI voice, tightness and concreteness,
behind that hard gate: one line, one sentence, 1-140 characters. This
program enforces the gate strictly so an invalid line can never ship:
length, single line, single sentence (exactly one terminal period, at
the end), no leading/trailing whitespace, no double spaces, no '!'/'?'.

Structure: each gate rule is one small check function registered in
CHECKS; ``validate`` runs them and collects failures. Writing and
reading go through ``write_entry`` / ``read_entry``, and every write is
followed by ``verify_file_matches`` so a truncated or re-encoded file
is caught immediately instead of shipping silently.

Usage:
    python3 main.py --self-test   # validate + byte-identical round-trip
    python3 main.py --check       # validate ENTRY only, write nothing
    python3 main.py               # validate and write entry.txt
    python3 main.py --out DIR     # write entry.txt under DIR instead
"""

import argparse
import os
import sys

ENTRY = (
    "Delete the database to fix the bug \u2014 with no data left, the error "
    "messages will have nothing left to complain about."
)

MAX_CHARS = 140
ENTRY_FILENAME = "entry.txt"
DEFAULT_OUT_DIR = "/output"


def count_sentences(text: str) -> int:
    """Count sentences by terminal periods.

    A period counts as a sentence terminator when it ends the text or is
    followed by a space (so abbreviations such as "e.g." do not inflate
    the count, while "One. Two." counts as two).
    """
    return sum(
        1
        for i, ch in enumerate(text)
        if ch == "." and (i + 1 == len(text) or text[i + 1] == " ")
    )


def _check_length(text: str) -> str | None:
    if not 1 <= len(text) <= MAX_CHARS:
        return f"length {len(text)} chars, must be 1-{MAX_CHARS}"
    return None


def _check_not_blank(text: str) -> str | None:
    if not text.strip():
        return "entry is only white space"
    return None


def _check_no_edge_whitespace(text: str) -> str | None:
    if text != text.strip():
        return "entry has leading or trailing whitespace"
    return None


def _check_no_double_spaces(text: str) -> str | None:
    if "  " in text:
        return "entry contains double spaces"
    return None


def _check_single_line(text: str) -> str | None:
    if "\n" in text or "\r" in text:
        return "entry must be a single line"
    return None


def _check_single_sentence(text: str) -> str | None:
    if count_sentences(text) != 1 or not text.endswith("."):
        return ("entry must be exactly one sentence "
                "(one period, at the end)")
    return None


def _check_no_other_terminators(text: str) -> str | None:
    if "!" in text or "?" in text:
        return "entry must not contain '!' or '?' (one sentence only)"
    return None


def _check_utf8(text: str) -> str | None:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        return f"not encodable as UTF-8: {exc}"
    return None


# Every gate rule, in the order its failure is reported. Each check
# returns None when the rule passes, or a human-readable problem.
CHECKS = (
    _check_length,
    _check_not_blank,
    _check_no_edge_whitespace,
    _check_no_double_spaces,
    _check_single_line,
    _check_single_sentence,
    _check_no_other_terminators,
    _check_utf8,
)


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid)."""
    return [msg for check in CHECKS if (msg := check(text)) is not None]


def resolve_out_dir(cli_out: str | None) -> str:
    """Pick the output directory: --out wins, then $MAKEFUN_OUTPUT_DIR.

    An explicitly empty --out value is rejected rather than silently
    falling back, so a typo cannot redirect the entry elsewhere.
    """
    if cli_out is not None:
        if not cli_out.strip():
            raise ValueError("--out must not be empty")
        return cli_out
    return os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUT_DIR)


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path.

    The file is opened with newline="" so no platform line-ending
    translation can sneak a newline into the judged bytes.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, ENTRY_FILENAME)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(ENTRY)
    return path


def read_entry(path: str) -> str:
    """Read back an entry file as text, preserving its exact bytes."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def verify_file_matches(path: str) -> bool:
    """True when the file at `path` holds exactly ENTRY, byte for byte."""
    with open(path, "rb") as f:
        raw = f.read()
    return raw == ENTRY.encode("utf-8") and raw.decode("utf-8") == ENTRY


def self_test() -> int:
    """Validate ENTRY, write it to a temp dir, read it back, compare bytes."""
    import tempfile

    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        path = write_entry(tmp)
        if not verify_file_matches(path):
            print("self-test FAIL: read-back bytes differ from ENTRY",
                  file=sys.stderr)
            return 1
        if read_entry(path) != ENTRY:
            print("self-test FAIL: read-back text differs from ENTRY",
                  file=sys.stderr)
            return 1
    print(f"self-test OK: {len(ENTRY)} chars, single line, single sentence, "
          f"byte-identical round-trip")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output directory (default: "
                             "$MAKEFUN_OUTPUT_DIR or /output)")
    parser.add_argument("--self-test", action="store_true",
                        help="validate ENTRY and check a byte-identical "
                             "write/read round-trip, then exit")
    parser.add_argument("--check", action="store_true",
                        help="validate ENTRY only, write nothing, then exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    problems = validate(ENTRY)
    if problems:
        print("invalid ENTRY: " + "; ".join(problems), file=sys.stderr)
        return 1

    if args.check:
        print(f"check OK: {len(ENTRY)} chars, single sentence, valid")
        return 0

    try:
        out_dir = resolve_out_dir(args.out)
    except ValueError as exc:
        print(f"invalid output directory: {exc}", file=sys.stderr)
        return 1
    path = write_entry(out_dir)
    # Read back and confirm the file holds exactly the entry.
    if not verify_file_matches(path):
        print(f"read-back mismatch in {path}", file=sys.stderr)
        return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
