#!/usr/bin/env python3
"""Cross-checks: ParamCatalog tags <-> defaultConfig fields; code-ASCII scan."""
import re, os, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]

# --- parse defaultConfig fields: cfg.A.B = ...
cfg_txt = (root / "simulation/defaultConfig.m").read_text(encoding="utf-8")
fields = {}
for m in re.finditer(r'cfg\.(\w+)\.(\w+)\s*=\s*([^;]+);', cfg_txt):
    sec, fld, val = m.group(1), m.group(2), m.group(3).strip()
    fields.setdefault(sec, {})[fld] = val

def tag_ok(tag):
    parts = tag.split('.')
    if len(parts) != 2: return False, f"bad depth: {tag}"
    sec, sub = parts
    m = re.match(r'^(\w+)(?:\((\d+)\))?$', sub)
    if not m: return False, f"bad token: {sub}"
    fld, idx = m.group(1), m.group(2)
    if sec not in fields: return False, f"unknown section {sec}"
    if fld not in fields[sec]: return False, f"unknown field {tag}"
    if idx is not None:
        v = fields[sec][fld]
        vals = v.strip('[]').split()
        if not (v.startswith('[') and len(vals) >= int(idx)):
            return False, f"{tag}: field not indexable ({v})"
    return True, ""

problems = []
cat = (root / "ui/ParamCatalog.m").read_text(encoding="utf-8")
tags = re.findall(r"'((?:Sim|Traj|IMU|GNSS|INS|Align|Fusion)\.[\w()]+)'", cat)
for t in sorted(set(tags)):
    ok, why = tag_ok(t)
    if not ok: problems.append(f"ParamCatalog: {why}")
    # dropdown values sanity
print(f"  checked {len(set(tags))} unique UI tags against defaultConfig: {'OK' if not problems else 'ISSUES'}")

# --- every dropdown/text/number control value type consistency
# (rough: for 'drop' rows, Items cell must contain the default value)
for m in re.finditer(r"'([\w\s&]+)','([^']*)','((?:Sim|Traj|IMU|GNSS|INS|Align|Fusion)\.[\w()]+)','(num|check|drop|text)',([^;]+);\n", cat):
    label, _lbl2, tag, typ, extra = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    sec, sub = tag.split('.')
    fld = re.match(r'^(\w+)', sub).group(1)
    dv = fields[sec][fld]
    if typ == 'check' and dv not in ('true', 'false'):
        problems.append(f"{tag}: checkbox default not logical ({dv})")
    if typ == 'drop':
        if '(' in extra:    # dynamic item list (function call) — skip literal check
            continue
        items = re.findall(r"'(\w+)'", extra)
        if dv.strip("'") not in items:
            problems.append(f"{tag}: dropdown default '{dv}' not in items {items}")
    if typ == 'text' and not dv.startswith("'"):
        problems.append(f"{tag}: text default not a char ({dv})")

# --- ASCII-only code outside strings/comments
bad_re = re.compile(r'[^\x00-\x7F]')
for dp, _, fns in os.walk(root):
    for fn in fns:
        if not fn.endswith('.m'): continue
        p = os.path.join(dp, fn)
        for ln, line in enumerate(open(p, encoding='utf-8', errors='replace'), 1):
            # strip comments and strings
            out = []; in_s = False
            for ch in line:
                if ch == "'": in_s = not in_s; out.append(' ')
                elif in_s: out.append(' ')
                elif ch == '%': break
                else: out.append(ch)
            if bad_re.search(''.join(out)):
                problems.append(f"{p}:{ln}: non-ASCII in code area")
print(f"  non-ASCII code scan: {'OK' if not any('non-ASCII' in x for x in problems) else 'ISSUES'}")

if problems:
    print("PROBLEMS:")
    for x in problems: print(" -", x)
    sys.exit(1)
print("All UI/config cross-checks passed.")
