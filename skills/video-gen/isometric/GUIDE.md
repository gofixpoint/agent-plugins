# Isometric technical diagrams

Line-art machines (server racks, laptops, VMs, sandbox trays) on a machined
plate, drawn in a dimetric projection with face shading. The network is the
only thing in the accent color, so the eye follows it. Titles borrow from CAD
drawings (dimension lines) or Renaissance notebooks (italic serif). Output is
1600x900 SVG rendered to 3200x1800 PNG, plus an optional looping build-up video.

Plain Python 3 with no dependencies; rendering uses headless Chrome and ffmpeg.

## Files

| File | What's in it |
| --- | --- |
| `iso.py` | Engine: projection `P()`, `Scene` and `Box`, themes, `page()` framing, `callout()`, titles |
| `parts.py` | Props: `rack`, `laptop`, `droplet`, `sandbox_tray`, `baseplate`, `island`, `post`, `rail`, `carriage`, `port` |
| `anim.py` | CSS motion vocabulary, packet routes, loop fade, HTML wrapper for capture |
| `render.sh` | `stills <dir>` (SVG to PNG) and `video <page.html> <out.mp4> [seconds]` |
| `examples/agents_across_clouds.py` | The scenes behind `assets/agents-across-clouds/` |

## Re-render an example

From the repo root:

```bash
out=scratch/agents-across-clouds
python3 .agents/skills/video-gen/isometric/examples/agents_across_clouds.py $out
.agents/skills/video-gen/isometric/render.sh stills $out
.agents/skills/video-gen/isometric/render.sh video $out/j-drafting-fast.html $out/j-drafting-fast-1080p.mp4 10
```

The example writes one SVG per entry in its `STILLS` dict plus the animated
`j-drafting-fast.html`. The stills render pixel-identical to the committed
assets. To check after a refactor:
`magick compare -metric AE assets/<slug>/<name>.png $out/<name>.png null:` should print `0`.

## Make a new diagram

1. Copy `examples/agents_across_clouds.py` to `examples/<slug>.py`.
2. Rewrite the scene function: place props, then cables, then the rail or hub.
3. Run it into `scratch/<slug>/`, render stills, `Read` the PNGs, adjust.
4. When a variant is picked, add the animated version, preview, final render.
5. Copy finals to `assets/<slug>/`.

New props that could recur go in `parts.py`; one-off geometry stays in the example.

## Drawing model

- **World coordinates.** x runs right-down along the long axis, y runs
  left-down toward the viewer, z is up. Units are arbitrary; a rack is about
  2.5 x 3 x 5. The visible faces are top (+z), front (+y), and side (+x).
- **Painter's order.** No depth buffer: later elements cover earlier ones. Draw
  back to front (low y before high y, low x before high x), and draw things
  that hang in front (cables, carriages) after what they hang over. A cable
  must land on a top face drawn before it. In the example, the sandbox cables
  land on the front-middle cube (`cubes[4]`) because landing on the back row
  left the cable drawn over the front cubes.
- **Faces.** `Scene.box()` returns a `Box`; `box.front(u, v)`, `box.side(u, v)`,
  and `box.top(u, v)` map face coordinates to world points. `sc.rect(face, ...)`
  and `sc.circle(face, ...)` draw details on a face; `sc.text_front()` and
  `sc.text_top()` lay text on one.
- **Fitting.** `sc.render((x, y, w, h))` scales the scene into a pixel region
  and returns the SVG group plus `to_screen(p3)`, used to anchor screen-space
  callouts to world points.
- **Strokes** use `vector-effect: non-scaling-stroke`, so lines stay 1.25px
  (0.8px for `hair`) whatever the scene scale.

Classes for fills: `top`, `front`, `side`, `deep` (recesses), `screen`, `led`,
`netfill`; strokes: `hair`, `net` (accent cable); text: `engrave`, `scr`
(screen text), `neteng` (accent label).

## Look

- **Themes** in `iso.THEMES`: `light` (warm paper, default), `dark`, `codex`
  (parchment and sepia), `blueprint` (Amika navy plus a drafting grid, added by
  `page()`). Keep `net` as the one saturated color.
- **Titles:** `title_cad` sets condensed caps into a dimension line;
  `title_codex` uses Cormorant Garamond italic with ruled flourishes. `hw` is
  half the rendered title width, tuned by eye: re-tune it when the copy or
  size changes, or the rules will overlap the text or float away from it.
- **Layout constants:** untitled scenes fit `(80, 120, 1440, 610)` with callout
  labels at y=790; titled scenes fit `(80, 178, 1440, 560)` with labels at 815.
- **Fonts** load from Google Fonts (Barlow Condensed, Cormorant Garamond,
  JetBrains Mono, Plus Jakarta Sans), so rendering needs network. The mono
  stack prefers a local JetBrainsMono Nerd Font if installed; it's the same
  face for ASCII.

## Animation

The scene is the same for stills and video. Groups carry classes that
`anim.MOTION_CSS` animates; stills simply don't include that CSS.

- **Choreography** lives in the example's `TIMELINE`: start times and
  `(start, step)` staggers in seconds. Each group gets its start as an inline
  `animation-delay` via `sc.group(cls, anim.delay(t))`.
- **Motions:** `a-plate` rise, `a-post` grow, `a-rail` drop on, `a-mod` drop in,
  `a-car` slide along the rail from `--dx/--dy`, `a-cable` extend down, `a-port`
  pop, `a-fade`, `a-co` (callouts). Grow and pop use
  `transform-box: fill-box` so they scale from the element's own edge.
- **LEDs** light at the `--led` variable set on their host group. Some blink,
  picked by `nth-of-type`, starting at `--blink-a` and `--blink-b`.
- **Terminal lines** take explicit delays through `laptop(line_delays=...)`.
- **Packets:** `anim.route_keyframes()` turns a list of world points into
  constant-speed `@keyframes`; `anim.packet()` loops a dot along it. Run one
  forward and one `reverse` per route for two-way traffic.
- **Loop:** `anim.fade_overlay()` fades the card in over the last 5% of the
  loop. Elements placed after it in the body (the title) stay visible
  throughout.

Preview with `FPS=4 SCALE=1` through capture.mjs and check frames before the
full render (commands in `../SKILL.md`).

## Gotchas

- A CSS class `font-size` beats an SVG `font-size` attribute. To resize text
  that has a class, use an inline `style`.
- Keep the build-up short. The user wanted machines on screen within a second;
  the current timeline lands hosts by ~1s and has packets flowing by ~2.5s.
- `render.sh` finds the repo from its own path, so run it from inside the repo
  checkout.
