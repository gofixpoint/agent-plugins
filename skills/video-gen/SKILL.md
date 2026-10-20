---
name: video-gen
description: Make marketing graphics and short looping videos (PNG stills, MP4 animations) for social posts, launches, and decks. Use when the user asks for a graphic, diagram, illustration, or animated video to go with a tweet or post, or wants to re-render an existing one. Routes to per-style sub-guides; today that is isometric technical diagrams.
argument-hint: "[what the graphic should show, or a post to illustrate]"
---

# Video gen

Graphics and short videos for posts. Each visual style is a sub-skill: a folder
here with a `GUIDE.md` and the code that renders it. Read the root of this file
for the shared workflow, then the guide for the style you need.

**Usage:** `/video-gen [what to show]`

## Sub-skills

| Style | Guide | What it makes | Example output |
| --- | --- | --- | --- |
| Isometric technical diagram | [`isometric/GUIDE.md`](isometric/GUIDE.md) | Line-art machines on a machined plate, network drawn in the accent color, drafting or blueprint titles. Stills plus a looping build-up video. | `assets/agents-across-clouds/` |

Other video tooling in the repo, not wrapped as sub-skills yet:
[Remotion](../../../video/remotion/AGENTS.md) (React to MP4, terminal and card
motifs), [Motion Canvas](../../../video/motion-canvas/AGENTS.md),
[Revideo](../../../video/revideo/AGENTS.md), and
[web capture](../../../video/capture/AGENTS.md) (record an animation from one of
our web apps).

To add a style: create `<style>/GUIDE.md` plus its code and an `examples/`
folder, then add a row above.

## Workflow

1. **Plan before drawing.** If the user shares a reference image, describe how
   you'll build it and which variants you'll try, and confirm before rendering.
   Borrow the reference's feel, not its signature elements: an early round here
   copied a reference's "Fig 1" corner captions and gantry layout too closely
   and had to be redone.
2. **Iterate in `scratch/<slug>/`** (gitignored). Render, `Read` every PNG, fix
   overlaps and clipped text, then show the user 3 to 5 variants side by side.
3. **Check facts on the graphic.** Labels are claims. Verify product details
   against `launches/`, `agentdocs/company.md`, or the amika repo docs before
   engraving them (we dropped "wireguard mesh" because nothing confirmed it).
   No third-party logos or brand marks; name providers in plain text.
4. **Animate last**, once a still is picked. Preview at low frame rate before
   the full render (see below).
5. **Ship finals to `assets/<slug>/`**, which `.gitattributes` routes to Git
   LFS. Every shipped asset needs a generator under `<style>/examples/<slug>.py`
   that reproduces it, so it can be re-rendered or tweaked later.

On-screen copy follows [`agentdocs/style.md`](../../../agentdocs/style.md): no
em-dashes. Brand colors and fonts come from
[`slides/design-system.md`](../slides/design-system.md).

## Shared video pipeline

Animations are HTML pages driven only by CSS animations.
[`video/capture/capture.mjs`](../../../video/capture/capture.mjs) fakes the page
clock and steps every CSS animation by hand, so frames are exact no matter how
slow screenshots are. SMIL, JS timers, and `requestAnimationFrame` loops won't
be stepped.

- **Browser:** pass `CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`.
  Playwright's bundled Chromium failed to launch on this machine.
- **Preview first:** `FPS=4 SCALE=1 SECONDS=<n> node video/capture/capture.mjs <file-url> <out.mp4>`
  takes seconds. Pull frames with `ffmpeg -ss <t> -i in.mp4 -frames:v 1 f.png`
  and tile them with ffmpeg's `xstack` filter (ImageMagick `montage` needs
  Ghostscript, which isn't installed).
- **Final:** capture at `SCALE=2 FPS=60` (4K), then downscale to 1080p with
  lanczos. Hairlines stay crisper than capturing at 1080p. A 10s loop takes
  about 5 minutes and lands near 1MB, well inside X's limits. Run it in the
  background.
- **Loops:** fade everything except persistent elements (titles) into the card
  color over the last 5% so the restart is clean.
- **Other formats:** animated WebP and freeze frames are covered in
  `video/capture/AGENTS.md`.
