# CSS Animations Level 1 Plan

This checklist targets practical CSS Animations Level 1 parity. Checked items must have focused
tests and, where visual, a replayable widget-gallery example.

## L1.0 — Stabilize the existing foundation

- [ ] Sort keyframes by offset before playback.
- [ ] Merge duplicate offsets using declaration order and normal declaration precedence.
- [ ] Reject percentage selectors outside `0%..=100%`.
- [ ] Define behavior for an animation with zero or one usable keyframe without panicking.
- [ ] Resolve omitted `0%` and `100%` property values from the underlying computed style.
- [ ] Preserve the underlying value for properties absent from an intermediate keyframe.
- [ ] Add parser and runtime tests for `from`, `to`, percentages, multiple selectors, and duplicate
      offsets.

## L1.1 — CSS declarations and automatic playback

- [ ] Parse and store `animation-name` as a comma-separated list.
- [ ] Parse and store `animation-duration`.
- [ ] Parse and store `animation-delay`, including negative delays.
- [ ] Parse and store `animation-timing-function`.
- [ ] Parse and store `animation-iteration-count`, including fractional values and `infinite`.
- [ ] Parse and store `animation-direction` (`normal`, `reverse`, `alternate`,
      `alternate-reverse`).
- [ ] Parse and store `animation-fill-mode` (`none`, `forwards`, `backwards`, `both`).
- [ ] Parse and store `animation-play-state` (`running`, `paused`).
- [ ] Parse the `animation` shorthand without confusing its two time values.
- [ ] Coordinate list-valued longhands using CSS list repetition rules.
- [ ] Start, update, restart, and cancel CSS animations when matched computed declarations change.
- [ ] Preserve `Context::play_animation*` as the explicit Rust API.

## L1.2 — Timing and playback state

- [ ] Separate delay, active, and after phases.
- [ ] Implement positive and negative delays.
- [ ] Implement finite integer and fractional iteration counts.
- [ ] Implement infinite iteration.
- [ ] Implement all four directions and reverse easing correctly.
- [ ] Implement pause/resume without losing elapsed progress.
- [ ] Implement all four fill modes before and after the active interval.
- [ ] Handle zero duration and zero iterations deterministically.
- [ ] Make animation sampling testable with an injected timestamp rather than wall-clock sleeps.

## L1.3 — Easing

- [ ] Apply `animation-timing-function` as the default easing for every segment.
- [ ] Parse and apply per-keyframe `animation-timing-function`.
- [ ] Support `linear`, `ease`, `ease-in`, `ease-out`, and `ease-in-out`.
- [ ] Validate `cubic-bezier()` X coordinates and apply custom curves.
- [ ] Implement `steps()` including `step-start` and `step-end`.
- [ ] Test easing at segment boundaries and during reversed playback.

## L1.4 — Property coverage and invalidation

For every property, add the keyframe mapping, interpolator, playback registration, active-animation
query, tick, correct invalidation category, transition support where applicable, and tests.

- [x] Opacity.
- [x] Translate, rotate, scale, and transform.
- [x] Common colors, borders, corner radii, shadows, typography, size, spacing, and gaps.
- [ ] Audit every currently registered property for missing playback or tick wiring.
- [x] `filter: blur()`.
- [x] `backdrop-filter: blur()`.
- [ ] Define compatible filter-list interpolation and discrete fallback.
- [ ] Add a documented table of animatable, discrete, and unsupported properties.
- [ ] Ensure redraw-only properties never trigger layout and layout properties invalidate the
      narrowest correct subtree.

## L1.5 — Composition and lifecycle

- [ ] Define CSS animation precedence relative to inline values, matched rules, and transitions.
- [ ] Support multiple named animations on one entity when they affect different properties.
- [ ] Define deterministic replacement when animations target the same property; additive
      composition remains Level 2.
- [ ] Emit `animationstart`, `animationiteration`, `animationend`, and `animationcancel` events.
- [ ] Include animation name, elapsed time, and entity in lifecycle events.
- [ ] Cancel animations safely when an entity is removed or a named keyframe rule disappears.
- [ ] Respect reduced-motion environment preferences with an application override.

## L1.6 — Quality gate

- [ ] Unit-test every value parser and shorthand ambiguity.
- [ ] Unit-test the timing state machine without rendering.
- [ ] Add integration tests for selector changes starting and canceling animations.
- [ ] Add render regressions for transforms, rounded clipping, filters, and backdrop filters.
- [ ] Add all supported animation families to the widget gallery.
- [ ] Document remaining deliberate differences from CSS Animations Level 1.
- [ ] Run `cargo fmt`, workspace Clippy, tests, and the gallery on Linux, macOS, and Windows.
