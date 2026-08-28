"""Persian (RTL) text rendering: uharfbuzz shaping + fontTools outlines + PIL.

- Correctly shaped Persian (contextual joining, RTL order).
- Bidirectional strings: split into directional runs, laid out as an RTL
  paragraph (first logical run at the right edge).
- Font fallback: Vazirmatn (Persian + Latin) with DejaVu Sans fallback for
  missing glyphs (Greek, math, arrows, superscripts).
- Inline markup:  ^{...} superscript,  _{...} subscript.
Results are cached.
"""
import os
from functools import lru_cache

import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

FONT_DIR = os.path.join(os.path.dirname(__file__), '..', 'fonts')

_FONTS = {
    ('vazir', 'regular'): 'Vazirmatn-Regular.ttf',
    ('vazir', 'medium'): 'Vazirmatn-Medium.ttf',
    ('vazir', 'semibold'): 'Vazirmatn-SemiBold.ttf',
    ('vazir', 'bold'): 'Vazirmatn-Bold.ttf',
    ('vazir', 'black'): 'Vazirmatn-Black.ttf',
    ('dejavu', 'regular'): 'DejaVuSans.ttf',
    ('dejavu', 'medium'): 'DejaVuSans.ttf',
    ('dejavu', 'semibold'): 'DejaVuSans.ttf',
    ('dejavu', 'bold'): 'DejaVuSans-Bold.ttf',
    ('dejavu', 'black'): 'DejaVuSans-Bold.ttf',
}

_ttcache = {}
_face_cache = {}
_cmap_cache = {}


def _font_file(family, weight):
    key = (family, weight)
    if key not in _FONTS:
        key = (family, 'regular')
    return os.path.join(FONT_DIR, _FONTS[key])


def _tt(family, weight):
    key = (family, weight)
    if key not in _ttcache:
        path = _font_file(family, weight)
        tt = TTFont(path)
        glyf = tt['glyf']
        for name in list(glyf.keys()):
            g = glyf[name]
            try:
                g.expand(glyf)
            except Exception:
                pass
        _ttcache[key] = tt
    return _ttcache[key]


def _face(family, weight):
    key = (family, weight)
    if key not in _face_cache:
        with open(_font_file(family, weight), 'rb') as f:
            _face_cache[key] = hb.Face(f.read())
    return _face_cache[key]


def _cmap(family, weight):
    key = (family, weight)
    if key not in _cmap_cache:
        _cmap_cache[key] = set(_tt(family, weight).getBestCmap().keys())
    return _cmap_cache[key]


def _is_rtl_char(ch):
    cp = ord(ch)
    if (0x0660 <= cp <= 0x0669) or (0x06F0 <= cp <= 0x06F9) or cp in (0x066B, 0x066C):
        return False
    return ((0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F)
            or (0xFB50 <= cp <= 0xFDFF) or (0xFE70 <= cp <= 0xFEFF)
            or (0x07C0 <= cp <= 0x07C9) or (0x08A0 <= cp <= 0x08FF))


def _parse_rich(text):
    """Split into [(scale_factor, y_shift_fraction, s)] honoring ^{..} _{..}."""
    parts = []
    i, n = 0, len(text)
    buf = ''
    while i < n:
        if text[i] in '^_' and i + 1 < n and text[i + 1] == '{':
            j = text.find('}', i + 2)
            if j != -1:
                if buf:
                    parts.append((1.0, 0.0, buf))
                    buf = ''
                if text[i] == '^':
                    parts.append((0.62, -0.34, text[i + 2:j]))
                else:
                    parts.append((0.62, 0.16, text[i + 2:j]))
                i = j + 1
                continue
        buf += text[i]
        i += 1
    if buf:
        parts.append((1.0, 0.0, buf))
    return parts


def _shape(text, size, family, weight, direction):
    font = hb.Font(_face(family, weight))
    s64 = max(1, int(round(size * 64)))
    font.scale = (s64, s64)
    buf = hb.Buffer()
    buf.direction = direction
    buf.add_str(text)
    hb.shape(font, buf)
    go = _tt(family, weight).getGlyphOrder()
    return [(go[gi.codepoint], po.x_offset / 64.0, po.y_offset / 64.0, po.x_advance / 64.0)
            for gi, po in zip(buf.glyph_infos, buf.glyph_positions)]


def _contour_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a * 0.5


def _font_for_char(ch, weight):
    if ch == ' ':
        return 'vazir'
    cp = ord(ch)
    if cp in _cmap('vazir', weight):
        return 'vazir'
    if cp in _cmap('dejavu', weight):
        return 'dejavu'
    return 'dejavu'


def _split_segments(rtext, direction, weight):
    """Split run text into [(text, direction, family, scale, yshift_frac)]."""
    rich = _parse_rich(rtext)
    segs = []
    for scale, yshift, s in rich:
        cur = ''
        cur_fam = None
        for ch in s:
            if ch == ' ':
                cur += ch
                continue
            fam = _font_for_char(ch, weight)
            if cur_fam is None:
                cur_fam = fam
            if fam != cur_fam:
                segs.append((cur, direction, cur_fam, scale, yshift))
                cur = ch
                cur_fam = fam
            else:
                cur += ch
        if cur:
            segs.append((cur, direction, cur_fam, scale, yshift))
    merged = []
    for (t, d, f, sc, ys) in segs:
        if merged and merged[-1][1] == d and merged[-1][2] == f and merged[-1][3] == sc and merged[-1][4] == ys:
            merged[-1] = (merged[-1][0] + t, d, f, sc, ys)
        else:
            merged.append((t, d, f, sc, ys))
    return merged


