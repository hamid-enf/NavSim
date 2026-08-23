#!/usr/bin/env python3
"""Parse every project .m file with the Tree-sitter MATLAB grammar."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__"}


def matlab_files() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*.m"))
        if not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
    ]


def syntax_errors(node):
    """Yield the smallest explicit ERROR and missing-token nodes."""
    if node.type == "ERROR" or node.is_missing:
        yield node
        return
    for child in node.children:
        yield from syntax_errors(child)


def main() -> int:
    try:
        import tree_sitter_matlab
        from tree_sitter import Language, Parser
    except ImportError as exc:
        print(
            "Tree-sitter MATLAB parser is not installed. Run "
            "`python -m pip install -r requirements-dev.txt`.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    language = Language(tree_sitter_matlab.language())
    parser = Parser(language)
    files = matlab_files()
    problems: list[str] = []

    for path in files:
        source = path.read_bytes()
        tree = parser.parse(source)
        if not tree.root_node.has_error:
            continue
        lines = source.decode("utf-8", errors="replace").splitlines()
        for node in syntax_errors(tree.root_node):
            row, column = node.start_point
            excerpt = lines[row].strip() if row < len(lines) else ""
            kind = "missing token" if node.is_missing else "syntax error"
            rel = path.relative_to(ROOT)
            problems.append(f"{rel}:{row + 1}:{column + 1}: {kind}: {excerpt}")

    if problems:
        print("MATLAB syntax problems:")
        for problem in problems:
            print(f"  {problem}")
        return 1

    print(f"Tree-sitter parsed all {len(files)} .m files without syntax errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
