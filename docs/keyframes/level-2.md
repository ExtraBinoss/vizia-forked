# CSS Animations Level 2 Plan

Start this work only after the Level 1 timing model and lifecycle are stable.

## L2.1 — Effect stacks and composition

- [ ] Represent multiple simultaneous effects per entity and property.
- [ ] Implement stable animation composite order.
- [ ] Parse `animation-composition`.
- [ ] Implement `replace`, `add`, and `accumulate` with property-specific compositing.
- [ ] Define interaction between CSS transitions, CSS animations, and Rust-started animations.
- [ ] Add transform, numeric, color, and filter composition tests.

## L2.2 — Timelines

- [ ] Separate animation effects from their timelines.
- [ ] Introduce a monotonic document timeline abstraction.
- [ ] Parse `animation-timeline` without tying core animation code to a window backend.
- [ ] Implement named timelines.
- [ ] Add scroll-progress timelines.
- [ ] Add view-progress timelines.
- [ ] Define timeline behavior for headless and deterministic testing environments.

## L2.3 — Runtime control

- [ ] Provide inspectable current time, playback rate, pending state, and finished state.
- [ ] Support seek, reverse, finish, cancel, pause, and resume operations.
- [ ] Define behavior when keyframes or computed styles change during playback.
- [ ] Expose completion in an idiomatic Rust API without requiring a browser-like DOM facade.

## L2.4 — Advanced authoring and testing

- [ ] Support per-keyframe `animation-composition`.
- [ ] Test effect ordering across ancestors, siblings, and pseudo-elements supported by Vizia.
- [ ] Add interactive composition and scroll-timeline examples to the widget gallery.
- [ ] Document deliberate omissions from CSS Animations Level 2 and Web Animations.

