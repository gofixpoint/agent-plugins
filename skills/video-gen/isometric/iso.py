"""Isometric line-art engine: projection, scene graph, themes, and page framing.

Coordinates are world units: x runs right-down along the long axis, y runs
left-down toward the viewer, z is up. Everything projects through P(), and a
Scene collects SVG elements in projected units until render() fits it into a
pixel region of the 1600x900 page.
"""
import math
from contextlib import contextmanager

# Dimetric projection: x axis drops 18 degrees, y axis drops 40 degrees and is
# foreshortened to 0.8. Visible faces are top (+z), front (+y), and side (+x).
AX, AY, YS = math.radians(18), math.radians(40), 0.8
CX, SX = math.cos(AX), math.sin(AX)
CY, SY = math.cos(AY) * YS, math.sin(AY) * YS
W, H = 1600, 900
MONO = "'JetBrainsMono Nerd Font Mono','JetBrains Mono','SF Mono',Menlo,monospace"
SANS = "'Plus Jakarta Sans','Helvetica Neue',Helvetica,Arial,sans-serif"
FONTS = ("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800"
         "&amp;family=Cormorant+Garamond:ital,wght@1,500;1,600"
         "&amp;family=Barlow+Condensed:wght@500;600"
         "&amp;family=JetBrains+Mono:wght@400;600&amp;display=swap")


def P(x, y, z):
    return (x * CX - y * CY, x * SX + y * SY - z)


def vec(v):
    """Projected direction of a world-space vector."""
    a, b = P(*v), P(0, 0, 0)
    return (a[0] - b[0], a[1] - b[1])


def bezier_points(a, c1, c2, b, n=40):
    return [tuple((1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * c1[k]
                  + 3 * (1 - t) * t ** 2 * c2[k] + t ** 3 * b[k] for k in range(3))
            for t in (i / n for i in range(n + 1))]


def fmt(pts):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


# Face fills step light to dark: top, front, side, deep (recesses). `net` is the
# accent reserved for the network (cables, rail label, ports, packets).
THEMES = {
    "light": dict(bg="#ecebe7", card="#f8f8f6", border="#dcdad6", stroke="#8a8c90",
                  top="#ffffff", front="#f2f1ee", side="#e2e1dc", deep="#d4d3cd",
                  screen="#1b2130", screentext="#c9d2e3", ink="#131720",
                  muted="#6b7385", engrave="#9a9ca2", net="#d44a35", led="#00bb7f"),
    "dark": dict(bg="#0b0c10", card="#121419", border="#262a33", stroke="#a3a9b5",
                 top="#262a33", front="#1d2028", side="#171a21", deep="#121419",
                 screen="#07090d", screentext="#9fb0cc", ink="#eceae6",
                 muted="#8c94a5", engrave="#6c7383", net="#ff6a4f", led="#21d39a"),
    "codex": dict(bg="#e2d6bc", card="#f0e6cf", border="#cdbd9a", stroke="#6b563f",
                  top="#f7efdc", front="#ebe0c7", side="#ddd0b2", deep="#d1c19f",
                  screen="#3a2e22", screentext="#eadcbc", ink="#33281c",
                  muted="#7a6650", engrave="#8d7a5f", net="#b4402a", led="#4f8a5b"),
    "blueprint": dict(bg="#18305d", card="#22427c", border="#3d5d97", stroke="#dfe9ff",
                      top="#2a4d8b", front="#264781", side="#203f76", deep="#1c3970",
                      screen="#132a52", screentext="#dfe9ff", ink="#f3f7ff",
                      muted="#b0c3ea", engrave="#a8bce6", net="#ff7d5e", led="#86f0c4"),
}


def style(t):
    return f"""
  .top{{fill:{t['top']}}} .front{{fill:{t['front']}}} .side{{fill:{t['side']}}}
  .deep{{fill:{t['deep']}}}
  polygon,polyline,path,line{{stroke:{t['stroke']};stroke-width:1.25;stroke-linejoin:round;
    stroke-linecap:round;vector-effect:non-scaling-stroke}}
  polyline,path.open{{fill:none}}
  .hair{{stroke-width:0.8}}
  .screen{{fill:{t['screen']}}}
  .led{{fill:{t['led']};stroke:none}}
  .netfill{{fill:{t['net']}}}
  .net{{stroke:{t['net']}!important;stroke-width:2.6!important;fill:none}}
  .engrave{{fill:{t['engrave']};font-family:{MONO};letter-spacing:0.04em}}
  .scr{{fill:{t['screentext']};font-family:{MONO}}}
  .neteng{{fill:{t['net']};font-family:{MONO};font-weight:600;letter-spacing:0.06em}}
  .chrome{{fill:{t['muted']};font-family:{MONO};font-size:17px;letter-spacing:0.18em}}
  .callout{{fill:{t['ink']};font-family:{MONO};font-size:15px;letter-spacing:0.12em}}
  .lead{{stroke:{t['muted']};stroke-width:1;fill:none}}
  .leaddot{{fill:{t['muted']}}}
"""


class Box:
    """A drawn box. Face helpers map (u, v) on a face to a world point."""

    def __init__(self, x, y, z, dx, dy, dz):
        self.x, self.y, self.z, self.dx, self.dy, self.dz = x, y, z, dx, dy, dz

    def front(self, u, v):  # face y = y+dy, u along x, v up
        return (self.x + u, self.y + self.dy, self.z + v)

    def side(self, u, v):  # face x = x+dx, u from front edge going back, v up
        return (self.x + self.dx, self.y + self.dy - u, self.z + v)

    def top(self, u, v):  # face z = z+dz, u along x, v along y
        return (self.x + u, self.y + v, self.z + self.dz)

    @property
    def topz(self):
        return self.z + self.dz

    def cx(self):
        return self.x + self.dx / 2

    def cy(self):
        return self.y + self.dy / 2


class Scene:
    """Painter's-algorithm scene: later elements cover earlier ones, so draw
    back to front (increasing x and y)."""

    def __init__(self):
        self.els, self.pts = [], []

    def add(self, el, pts):
        self.els.append(el)
        self.pts.extend(pts)

    @contextmanager
    def group(self, cls, style=""):
        """Wrap elements in a <g>; anim.py targets these classes."""
        self.els.append(f'<g class="{cls}" style="{style}">')
        yield
        self.els.append("</g>")

    def poly(self, pts3, cls):
        pp = [P(*p) for p in pts3]
        self.add(f'<polygon class="{cls}" points="{fmt(pp)}"/>', pp)

    def polyline(self, pts3, cls):
        pp = [P(*p) for p in pts3]
        self.add(f'<polyline class="{cls}" points="{fmt(pp)}"/>', pp)

    def line(self, a, b, cls=""):
        self.polyline([a, b], cls)

    def bezier(self, a, c1, c2, b, cls="net"):
        self.polyline(bezier_points(a, c1, c2, b), cls)

    def box(self, x, y, z, dx, dy, dz, cls=""):
        b = Box(x, y, z, dx, dy, dz)
        x1, y1, z1 = x + dx, y + dy, z + dz
        self.poly([(x, y1, z), (x1, y1, z), (x1, y1, z1), (x, y1, z1)], f"front {cls}")
        self.poly([(x1, y1, z), (x1, y, z), (x1, y, z1), (x1, y1, z1)], f"side {cls}")
        self.poly([(x, y, z1), (x1, y, z1), (x1, y1, z1), (x, y1, z1)], f"top {cls}")
        return b

    def rect(self, face, u, v, w, h, cls="deep hair"):
        self.poly([face(u, v), face(u + w, v), face(u + w, v + h), face(u, v + h)], cls)

    def circle(self, face, u, v, r, cls="deep hair", n=28):
        self.poly([face(u + r * math.cos(2 * math.pi * i / n), v + r * math.sin(2 * math.pi * i / n))
                   for i in range(n)], cls)

    def text(self, s, origin3, u3, v3, size, cls="engrave", style=""):
        """Text laid on the plane spanned by world vectors u3 (baseline) and v3 (down)."""
        o = P(*origin3)
        a, b = vec(u3)
        c, d = vec(v3)
        st = f' style="{style}"' if style else ""
        self.add(f'<text class="{cls}" font-size="{size}" text-anchor="start"{st} '
                 f'transform="matrix({a:.4f},{b:.4f},{c:.4f},{d:.4f},{o[0]:.2f},{o[1]:.2f})">'
                 f'{s}</text>', [o])

    def text_top(self, s, origin3, size, **kw):
        self.text(s, origin3, (1, 0, 0), (0, 1, 0), size, **kw)

    def text_front(self, s, origin3, size, **kw):
        self.text(s, origin3, (1, 0, 0), (0, 0, -1), size, **kw)

    def render(self, region):
        """Fit into pixel region (x, y, w, h). Returns (svg <g>, world->pixel fn)."""
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        bx, by, bw, bh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
        rx, ry, rw, rh = region
        s = min(rw / bw, rh / bh)
        ox = rx + (rw - bw * s) / 2 - bx * s
        oy = ry + (rh - bh * s) / 2 - by * s

        def to_screen(p3):
            p = P(*p3)
            return (p[0] * s + ox, p[1] * s + oy)

        g = f'<g transform="matrix({s:.4f},0,0,{s:.4f},{ox:.2f},{oy:.2f})">' + "\n".join(self.els) + "</g>"
        return g, to_screen


# ---------- page framing ----------

BLUEPRINT_GRID = (
    '<defs><pattern id="bpminor" width="20" height="20" patternUnits="userSpaceOnUse">'
    '<path d="M20 0H0V20" fill="none" stroke="#ffffff" stroke-opacity="0.06" stroke-width="1"/></pattern>'
    '<pattern id="bpmajor" width="100" height="100" patternUnits="userSpaceOnUse">'
    '<rect width="100" height="100" fill="url(#bpminor)"/>'
    '<path d="M100 0H0V100" fill="none" stroke="#ffffff" stroke-opacity="0.12" stroke-width="1"/></pattern>'
    '<clipPath id="bpclip"><rect x="29" y="29" width="1542" height="842" rx="21"/></clipPath></defs>'
    '<rect x="29" y="29" width="1542" height="842" fill="url(#bpmajor)" clip-path="url(#bpclip)"/>')


def page(theme, body, corners=None):
    """Full 1600x900 SVG: background, rounded card, optional corner captions
    (dict with any of tl, tr, bl, br), then body elements in order."""
    t = THEMES[theme]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             f"<style>@import url('{FONTS}');", style(t), "</style>",
             f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
             f'<rect x="28" y="28" width="{W - 56}" height="{H - 56}" rx="22" fill="{t["card"]}" '
             f'stroke="{t["border"]}" stroke-width="1.5"/>']
    if theme == "blueprint":
        parts.append(BLUEPRINT_GRID)
    pos = {"tl": (72, 86, "start"), "tr": (W - 72, 86, "end"),
           "bl": (72, H - 66, "start"), "br": (W - 72, H - 66, "end")}
    for k, text in (corners or {}).items():
        x, y, anchor = pos[k]
        parts.append(f'<text class="chrome" x="{x}" y="{y}" text-anchor="{anchor}">{text}</text>')
    parts += body
    parts.append("</svg>")
    return "\n".join(parts)


