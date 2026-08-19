# CSS Animations Level 2 Plan

This work builds directly on the Level 1 CSS animation runtime. It must stay integrated with Vizia's
existing style-property storage (`AnimatableSet` / `AnimatableVarSet`) rather than introducing a
parallel animation engine.

The target is practical Level 2 behavior inspired by CSS Animations Level 2, Web Animations, and
Scroll-driven Animations where those models naturally fit Vizia. Deliberate differences must be
documented explicitly.

## L2.0 — Architecture and invariants

- [ ] Keep Level 1 behavior source-compatible and preserve `Context::play_animation*`.
- [ ] Separate an animation effect (keyframes/composition) from its timeline/progress source.
- [ ] Give every running effect a stable runtime identity and stable composite order.
- [ ] Ensure all effect application still resolves through Vizia's existing style-property stores.
- [ ] Add deterministic/headless hooks so every timeline and runtime-control path is testable without sleeps.
- [ ] Document precedence between inline style, matched style, transitions, CSS animations, and Rust-started animations.

## L2.1 — Effect stacks and composition

- [ ] Represent multiple simultaneous effects per entity and property.
- [ ] Implement stable animation composite order independent of storage iteration order.
- [ ] Parse `animation-composition` as a comma-separated list using CSS list repetition rules.
- [ ] Support `replace`, `add`, and `accumulate`.
- [ ] Implement property-specific composition for transforms first, then numeric/length-like values.
- [ ] Define color composition behavior and reject/replace unsupported additive cases deterministically.
- [ ] Define filter-list composition behavior and deterministic fallback for incompatible lists.
- [ ] Support per-keyframe `animation-composition` where representable by Vizia's style model.
- [ ] Define interaction between CSS transitions, CSS animations, and Rust-started animations.
- [ ] Add transform, numeric, color, filter, and mixed-effect-order tests.

Acceptance examples:

```css
.card {
    animation: move 1600ms infinite alternate, spin 900ms infinite linear;
    animation-composition: add, add;
}
```

The card must translate and rotate simultaneously instead of the later transform effect replacing the
earlier one.

## L2.2 — Timeline model

- [ ] Introduce an explicit `AnimationTimeline` abstraction separate from animation effects.
- [ ] Keep the document timeline monotonic and injectable for tests.
- [ ] Parse `animation-timeline` as a CSS list without coupling parser code to a window backend.
- [ ] Support `auto`/document timeline behavior.
- [ ] Implement named timeline lookup with stable lifecycle semantics.
- [ ] Implement scroll-progress timelines.
- [ ] Implement view-progress timelines.
- [ ] Clamp and normalize timeline progress deterministically for zero-size/degenerate ranges.
- [ ] Define timeline behavior when the source entity disappears.
- [ ] Define timeline behavior in headless environments.

Acceptance examples:

```css
.reveal {
    animation: reveal linear both;
    animation-timeline: gallery-scroll;
}
```

Scrolling the source container must advance the keyframe effect without depending on wall-clock time.

## L2.3 — Runtime control

- [ ] Introduce a public runtime animation handle/id that is independent of the declared `@keyframes` id.
- [ ] Expose inspectable current time/progress, playback rate, pending state, running/paused state, and finished state.
- [ ] Support `seek`, `set_playback_rate`, `reverse`, `finish`, `cancel`, `pause`, and `resume`.
- [ ] Preserve current progress when playback rate or direction changes.
- [ ] Define behavior when keyframes change during playback.
- [ ] Define behavior when computed animation declarations change during playback.
- [ ] Keep lifecycle events coherent under seek/reverse/finish/cancel.
- [ ] Expose completion in an idiomatic Rust API without requiring a browser-like DOM facade.
- [ ] Add deterministic runtime-control tests using an injected timeline timestamp.

## L2.4 — Invalidation and performance

- [ ] Composition must not broaden invalidation beyond the final composed property's category.
- [ ] Additive transform effects must use the transform/retransform path, never layout.
- [ ] Scroll/view timelines must invalidate only animations subscribed to the changed timeline source.
- [ ] Off-screen/virtualized gallery demos must not keep unnecessary effects mounted.
- [ ] Avoid full-tree scans per animation frame; timeline/source tracking must be sparse.
- [ ] Add regression tests for paused/stepped/composed values not causing redundant layout work.

## L2.5 — Widget Gallery demos

- [ ] Add a dedicated "Level 2" section to the Animation gallery.
- [ ] Add an always-running transform composition demo (`translate + rotate + scale`).
- [ ] Add a `replace` vs `add` side-by-side comparison.
- [ ] Add an `accumulate` multi-iteration demo where visually meaningful.
- [ ] Add a scroll-progress timeline demo with an obvious progress indicator.
- [ ] Add a view-progress timeline demo driven by entering/leaving a viewport.
- [ ] Add runtime controls: pause/resume, reverse, seek slider, finish, cancel, playback-rate control.
- [ ] Display current progress/time/state so runtime behavior can be inspected manually.
- [ ] Keep demos visually rich and virtualized so the gallery remains smooth while animations run continuously.

## L2.6 — Quality gate

- [ ] Unit-test every new parser value and shorthand/list interaction.
- [ ] Unit-test composition order and property-specific composition.
- [ ] Unit-test document, named, scroll, and view timeline sampling.
- [ ] Unit-test runtime control without rendering or wall-clock sleeps.
- [ ] Add integration tests for style changes, timeline-source removal, and entity removal.
- [ ] Add render/manual regression coverage for composed transforms, filters, clipping, and scroll/view timelines.
- [ ] Document supported additive/accumulative property families and deliberate fallbacks.
- [ ] Run `cargo fmt`, workspace Clippy, focused tests, core tests, gallery checks, and official CI on Linux/macOS/Windows.

## Deliberate scope boundary

Level 2 should not turn Vizia into a browser DOM/Web Animations clone. The implementation should adopt
the useful CSS/Web Animations semantics while exposing them through Vizia-native style storage,
entities, signals, scroll views, and Rust APIs.
