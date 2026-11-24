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

Usage:
    python3 main.py --self-test   # validate + byte-identical round-trip
    python3 main.py --check       # validate ENTRY only, write nothing
    python3 main.py               # validate and write entry.txt
"""

import argparse
import os
import sys

ENTRY = (
    "Delete the database to fix the bug \u2014 with no data left, the error "
    "messages will have nothing left to complain about."
)

MAX_CHARS = 140


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


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid)."""
    problems = []
    if not 1 <= len(text) <= MAX_CHARS:
        problems.append(f"length {len(text)} chars, must be 1-{MAX_CHARS}")
    if not text.strip():
        problems.append("entry is only white space")
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if "  " in text:
        problems.append("entry contains double spaces")
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    if count_sentences(text) != 1 or not text.endswith("."):
        problems.append("entry must be exactly one sentence "
                        "(one period, at the end)")
    if "!" in text or "?" in text:
        problems.append("entry must not contain '!' or '?' "
                        "(one sentence only)")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        problems.append(f"not encodable as UTF-8: {exc}")
    return problems


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(ENTRY)
    return path


def self_test() -> int:
    """Validate ENTRY, write it to a temp dir, read it back, compare bytes."""
    import tempfile

    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        path = write_entry(tmp)
        with open(path, "rb") as f:
            raw = f.read()
        if raw != ENTRY.encode("utf-8"):
            print("self-test FAIL: read-back bytes differ from ENTRY",
                  file=sys.stderr)
            return 1
        if raw.decode("utf-8") != ENTRY:
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

    out_dir = args.out or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = write_entry(out_dir)
    # Read back and confirm the file holds exactly the entry.
    with open(path, encoding="utf-8") as f:
        if f.read() != ENTRY:
            print(f"read-back mismatch in {path}", file=sys.stderr)
            return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