def callout(to_screen, p3, label, label_y):
    """Dot on a world point, vertical leader down to a label at label_y (pixels)."""
    ax, ay = to_screen(p3)
    return "\n".join([
        f'<circle class="leaddot" cx="{ax:.1f}" cy="{ay:.1f}" r="3"/>',
        f'<polyline class="lead" points="{ax:.1f},{ay:.1f} {ax:.1f},{label_y - 22:.1f}"/>',
        f'<text class="callout" x="{ax:.1f}" y="{label_y:.1f}" text-anchor="middle">{label}</text>',
    ])


# ---------- titles ----------
# `hw` is half the rendered title width in pixels, tuned by eye per size so the
# rules stop just short of the text. Re-tune it when the copy or size changes.

def title_codex(t, text, y=118, size=68, hw=455):
    """Renaissance notebook: italic old-style serif with ruled flourishes."""
    c = t["ink"]
    out = [f'<text x="{W / 2}" y="{y}" text-anchor="middle" font-family="\'Cormorant Garamond\',Garamond,serif" '
           f'font-style="italic" font-weight="600" font-size="{size}" fill="{c}">{text}</text>']
    for sgn in (-1, 1):
        x0, x1 = W / 2 + sgn * (hw + 26), W / 2 + sgn * (hw + 150)
        ly = y - 20
        out.append(f'<line x1="{x0}" y1="{ly}" x2="{x1}" y2="{ly}" stroke="{c}" stroke-width="1.2"/>')
        out.append(f'<line x1="{x0 + sgn * 18}" y1="{ly + 6}" x2="{x1 - sgn * 30}" y2="{ly + 6}" '
                   f'stroke="{c}" stroke-width="0.8" opacity="0.6"/>')
        out.append(f'<path d="M{x1} {ly - 5} l{sgn * 5} 5 l{-sgn * 5} 5 l{-sgn * 5} -5 z" fill="{c}"/>')
    return "\n".join(out)


def title_cad(t, text, y=112, size=50, hw=455, spacing=6):
    """Drafting: condensed caps set into a dimension line with extension ticks."""
    c, m = t["ink"], t["muted"]
    L, R = 110, W - 110
    gap, a = 26, 12
    dy = y - 16
    out = [f'<text x="{W / 2}" y="{y}" text-anchor="middle" font-family="\'Barlow Condensed\',\'Arial Narrow\',sans-serif" '
           f'font-weight="600" font-size="{size}" letter-spacing="{spacing}" fill="{c}">{text.upper()}</text>']
    for x in (L, R):
        out.append(f'<line x1="{x}" y1="{dy - 26}" x2="{x}" y2="{dy + 26}" stroke="{m}" stroke-width="1.2"/>')
    out.append(f'<line x1="{L}" y1="{dy}" x2="{W / 2 - hw - gap}" y2="{dy}" stroke="{m}" stroke-width="1.2"/>')
    out.append(f'<line x1="{W / 2 + hw + gap}" y1="{dy}" x2="{R}" y2="{dy}" stroke="{m}" stroke-width="1.2"/>')
    out.append(f'<path d="M{L} {dy} l{a} -4.5 v9 z" fill="{m}"/>')
    out.append(f'<path d="M{R} {dy} l{-a} -4.5 v9 z" fill="{m}"/>')
    return "\n".join(out)
