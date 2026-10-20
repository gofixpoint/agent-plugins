"""Reusable props for isometric scenes. Each takes a Scene plus a world-space
position and size, draws itself, and returns its Box (or a tuple of handles)
so the caller can anchor cables and callouts to its faces.

LEDs use the `led` class; anim.py lights them with the `--led` delay set on an
enclosing group, so props never need to know about timing.
"""


def rack(sc, x, y, dx, dy, dz, name, blades=6):
    """Server rack: stacked 1U blades with vents and status LEDs."""
    b = sc.box(x, y, 0, dx, dy, dz)
    m = 0.18
    bh = (dz - 2 * m) / blades
    for i in range(blades):
        v = m + i * bh
        sc.rect(b.front, m, v + 0.06, dx - 2 * m, bh - 0.12, "front hair")
        for k in range(5):
            sc.rect(b.front, m + 0.25 + k * 0.17, v + 0.2, 0.08, bh - 0.4, "deep hair")
        sc.circle(b.front, dx - m - 0.25, v + bh / 2, 0.075, "led" if i % 2 == 0 else "deep hair", n=14)
        sc.circle(b.front, dx - m - 0.5, v + bh / 2, 0.075, "deep hair", n=14)
    for k in range(4):
        sc.rect(b.side, 0.4 + k * 0.55, dz * 0.25, 0.25, dz * 0.5, "deep hair")
    sc.text_top(name, b.top(0.25, dy - 0.35), 0.32)
    return b


TERMINAL = ["$ claude", "> agent: fixing #412", "  editing auth.ts", "  tests: 48 passed", "> agent: done ✓"]


def laptop(sc, x, y, dx, dy, lines=TERMINAL, line_delays=None):
    """Open laptop with a leaning lid and terminal text on the screen.
    Returns (base Box, lid(u, v) -> world point, v in 0..1 up the lid).
    line_delays: optional per-line animation-delay seconds (see anim.py `term`)."""
    base = sc.box(x, y, 0, dx, dy, 0.22)
    kw, kh = 0.26, 0.26
    cols, rows = int((dx - 0.6) / (kw + 0.07)), 4
    u0 = (dx - cols * (kw + 0.07)) / 2
    for r in range(rows):
        for c in range(cols):
            sc.rect(base.top, u0 + c * (kw + 0.07), 0.55 + r * (kh + 0.07), kw, kh, "front hair")
    sc.rect(base.top, dx / 2 - 0.7, 0.55 + rows * (kh + 0.07) + 0.12, 1.4, 0.55, "side hair")
    # lid: hinged at the back edge, leaning back
    hy, z0 = y + 0.12, 0.22
    lean, sh = 0.6, 2.9
    ty, z1 = hy - lean, z0 + sh
    t = 0.12  # lid thickness
    sc.poly([(x, ty - t, z1), (x + dx, ty - t, z1), (x + dx, ty, z1), (x, ty, z1)], "top")
    sc.poly([(x + dx, hy, z0), (x + dx, hy - t, z0), (x + dx, ty - t, z1), (x + dx, ty, z1)], "side")
    sc.poly([(x, hy, z0), (x + dx, hy, z0), (x + dx, ty, z1), (x, ty, z1)], "front")

    def lid(u, v):
        return (x + u, hy - lean * v, z0 + sh * v)

    m = 0.16
    sc.poly([lid(m, 0.06), lid(dx - m, 0.06), lid(dx - m, 0.95), lid(m, 0.95)], "screen hair")
    for i, s in enumerate(lines):
        st = f"animation-delay:{line_delays[i]:.2f}s" if line_delays else ""
        sc.text(s, lid(m + 0.2, 0.86 - i * 0.15), (1, 0, 0), (0, lean / sh, -1), 0.24,
                cls="scr term" if line_delays else "scr", style=st)
    return base, lid


def droplet(sc, x, y, dx, dy, dz, name):
    """Single cloud VM: a box with vents, a status LED, and a port on top."""
    b = sc.box(x, y, 0, dx, dy, dz)
    for k in range(7):
        sc.rect(b.front, 0.3 + k * 0.22, 0.35, 0.1, dz * 0.45, "deep hair")
    sc.circle(b.front, dx - 0.55, dz * 0.58, 0.28, "side hair")
    sc.circle(b.front, dx - 0.55, dz * 0.58, 0.1, "led", n=16)
    sc.circle(b.top, dx / 2, dy / 2 - 0.15, 0.62, "front hair")
    sc.circle(b.top, dx / 2, dy / 2 - 0.15, 0.38, "side hair")
    for k in range(3):
        sc.rect(b.side, 0.35 + k * 0.5, dz * 0.3, 0.22, dz * 0.4, "deep hair")
    sc.text_top(name, b.top(0.22, dy - 0.3), 0.3)
    return b