def _split_runs(text):
    """Split into [(run_text, direction)] in logical order (no markup here)."""
    runs = []
    cur = ''
    cur_dir = None

    def flush():
        nonlocal cur, cur_dir
        if cur and cur_dir is not None:
            if runs and runs[-1][1] == cur_dir:
                runs[-1][0] += cur
            else:
                runs.append([cur, cur_dir])
        cur = ''
        cur_dir = None

    for ch in text:
        if ch == ' ':
            cur += ch
            continue
        d = 'rtl' if _is_rtl_char(ch) else 'ltr'
        if cur_dir is None:
            cur_dir = d
        if d != cur_dir:
            flush()
            cur = ch
            cur_dir = d
        else:
            cur += ch
    flush()
    return runs


@lru_cache(maxsize=400)
def _render_key2(text, size, weight, color):
    runs = _split_runs(text)
    if not runs:
        return None
    polys = []
    x_cursor = 0.0
    for rtext, rdir in runs:
        segs = _split_segments(rtext, rdir, weight)
        run_width = 0.0
        shaped = []
        for (stext, sdir, sfam, sscale, syshift) in segs:
            infos = _shape(stext, size * sscale, sfam, weight, sdir)
            w = sum(xa for _, _, _, xa in infos)
            shaped.append((sfam, sscale, syshift, infos))
            run_width += w
        x_cursor -= run_width
        x = x_cursor
        for (sfam, sscale, syshift, infos) in shaped:
            tt = _tt(sfam, weight)
            glyf = tt['glyf']
            scale = (size * sscale) / tt['head'].unitsPerEm
            yoff = syshift * size
            for name, xo, yo, xa in infos:
                if name is not None:
                    g = glyf[name]
                    try:
                        coords = list(g.getCoordinates(glyf)[0])
                    except Exception:
                        coords = []
                    if coords:
                        pts = [(x + xo + fx * scale, -(yo + fy * scale) + yoff)
                               for (fx, fy) in coords]
                        polys.append(pts)
                x += xa

    allpts = [p for pts in polys for p in pts]
    if not allpts:
        return (Image.new('RGBA', (8, int(size)), (0, 0, 0, 0)), 8, int(size), size // 2, size * 0.8, size * 0.2)

    minx = min(p[0] for p in allpts)
    maxx = max(p[0] for p in allpts)
    miny = min(p[1] for p in allpts)
    maxy = max(p[1] for p in allpts)
    w = int(maxx - minx) + 2
    h = int(maxy - miny) + 2
    ox, oy = -minx + 1, -miny + 1

    SS = 3
    mask = Image.new('L', (max(1, w * SS), max(1, h * SS)), 0)
    md = ImageDraw.Draw(mask)
    first_area_sign = 0
    for pts in polys:
        if not pts or len(pts) < 3:
            continue
        pts_s = [((px + ox) * SS, (py + oy) * SS) for (px, py) in pts]
        area = _contour_area(pts_s)
        if area == 0:
            continue
        sign = 1 if area > 0 else -1
        if first_area_sign == 0:
            first_area_sign = sign
        fill = 255 if sign == first_area_sign else 0
        md.polygon(pts_s, fill=fill)
    img = mask.resize((w, h), Image.LANCZOS)
    r, g, b = color[0], color[1], color[2]
    anp = np.zeros((h, w, 4), dtype=np.uint8)
    anp[..., 0] = r
    anp[..., 1] = g
    anp[..., 2] = b
    anp[..., 3] = np.asarray(img)
    out = Image.fromarray(anp, 'RGBA')
    return (out, w, h, oy, -miny if miny < 0 else 0, maxy if maxy > 0 else 0)


@lru_cache(maxsize=1024)
def text_size(text, size, weight='regular'):
    img, w, h, bl, asc, desc = _render_key2(text, int(size), weight, (0, 0, 0, 0))
    return (w, h, bl, asc, desc)


def render(text, size, weight='regular', color=(255, 255, 255)):
    """Returns (RGBA image, w, h, baseline_y)."""
    r = _render_key2(text, int(size), weight, color)
    if r is None:
        return (Image.new('RGBA', (2, 2), (0, 0, 0, 0)), 2, 2, 0)
    return r[:4]


def paste_text(canvas, xy, text, size, weight='regular', color=(255, 255, 255),
               align='right'):
    """Paste text on canvas. xy is the anchor point:
    align 'right' -> xy is top-RIGHT of the text block
    align 'left'  -> xy is top-LEFT
    align 'center'-> xy is top-CENTER
    Returns (w, h, baseline_y).
    """
    r = render(text, size, weight, color)
    img, w, h, bl = r
    if w == 0:
        return (0, 0, 0)
    x, y = int(xy[0]), int(xy[1])
    if align == 'right':
        x = x - w
    elif align == 'center':
        x = x - w // 2
    canvas.alpha_composite(img, (x, y))
    return (w, h, bl)


def wrap_width(text, size, weight, max_w):
    """Greedy wrap (word based, RTL order preserved). Returns list of lines."""
    words = text.split(' ')
    lines = []
    cur = ''
    for wd in words:
        trial = (cur + ' ' + wd).strip()
        w, _, _, _, _ = text_size(trial, size, weight)
        if w <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines
