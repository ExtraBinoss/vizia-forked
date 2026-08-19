# Animation Gallery and Verification

The Widget Gallery owns a top-level **Animation** page. The showcase uses the normal page scroll and
the same native buttons, sliders, popovers, typography, spacing and theme variables as the rest of
the application. Demo-specific CSS is limited to the animated surfaces themselves.

The page deliberately distinguishes two timeline models:

- The document timeline autoplays and exposes a continuously-following scrubber.
- Scroll/view timelines are progress timelines: scrolling is the clock, so stopping the scroll must
  freeze the effect without wall-clock drift.

## Level 2 showcase

- [x] `replace` vs `add` side-by-side using two effects on the same `translate` property.
- [x] `accumulate` using two rotation effects plus a separate scale effect.
- [x] Document-timeline autoplay with live progress, pause/resume, reverse, seek and playback-rate controls.
- [x] Named scroll timeline using a local `ScrollView` and an explicit live percentage readout.
- [x] View-progress timeline with a subject entering and leaving a local viewport.
- [x] Native Vizia `Popover` opened by a native `Button`, with a short CSS blur/opacity reveal.
- [x] Geometric vector-path morph between Heart and Star shapes, with Tabler Heart/Star controls,
      manual scrub and an alternating play sequence.
- [x] Lightweight staggered text throbber as a practical small animation pattern.
- [x] Page-level play/pause controls for document-time examples.

The named scroll demo is registered from Rust with `ScrollView::timeline_name("--gallery-scroll")`
and consumed by CSS through `animation-timeline: --gallery-scroll`. The view demo uses
`animation-timeline: view(block)`.

## Level 1 regression sampler

All ten Level 1 witnesses remain available, but only **one witness is mounted at a time**. Previous
and Next buttons switch the active witness. This preserves the full regression matrix without making
the normal gallery scroll pay for every continuous animation simultaneously.

- [x] Entrance: opacity + translate + scale.
- [x] Style interpolation: background/text color + corner radius + border + shadow.
- [x] Layout: width + padding + gap with visible neighboring content.
- [x] Multi-keyframe transform motion.
- [x] Continuous easing and visibly discrete `steps()` motion.
- [x] Delay and negative delay.
- [x] Infinite iteration and alternate / alternate-reverse direction.
- [x] Fill mode and play-state behavior.
- [x] Paused state shown beside a running copy of the same animation.
- [x] Filter blur interpolation.
- [x] Backdrop-filter over moving colored content.
- [x] Multiple named animations on one entity.

## Interaction and visual rules

1. Do not add `LIVE` badges or debug-looking guide/axis bars to the showcase.
2. Avoid card-inside-card layouts. Sections are flat; only actual animation viewports receive a border/background.
3. Native controls keep their normal Widget Gallery styling instead of being restyled in `animation.css`.
4. Progress-timeline examples must clearly explain that they are scrubbed by scroll, not autoplayed.
5. Runtime controls operate on the same CSS animation occurrence and do not call
   `Context::play_animation*` to fake CSS playback.
6. The document-timeline scrubber must track current progress continuously while playback is running.
7. Keep fixed heights limited to the actual demonstration viewport; section containers use content height.
8. Keep the Animation page searchable and present in the all-items overview.

## Acceptance

- No headings, labels or animation surfaces overlap at common desktop widths.
- The page remains visually consistent with the rest of Widget Gallery in light and dark themes.
- `replace` and `add` visibly produce different motion.
- Document-timeline playback advances without interaction and its scrubber follows continuously.
- Named scroll/view timelines move only with their source and freeze when scrolling stops.
- Runtime pause/resume/reverse/seek/rate controls preserve the stable occurrence ID.
- The native Popover performs a visible blur reveal without custom button styling.
- Heart/Star morph visibly interpolates geometry rather than cross-fading two SVG images.
- Only one Level 1 witness is mounted at once.
- Resizing during playback does not panic or corrupt layout.
- The source compiles on supported Widget Gallery backends and `animation.css` passes the runtime stylesheet smoke test.
