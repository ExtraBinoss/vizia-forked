# CSS Animations — Widget Gallery Reference

The Widget Gallery **Animation** page is an interactive CSS-animation reference, not a stress-test or a standards-level showcase.

Its layout intentionally mirrors documentation sites such as MDN:

- a secondary, bounded animation-reference navigation column on the left;
- the selected property/concept documented in the main pane;
- CSS source on the left side of the example;
- the live Vizia result on the right side;
- native Widget Gallery buttons, button groups, sliders, popovers, typography and theme tokens.

## Performance rule

Only the selected documentation entry mounts a live preview. Inactive examples do not keep CSS animation occurrences, filters, layout animations, timers or progress timelines running in the background.

Entries with several meaningful sub-properties use one selected variant at a time. Switching a variant replaces both the CSS snippet and live preview, so hidden variants do not continue animating.

The page must not install a page-wide periodic timer merely to refresh readouts. Runtime-control readouts update when the user interacts. Document-time animations are driven by the normal animation system; scroll/view animations are driven only by their progress source.

## Animation property reference

The navigation documents every CSS animation property currently implemented by Vizia:

- `animation`
- `animation-name`
- `animation-duration`
- `animation-delay`
- `animation-timing-function`
- `steps()`, `step-start`, `step-end`
- `animation-iteration-count`
- `animation-direction`
- `animation-fill-mode`
- `animation-play-state`
- `animation-composition`
- `animation-timeline`

It also documents `@keyframes`, percentage offsets, multiple animation lists, document timelines, named scroll timelines, `scroll(...)`, and `view(...)`.

## Animated property-store reference

The reference mirrors the property families wired by `Style::play_css_on_stores` / `update_css_on_stores` rather than maintaining a hand-wavy demo list.

The page covers:

- `display`
- `opacity`
- `clip-path`
- `filter`
- `backdrop-filter`
- `transform`
- `transform-origin`
- `translate`
- `rotate`
- `scale`
- border top/right/bottom/left widths
- border top/right/bottom/left colors
- per-corner radius and smoothing
- `outline-width`, `outline-color`, `outline-offset`
- `background-color`
- background image / position / repeat / size stores
- `shadow`
- `color`
- `font-size`
- `letter-spacing`
- `line-height`
- `caret-color`
- `selection-color`
- `text-decoration-color`
- `fill`
- `left`, `right`, `top`, `bottom`
- padding top/right/bottom/left
- horizontal / vertical gap
- width / height
- min/max width / height
- min/max horizontal / vertical gap constraints
- typed custom color, length, font-size, letter-spacing, line-height, units, opacity and shadow stores

Grouped families expose native Widget Gallery variant controls. In particular:

- `transform`: Translate / Rotate / Combined;
- background geometry: Position / Size / Repeat;
- border width: Top / Right / Bottom / Left / All;
- border color: Top / Right / Bottom / Left / All;
- corner radius: All / Top left / Top right / Bottom left / Bottom right.

The selected variant changes both source and result. Text, border, radius, background and shadow examples use large stable surfaces with generous padding so the animated property is visually legible instead of being constrained to glyph bounds.

## Runtime and UI-pattern examples

The reference also includes focused, opt-in examples for:

- stable CSS animation occurrence inspection;
- pause / resume;
- seek;
- reverse;
- playback-rate changes;
- copying the currently selected CSS/variant to the clipboard;
- a native `Button` opening a native `Popover` with a CSS blur reveal;
- a lightweight staggered text throbber.

The backdrop-filter preview uses moving high-contrast content behind translucent glass so the difference between `filter` and `backdrop-filter` is observable.

## Acceptance

- No “Level 1”, “Level 2”, or `LIVE` presentation badges appear in the Widget Gallery Animation page.
- The first screen reads like documentation, not like nested demo cards.
- The selected entry shows CSS and its live result side-by-side when space permits.
- Grouped property variants use native Widget Gallery controls and update both snippet and result.
- Only one live documentation preview and one selected variant are mounted at a time.
- The page does not add a periodic UI refresh timer on top of the animation frame loop.
- Text/border/radius previews have enough fixed visual surface to make interpolation obvious.
- Backdrop-filter is demonstrated over moving content with translucent glass.
- Normal document-time animation remains smooth while scrolling the gallery.
- Named scroll and view timelines stop when their source stops changing.
- The stylesheet parses through `Context::add_stylesheet(...)` in the gallery smoke test.
- The source passes formatting, Clippy and the supported backend/platform build matrix.
