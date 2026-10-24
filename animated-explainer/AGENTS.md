# Animated explainer: notes for AI agents

The repo-wide rules in [../AGENTS.md](../AGENTS.md) apply here too.

## Status

This is a prototype. There is no package, setup or tests yet. The folder holds
one hand-built page, [examples/night-train.html](examples/night-train.html),
with its article and the tool that cut its map. Use this approach only when
the user asks for an animated explainer. Template rendering stays the default
for presenting an article.

## The example page

- It is one self-contained file: inline CSS and JavaScript, no external
  fonts, scripts or images, nothing loaded from the network. Keep it that
  way.
- It has three parts:
  - **The script** (`<script type="application/json" id="explainer">`)
    holds every word and figure on screen.
  - **The map** (`id="europe"`) is the output of
    [tools/cut_map.py](tools/cut_map.py). Regenerate it with the tool, don't
    edit it by hand.
  - **The engine** (the last `<script>`) draws the scene kinds and runs the
    player.
- Content changes go in the script, not the engine. Words the page adds
  itself, such as "now" or "Source", go in the script's `labels`.
- Each scene is one page. The page shows at most `max_pages` scenes (default
  5), or `?pages=N` from the address, keeping the best `rank`s in story
  order. Give every scene a unique rank, with 1 for the page to keep if only
  one fits. A new scene doesn't make the default explainer longer unless it
  outranks one already in the top 5.
- Facts follow template rendering's rules. Every figure and quote must come
  from [examples/night-train.md](examples/night-train.md), and quotes must be
  word for word. A number the article only implies, such as a ratio, belongs
  in a beat's `math` with its working, and it must be right.
- Colour comes from roles (`train`, `plane`, `gold`, `warn`), written as
  `{role:text}` in captions and as the tokens on `:root` in CSS. Don't add
  raw colours.
- Keep the design this project's own. Don't name channels, creators or
  brands as the style it follows, in docs, code or pages. Don't copy their
  palettes, fonts, characters, music, logos or signature sequences.
- The screen stays dark in both themes, like a video frame. The page around
  it follows the reader's light or dark setting, or `data-theme` on the root
  element.
- There are two layouts: a 1600×900 viewBox, and a 900×1400 one for phones
  held upright. The CSS and the JavaScript use the same media query to pick
  one. Check both after a change.

## Checking a change

- Every step has an address: `night-train.html#step-12` opens step 12.
- When the reader prefers reduced motion, each step renders instantly, which
  makes screenshots easy. With headless Chrome:
  ```bash
  chrome --headless=new --force-prefers-reduced-motion --window-size=1440,900 \
    --virtual-time-budget=3000 --screenshot=step12.png "file:///…/night-train.html#step-12"
  ```
  Chrome won't make a window narrower than about 500 px. To see the phone
  layout, load the page in a 390×844 iframe.
- Also play every step with the animation running, go back and forward
  mid-animation, and watch the console for errors.

## Next: the pipeline

When asked to build it, follow "Adding an approach" in
[../AGENTS.md](../AGENTS.md). That means a package, a prompt and catalog for
the agent, a checker, a renderer that inlines the engine, tests, and a job in
[../.github/workflows/tests.yml](../.github/workflows/tests.yml). Start the
script schema from the example's script. [README.md](README.md) describes the
planned design.