def sandbox_tray(sc, x, y, dx, dy, name, cols=3, rows=2, lit=(0, 2, 4)):
    """Tray of small cubes (ephemeral sandboxes). `lit` indexes cubes whose LED is on.
    Returns (tray Box, list of cube Boxes, back row first)."""
    tray = sc.box(x, y, 0, dx, dy, 0.32)
    c, g = 0.95, 0.28
    u0 = (dx - (cols * c + (cols - 1) * g)) / 2
    v0 = 0.35
    cubes = []
    for r in range(rows):
        for k in range(cols):
            i = r * cols + k
            cb = sc.box(x + u0 + k * (c + g), y + v0 + r * (c + g), 0.32, c, c, c * 0.95)
            sc.circle(cb.top, c / 2, c / 2, 0.2, "side hair", n=18)
            sc.circle(cb.front, c - 0.2, c * 0.75, 0.06, "led" if i in lit else "deep hair", n=12)
            sc.rect(cb.front, 0.15, 0.15, 0.45, 0.08, "deep hair")
            cubes.append(cb)
    sc.text_front(name, tray.front(0.15, 0.08), 0.2)
    return tray, cubes


def baseplate(sc, x0, y0, x1, y1, label, thickness=0.75):
    """Long machined plate: ruler strip along the front, engraved label, screw
    holes, and a recessed status screen at the front-right. Returns (plate Box,
    origin for status text on the screen)."""
    plate = sc.box(x0, y0, -thickness, x1 - x0, y1 - y0, thickness)
    L, D = x1 - x0, y1 - y0
    sc.rect(plate.top, 0.3, D - 0.85, L - 0.6, 0.55, "front hair")
    for i in range(int((L - 1) / 0.25)):
        u = 0.5 + i * 0.25
        tick = 0.22 if i % 4 == 0 else 0.11
        sc.line(plate.top(u, D - 0.3), plate.top(u, D - 0.3 - tick), "hair")
    sc.text_front(label, plate.front(0.6, 0.22), 0.3)
    sc.rect(plate.front, L - 6.0, 0.14, 5.2, 0.46, "screen hair")
    return plate, plate.front(L - 5.55, 0.25)


def screw_holes(sc, plate):
    for u in (0.5, plate.dx - 0.5):
        sc.circle(plate.top, u, 0.5, 0.14, "deep hair", n=16)


def island(sc, x, y, dx, dy, label):
    """Small floor plate for one provider, label engraved on the front edge."""
    b = sc.box(x, y, -0.45, dx, dy, 0.45)
    sc.text_front(label, b.front(0.25, 0.12), 0.24)
    for u in (0.3, dx - 0.3):
        sc.circle(b.top, u, 0.3, 0.1, "deep hair", n=14)
    return b


def post(sc, x, y, height, size=0.6):
    return sc.box(x, y, 0, size, size, height)


def rail(sc, x, y, z, length, label, depth=0.6):
    """Overhead rail with ruler ticks on its front face and an accent label."""
    r = sc.box(x, y, z, length, depth, depth)
    for i in range(int((length - 0.4) / 0.25)):
        u = 0.2 + i * 0.25
        tick = 0.2 if i % 4 == 0 else 0.1
        sc.line(r.front(u, depth), r.front(u, depth - tick), "hair")
    sc.text_front(label, r.front(0.5, 0.13), 0.36, cls="neteng")
    return r


def carriage(sc, xc, y, z):
    """Small block hanging under a rail at x = xc, with an accent port."""
    c = sc.box(xc - 0.35, y - 0.05, z - 0.45, 0.7, 0.7, 0.45)
    sc.circle(c.front, 0.35, 0.22, 0.09, "netfill", n=12)
    return c


def port(sc, x, y, z, r=0.14):
    """Accent dot lying flat on a top face, where a cable lands."""
    sc.circle(lambda u, v: (x + u, y + v, z), 0, 0, r, "netfill", n=14)
