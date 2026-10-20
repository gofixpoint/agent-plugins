#!/usr/bin/env python3
"""'Agents across clouds' (Oct 2026 tweet): coding agents on Hetzner, a laptop,
a DigitalOcean droplet, and two sandbox providers, networked by Amika.

Outputs land in assets/agents-across-clouds/. Usage:
    python3 agents_across_clouds.py <out-dir>
writes every still as <name>.svg plus the animated j-drafting-fast.html; see
../GUIDE.md for turning those into PNG and MP4.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anim  # noqa: E402
from anim import delay  # noqa: E402
from iso import Scene, THEMES, W, vec, page, callout, title_cad, title_codex, bezier_points  # noqa: E402
from parts import (rack, laptop, droplet, sandbox_tray, baseplate, screw_holes, island,  # noqa: E402
                   post, rail, carriage, port)

TITLE = "Don’t lock your agents into one box"

# Seconds from the start of the loop. (start, step) pairs stagger a row of
# elements left to right. The intro is fast: hosts land by ~1s, the network is
# wired by ~2.5s, and packets flow for the rest of the loop.
TIMELINE = dict(
    loop=10.0,
    plate=0.0, posts=0.1, rail=0.3,
    modules=(0.35, 0.12),     # drop-in, one per host group
    carriages=(1.15, 0.056),  # slide out along the rail
    cables=(1.65, 0.0625),    # extend down to each host
    ports=(1.90, 0.061),
    leds=(1.99, 0.06),        # per host with LEDs
    led_blink=2.14, blink_a=2.45, blink_b=2.85,
    callouts=(2.08, 0.075),
    status=2.21,
    terminal=(2.02, 2.33, 2.95, 3.75, 4.55),
    packets=(2.45, 0.23),
)


def at(key, i):
    start, step = TIMELINE[key]
    return start + i * step


# ---------- baseplate with network rail ----------

def scene_baseplate(animated=False):
    """Hosts on one long plate under an overhead rail; a cable drops from a
    carriage on the rail to each host. With animated=True, adds packets and
    returns their keyframes."""
    T = TIMELINE
    sc = Scene()
    keyframes = []

    with sc.group("a-plate", delay(T["plate"])):
        plate, status_at = baseplate(sc, -2.2, -1.2, 28.4, 6.4, "/net/amika · private agent network")
        with sc.group("a-fade", delay(T["status"])):
            sc.text_front("6 hosts · 1 network", status_at, 0.28, cls="scr")
        screw_holes(sc, plate)

    RY, RZ = 2.1, 7.6  # rail position: cables hang at y = RY + 0.3
    with sc.group("a-post", delay(T["posts"])):
        post(sc, -1.6, RY, RZ)

    def host(i, led_i, draw):
        st = delay(at("modules", i)) + (f";--led:{at('leds', led_i):.2f}s" if led_i is not None else "")
        with sc.group(f"a-mod m{i + 1}", st):
            return draw()

    ra = host(0, 0, lambda: rack(sc, 0.0, 0.5, 2.5, 3.0, 5.0, "hetzner-1"))
    rb = host(1, 1, lambda: rack(sc, 2.9, 0.5, 2.5, 3.0, 4.2, "hetzner-2", blades=5))
    term = list(T["terminal"]) if animated else None
    base, _ = host(2, None, lambda: laptop(sc, 7.2, 1.0, 4.4, 3.0, line_delays=term))
    dr = host(3, 2, lambda: droplet(sc, 13.4, 0.8, 2.8, 2.8, 2.5, "do-droplet"))
    ta, ca = host(4, 3, lambda: sandbox_tray(sc, 17.8, 0.6, 4.0, 3.4, "sandbox · provider a"))
    tb, cb = host(5, 4, lambda: sandbox_tray(sc, 22.5, 0.6, 4.0, 3.4, "sandbox · provider b", lit=(1, 3, 5)))

    # Cable drops, in rail order. None = the laptop, whose cable curves onto the lid.
    lx = 7.2 + 2.2
    lap = ((lx, RY + 0.3, RZ - 0.4), (lx, RY + 0.3, RZ - 2.2), (lx, 0.46, 4.72), (lx, 0.46, 3.12))
    drops = [(ra.cx(), ra.topz), (rb.cx(), rb.topz), (lx, None),
             (dr.cx(), dr.topz), (ta.cx(), ca[4].topz), (tb.cx(), cb[4].topz)]
    for k, (xc, zt) in enumerate(drops):
        with sc.group("a-cable", delay(at("cables", k))):
            if zt is None:
                sc.bezier(*lap, "net")
            else:
                sc.line((xc, RY + 0.3, RZ - 0.4), (xc, RY + 0.3, zt), "net")
        if zt is not None:
            with sc.group("a-port", delay(at("ports", k))):
                port(sc, xc, RY + 0.3, zt)

    with sc.group("a-rail", delay(T["rail"])):
        r = rail(sc, -1.9, RY, RZ, 30.0, "amika.dev")

    start_x = -1.2  # carriages slide out from the rail's left end
    for k, (xc, _) in enumerate(drops):
        dx, dy = vec((start_x - xc, 0, 0))
        with sc.group("a-car", f"--dx:{dx:.3f}px;--dy:{dy:.3f}px;" + delay(at("carriages", k))):
            carriage(sc, xc, RY, RZ)

    with sc.group("a-post", delay(T["posts"])):
        post(sc, 27.6, RY, RZ)

    if animated:
        # Packets ride the rail's front face, drop down the carriage, then the
        # cable. Each route runs one packet out and one back.
        for k, (xc, zt) in enumerate(drops):
            route = [(start_x + 0.2, RY + 0.62, RZ + 0.3), (xc, RY + 0.62, RZ + 0.3),
                     (xc, RY + 0.62, RZ - 0.25), (xc, RY + 0.3, RZ - 0.4)]
            route += bezier_points(*lap, n=10)[1:] if zt is None else [(xc, RY + 0.3, zt)]
            keyframes.append(anim.route_keyframes(f"r{k}", route))
            dur = 1.6 + xc * 0.035
            t0 = at("packets", k)
            anim.packet(sc, f"r{k}", dur, t0)
            anim.packet(sc, f"r{k}", dur, t0 + dur * 0.55, "reverse")

    anchors = {"HETZNER": rb.front(0.4, 0.0), "MY LAPTOP": base.front(2.2, 0.0),
               "DO DROPLET": dr.front(1.4, 0.0), "SANDBOX A": ta.front(3.5, 0.0),
               "SANDBOX B": tb.front(3.5, 0.0)}
    return sc, anchors, keyframes


def callouts(to_screen, anchors, label_y, animated=False):
    out = []
    for i, (label, p3) in enumerate(anchors.items()):
        c = callout(to_screen, p3, label, label_y)
        out.append(f'<g class="a-co" style="{delay(at("callouts", i))}">{c}</g>' if animated else c)
    return out


def baseplate_still(theme, title=None):
    sc, anchors, _ = scene_baseplate()
    if title is None:
        g, ts = sc.render((80, 120, W - 160, 610))
        return page(theme, [g] + callouts(ts, anchors, 790), corners={"tr": "AGENTS ACROSS CLOUDS"})
    g, ts = sc.render((80, 178, W - 160, 560))
    return page(theme, [title(THEMES[theme]), g] + callouts(ts, anchors, 815))


def baseplate_video(theme="light"):
    """Drafting title + baseplate, with the full build-up and packet loop."""
    T = TIMELINE
    sc, anchors, keyframes = scene_baseplate(animated=True)
    g, ts = sc.render((80, 178, W - 160, 560))
    body = [g] + callouts(ts, anchors, 815, animated=True) + [
        anim.fade_overlay(theme),
        title_cad(THEMES[theme], TITLE, y=114, size=56, hw=510, spacing=7),  # stays up through the fade
    ]
    blink = {"--led-blink": f"{T['led_blink']}s", "--blink-a": f"{T['blink_a']}s", "--blink-b": f"{T['blink_b']}s"}
    return anim.html(page(theme, body), theme, T["loop"], keyframes, blink)


# ---------- islands around a hub ----------

def scene_islands():
    """Each provider on its own plate, floor cables to a central Amika hub."""
    sc = Scene()
    # floor cables first: plates drawn later cover their ends
    ends = [((5.0, 4.6, 0), (10.7, 7.4, 0)), ((12.0, 3.8, 0), (12.0, 6.9, 0)),
            ((18.4, 4.4, 0), (13.3, 7.4, 0)), ((6.0, 11.5, 0), (10.7, 8.6, 0)),
            ((15.8, 12.0, 0), (12.6, 9.1, 0))]
    for a, b in ends:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0)
        c1 = (a[0] + (mid[0] - a[0]) * 0.2 + (b[1] - a[1]) * 0.15, a[1] + (mid[1] - a[1]) * 0.9, 0)
        c2 = (b[0] - (b[0] - mid[0]) * 0.9, b[1] - (b[1] - mid[1]) * 0.2 - (b[0] - a[0]) * 0.1, 0)
        sc.bezier(a, c1, c2, b, "net")

    # back row
    island(sc, 0.0, 0.0, 7.0, 4.6, "hetzner · fsn1")
    rack(sc, 0.7, 0.6, 2.5, 3.0, 4.6, "hx-1")
    rack(sc, 3.6, 0.6, 2.5, 3.0, 3.8, "hx-2", blades=5)
    island(sc, 10.0, -0.6, 4.4, 4.4, "digitalocean · nyc3")
    droplet(sc, 10.8, 0.1, 2.8, 2.8, 2.5, "droplet")
    island(sc, 17.4, 0.0, 5.2, 4.4, "sandbox provider a")
    sandbox_tray(sc, 18.0, 0.5, 4.0, 3.4, "ephemeral")

    # hub
    hx, hy = 12.0, 8.0
    sc.box(hx - 1.9, hy - 1.6, -0.45, 3.8, 3.2, 0.45)
    hub = sc.box(hx - 1.3, hy - 1.1, 0, 2.6, 2.2, 1.5)
    sc.rect(hub.top, 0.2, 0.2, 2.2, 1.8, "front hair")
    sc.text_top("amika", hub.top(0.35, 1.2), 0.5, cls="neteng")
    for k in range(4):
        sc.circle(hub.front, 0.45 + k * 0.55, 0.75, 0.12, "netfill", n=14)

    # front row
    island(sc, 1.2, 11.5, 6.2, 4.4, "localhost · my laptop")
    laptop(sc, 2.1, 12.6, 4.4, 3.0)
    island(sc, 14.6, 12.0, 5.2, 4.4, "sandbox provider b")
    sandbox_tray(sc, 15.2, 12.5, 4.0, 3.4, "ephemeral", lit=(1, 3, 5))
    return sc


def islands_still(theme):
    g, _ = scene_islands().render((90, 110, W - 180, 690))
    return page(theme, [g], corners={
        "tl": "Fig 1", "tr": "AGENTS ACROSS CLOUDS", "bl": "ONE NETWORK",
        "br": "hetzner · laptop · droplet · sandboxes → amika.dev"})


def cad(t):
    return title_cad(t, TITLE)


def codex(t):
    return title_codex(t, TITLE)


STILLS = {
    "a-baseplate": lambda: baseplate_still("light"),
    "b-islands": lambda: islands_still("light"),
    "d-baseplate-dark": lambda: baseplate_still("dark"),
    "e-islands-dark": lambda: islands_still("dark"),
    "i-codex": lambda: baseplate_still("codex", codex),
    "j-drafting": lambda: baseplate_still("light", cad),
    "k-blueprint": lambda: baseplate_still("blueprint", cad),
}

if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, build in STILLS.items():
        (out / f"{name}.svg").write_text(build())
        print(out / f"{name}.svg")
    (out / "j-drafting-fast.html").write_text(baseplate_video())
    print(out / "j-drafting-fast.html")
