#!/usr/bin/env python3
"""Rough static sanity checker for MATLAB files (not a full parser)."""
import os, re, sys

ROOT = "/home/user/NavSim/../NavSim"
OPENERS = re.compile(r'^\s*(classdef|function|if|for|while|switch|try|methods|properties|events|enumeration|parfor)\b')
ENDTOK  = re.compile(r'\bend\b')

def strip_line(line):
    # remove %% comments (naive but fine here: no % inside strings in our code except '...')
    in_str = False
    out = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "'":
            in_str = not in_str
            out.append(' ')
        elif not in_str and ch == '%':
            break
        elif in_str:
            out.append(' ')
        else:
            out.append(ch)
        i += 1
    return ''.join(out)

problems = []
for dirpath, _, files in os.walk(ROOT):
    for fn in sorted(files):
        if not fn.endswith('.m'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, encoding='utf-8', errors='replace') as f:
            src = f.read()
        depth = 0
        for ln, raw in enumerate(src.split('\n'), 1):
            line = strip_line(raw)
            if OPENERS.match(line):
                # ignore one-liners like: if cond, stmt; end / for ...; end
                opens = 1
                ends_here = 0
                for m in ENDTOK.finditer(line):
                    prev = line[:m.start()].rstrip()
                    c = prev[-1] if prev else ''
                    if c != '' and c in '([{,:':
                        continue
                    ends_here += 1
                depth += opens - ends_here
                continue
            for m in ENDTOK.finditer(line):
                prev = line[:m.start()].rstrip()
                c = prev[-1] if prev else ''
                nxt = line[m.end():].strip()
                if c != '' and c in '([{,:':
                    continue
                depth -= 1
            if depth < 0:
                problems.append(f"{path}:{ln}: negative block depth -> {raw.strip()}")
                depth = 0
        if depth != 0:
            problems.append(f"{path}: unbalanced blocks, final depth = {depth}")
        # suspicious patterns (scan the string/comment-stripped source)
        stripped = '\n'.join(strip_line(l) for l in src.split('\n'))
        for m in re.finditer(r'\w+\([^()]*\)\s*\(', stripped):
            problems.append(f"{path}: possible call-result indexing -> ...{m.group(0)[:40]}")

if problems:
    print("PROBLEMS:")
    for p in problems:
        print(" ", p)
    sys.exit(1)
print("All .m files passed the static block-balance check.")
