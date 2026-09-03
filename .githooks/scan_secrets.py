#!/usr/bin/env python3
"""Pre-commit guard: reject staged content containing payment identifiers."""
import re
import subprocess
import sys

CARD = re.compile(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)')
BSB = re.compile(r'(?<!\d)\d{3}-\d{3}(?!\d)')


def luhn(number: str) -> bool:
    digits = [int(c) for c in number][::-1]
    total = 0
    for i, d in enumerate(digits):
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def staged_files():
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True,
    ).stdout
    return [f for f in out.splitlines() if f]


def main() -> int:
    findings = []
    for path in staged_files():
        if path.startswith(".githooks/") or path.endswith((".lock", ".png", ".jpg", ".pyc")):
            continue
        blob = subprocess.run(
            ["git", "show", f":{path}"], capture_output=True
        ).stdout
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in CARD.findall(line):
                bare = re.sub(r"[ -]", "", match)
                if 13 <= len(bare) <= 19 and luhn(bare):
                    findings.append(
                        f"  {path}:{lineno}  Luhn-valid card number {bare[:4]}...{bare[-4:]}"
                    )
            if BSB.search(line) and re.search(r"account", line, re.I):
                findings.append(f"  {path}:{lineno}  possible BSB + account number")

    if findings:
        sys.stderr.write("\nCOMMIT BLOCKED - payment identifiers detected:\n\n")
        sys.stderr.write("\n".join(findings[:20]) + "\n")
        if len(findings) > 20:
            sys.stderr.write(f"  ... and {len(findings) - 20} more\n")
        sys.stderr.write(
            "\nThese must never enter git history. Move the file outside the repo,\n"
            "or confirm .gitignore covers it. Override (rarely correct): --no-verify\n\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
