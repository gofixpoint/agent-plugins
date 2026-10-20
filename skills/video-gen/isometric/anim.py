"""Animation layer: a CSS motion vocabulary keyed to group classes, packet
routes, and the HTML wrapper that video/capture/capture.mjs records.

The motions here carry no timing. A scene sets each element's start with an
inline `animation-delay` on its group (Scene.group(cls, style=...)), so the
choreography lives with the scene. Only CSS animations are allowed: capture.mjs
pauses and steps them frame by frame; SMIL and JS timers would drift.

Group classes:
  a-plate  rise into place        a-post   grow up from the floor
  a-rail   drop on from above     a-mod    drop in with a small overshoot
  a-car    slide along a rail from (--dx, --dy) to rest
  a-cable  extend downward        a-port   pop in
  a-fade   fade in                a-co     callout rises in
  a-pk     packet (see packet())  a-out    end-of-loop fade (see html())
Props draw LEDs with class `led`; they light at `--led` set on an enclosing
group, and some blink from --blink-a / --blink-b (set in html(vars=...)).
Laptop terminal lines carry class `term` plus their own delays.
"""
import math

from iso import P, THEMES, W, H

MOTION_CSS = """
  @keyframes rise{from{opacity:0;transform:translateY(1.2px)}to{opacity:1;transform:none}}
  @keyframes grow{from{transform:scaleY(0)}to{transform:none}}
  @keyframes raildrop{from{opacity:0;transform:translateY(-1.6px)}to{opacity:1;transform:none}}
  @keyframes drop{from{opacity:0;transform:translateY(-2.6px)}45%{opacity:1}to{opacity:1;transform:none}}
  @keyframes slide{from{opacity:0;transform:translate(var(--dx),var(--dy))}25%{opacity:1}to{opacity:1;transform:none}}
  @keyframes cable{from{transform:scaleY(0)}to{transform:none}}
  @keyframes pop{from{transform:scale(0)}to{transform:none}}
  @keyframes fadein{from{opacity:0}to{opacity:1}}
  @keyframes ledon{from{opacity:0}to{opacity:1}}
  @keyframes blink{0%{opacity:1}50%{opacity:.25}100%{opacity:1}}
  @keyframes pkfade{0%{opacity:0}6%{opacity:1}92%{opacity:1}100%{opacity:0}}
  @keyframes coin{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
  @keyframes out{0%,95%{opacity:0}100%{opacity:1}}
  .a-plate{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}
  .a-post{transform-box:fill-box;transform-origin:50% 100%;animation:grow .7s cubic-bezier(.3,.9,.3,1) both}
  .a-rail{animation:raildrop .6s cubic-bezier(.2,.9,.3,1.15) both}
  .a-mod{animation:drop .65s cubic-bezier(.2,.9,.3,1.18) both}
  .a-car{animation:slide .75s cubic-bezier(.25,.9,.3,1) both}
  .a-cable{transform-box:fill-box;transform-origin:50% 0;animation:cable .45s cubic-bezier(.4,0,.2,1) both}
  .a-port{transform-box:fill-box;transform-origin:50% 50%;animation:pop .35s cubic-bezier(.3,1.6,.5,1) both}
  .a-fade{animation:fadein .4s ease-out both}
  .a-co{animation:coin .5s cubic-bezier(.2,.8,.2,1) both}
  .led{animation:ledon .3s ease-out var(--led,0s) both}
  .a-mod .led:nth-of-type(3n){animation:ledon .3s ease-out var(--led-blink,0s) both,
    blink 1.3s steps(2,jump-none) var(--blink-a,0s) infinite}
  .a-mod .led:nth-of-type(4n+1){animation:ledon .3s ease-out var(--led-blink,0s) both,
    blink 1.9s steps(2,jump-none) var(--blink-b,0s) infinite}
  .term{animation:fadein .12s linear both}
  .a-pkdot{animation-name:pkfade;animation-timing-function:linear;animation-iteration-count:infinite;animation-fill-mode:both}
  .pkcore{fill:var(--net)}.pkglow{fill:var(--net);opacity:.22}
  .a-out{animation:out var(--loop) linear 0s both}
"""


def delay(t):
    return f"animation-delay:{t:.2f}s"


def route_keyframes(name, pts3):
    """@keyframes moving an element through world points at constant speed."""
    pp = [P(*p) for p in pts3]
    segs = [math.dist(a, b) for a, b in zip(pp, pp[1:])]
    total = sum(segs)
    frames, acc = [], 0.0
    for i, (x, y) in enumerate(pp):
        if i:
            acc += segs[i - 1]
        frames.append(f"{100 * acc / total:.2f}%{{transform:translate({x:.3f}px,{y:.3f}px)}}")
    return f"@keyframes {name}{{{''.join(frames)}}}"


def packet(sc, route, dur, start, direction="normal"):
    """A glowing dot looping along `route` (a route_keyframes name) forever."""
    with sc.group("a-pk", f"animation:{route} {dur:.2f}s linear {start:.2f}s infinite {direction} both"):
        sc.add(f'<g class="a-pkdot" style="animation-duration:{dur:.2f}s;animation-delay:{start:.2f}s">'
               f'<circle r="0.3" class="pkglow"/><circle r="0.15" class="pkcore"/></g>', [])


def fade_overlay(theme):
    """Card-colored rect that fades in over the last 5% of the loop so the
    video restarts from an empty card. Put persistent elements after it."""
    t = THEMES[theme]
    return f'<rect class="a-out" x="29" y="29" width="{W - 58}" height="{H - 58}" rx="21" fill="{t["card"]}"/>'


def html(svg, theme, loop, keyframes=(), vars=None):
    """1920x1080 page around the 1600x900 SVG, ready for capture.mjs."""
    t = THEMES[theme]
    root = {"--net": t["net"], "--loop": f"{loop:g}s", **(vars or {})}
    root_css = ";".join(f"{k}:{v}" for k, v in root.items())
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>html,body{{margin:0;background:{t['bg']}}}svg{{display:block;width:1920px;height:1080px}}</style>"
            f"<style>:root{{{root_css}}}{MOTION_CSS}{''.join(keyframes)}</style>"
            f"</head><body>{svg}</body></html>")
