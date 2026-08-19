# CSS Animations Level 2 — Vizia implementation

This work builds directly on the Level 1 CSS animation runtime and stays integrated with Vizia's
existing style-property storage (`AnimatableSet` / `AnimatableVarSet`). It does **not** introduce a
parallel browser-style animation engine.

The Vizia Level 2 scope combines the parts of CSS Animations Level 2, Web Animations, and
Scroll-driven Animations that fit Vizia's retained entity/style architecture. It is intentionally a
Vizia-native implementation rather than a claim of complete browser/DOM conformance.

## L2.0 — Architecture and invariants

- [x] Keep Level 1 behavior source-compatible and preserve `Context::play_animation*`.
- [x] Separate animation effects/keyframes from their timeline/progress source.
- [x] Give each CSS animation occurrence a stable runtime ID and stable composite order.
- [x] Resolve effect application through the existing property stores.
- [x] Keep sampling deterministic: core timing/timeline helpers accept explicit timestamps/progress and are unit-testable without sleeps.
- [x] Keep CSS animation output integrated with the existing matched/inline/transition/Rust animation storage path rather than a second style layer.

## L2.1 — Effect stacks and composition

- [x] Represent multiple simultaneous CSS effects per entity/property.
- [x] Sort the effect stack by CSS animation list order plus stable occurrence ID, independent of storage iteration order.
- [x] Parse `animation-composition` as a comma-separated list with CSS list repetition.
- [x] Support `replace`, `add`, and `accumulate`.
- [x] Compose individual `translate`, `rotate`, `scale`, transform lists, numeric/length-like values, opacity, colors, and filters inside the property stores.
- [x] Use deterministic replacement/fallback when a value family cannot be safely added or accumulated.
- [x] Compose compatible transform lists element-by-element for `accumulate`; fall back deterministically for incompatible lists.
- [x] Concatenate filter effects for `add` and accumulate compatible blur/filter lists.
- [x] Test stable additive transform behavior and property-specific composition.

Example:

```css
.card {
    animation: move-x 1600ms infinite alternate,
               move-y 900ms infinite alternate;
    animation-composition: add, add;
}
```

Both effects remain present in the same property's effect stack, so the final value is composed
instead of whichever store entry happened to be visited last.

## L2.2 — Timeline model

- [x] Add `AnimationTimeline` as a value separate from the keyframe effect.
- [x] Parse comma-separated `animation-timeline` values independently of any window backend.
- [x] Support `auto`, `none`, named dashed identifiers, `scroll(...)`, and `view(...)`.
- [x] Support block/inline/x/y axes and root/nearest/self scroll-source selection.
- [x] Add normalized `ScrollTimelineSource` sampling.
- [x] Add named scroll sources through `ScrollView::timeline_name(...)`.
- [x] Add view-progress sampling using subject/viewport geometry.
- [x] Clamp degenerate scroll/view ranges deterministically.
- [x] Treat a missing/dead timeline source as unresolved progress rather than falling back to wall-clock time.
- [x] Keep timeline tests headless through pure progress helpers and explicit samples.
- [x] Avoid layout-tree scans for timeline sampling; active CSS occurrences and registered scroll sources form the sparse working set.

Example:

```css
.reveal {
    animation: reveal 1s linear both;
    animation-timeline: --gallery-scroll;
}
```

```rust
ScrollView::new(cx, content).timeline_name("--gallery-scroll");
```

Scrolling the source changes animation progress directly; wall-clock time does not advance the
effect while the scroll position is unchanged.

## L2.3 — Runtime control

- [x] Add public `CssAnimationId`, independent of the declared `@keyframes` `Animation` ID.
- [x] Add `CssAnimationSnapshot` with name/entity/current local time/progress/playback rate/state/timeline kind.
- [x] Expose pending/running/paused/finished states.
- [x] Support pause, resume, seek, playback-rate changes, reverse, finish, and cancel from both `Context` and `EventContext`.
- [x] Preserve local time when playback rate/direction changes by re-anchoring the same clock.
- [x] Keep runtime commands synchronized across the named occurrence and every property store participating in that occurrence.
- [x] Allow seek/resume/reverse to revive a filled effect that had already reached its end instead of leaving the store stuck at `t == 1`.
- [x] Keep runtime IDs stable while timing/composition/timeline declarations update for the same CSS occurrence.
- [x] Emit cancel through the existing CSS animation lifecycle-event path.
- [x] Keep lifecycle sampling consistent with reversed progress timelines.
- [x] Expose completion through `CssAnimationSnapshot::state == CssAnimationPlaybackState::Finished` rather than introducing a DOM promise/facade.
- [x] Add deterministic clock/runtime tests using explicit `Instant` values.

## L2.4 — Invalidation and performance

- [x] Composition changes only the invalidation category of the final property value.
- [x] Additive transform effects use the retransform path, not layout.
- [x] Progress timelines sample active CSS occurrences and registered sources; no full-tree timeline scan is performed per frame.
- [x] Preserve the Level 1 sparse filter/backdrop-filter draw tracking instead of restoring an O(tree-size) draw scan.
- [x] Preserve change-aware layout ticking so stepped/paused layout animations do not relayout while their sampled value is unchanged.
- [x] Keep timeline source state normalized in `ScrollView` so sampling is O(1) per subscribed occurrence.

The Widget Gallery keeps only the small Level 2 showcase set plus one selected Level 1 regression
witness mounted at a time. Scroll/view examples keep local viewports because the viewport is the
actual timeline source; the rest of the page uses normal content height and the gallery's outer
scroll. This avoids turning the visual regression page into a permanent many-animation stress test.

## L2.5 — Widget Gallery demos

- [x] Use a flat, full-width Level 2 showcase with the same native Button, Slider, Popover, typography, spacing, and theme variables as the rest of Widget Gallery.
- [x] Add side-by-side `replace` vs `add` composition on the same `translate` property.
- [x] Add an `accumulate` rotation demo plus an independently composed scale effect.
- [x] Add a document-timeline demo that autoplays and exposes a continuously-following scrubber.
- [x] Add clear play/pause/reverse/playback-rate/restart controls for the document-timeline occurrence; `finish` and `cancel` remain covered by the public runtime API and deterministic tests rather than crowding the primary showcase.
- [x] Add a named scroll-progress timeline whose local scroll position is explicitly presented as the clock.
- [x] Add a `view(block)` demo driven by entering/leaving a local viewport.
- [x] Hide local timeline scrollbars and remove decorative guide/axis bars that could be mistaken for animation UI.
- [x] Add a native Button -> Popover interaction with a short CSS blur/opacity reveal.
- [x] Add a geometric Heart <-> Star vector-path morph with Tabler Heart/Star target buttons, a manual scrubber, and a play sequence.
- [x] Add a lightweight staggered text throbber as a practical small animation example.
- [x] Keep all ten Level 1 visual regression witnesses but mount only one selected witness at a time with Previous/Next controls.
- [x] Remove `LIVE` badges, card-inside-card nesting, fixed-height section containers, and the old nested 600px `VirtualList`.

## L2.6 — Quality gate

- [x] Parser tests cover `animation-composition` and timeline values/lists.
- [x] Core tests cover composition ordering/property behavior, progress timelines, and runtime clock control.
- [x] Runtime regression tests cover stable occurrence identity and re-sampling after a filled effect finishes.
- [x] The Widget Gallery stylesheet has a runtime `Context::add_stylesheet(...)` smoke test.
- [x] The gallery source is compiled by the official all-target/backend build matrix.
- [x] Supported additive/accumulative families and deterministic fallbacks are encoded by the property-specific `Compositor` implementations.
- [x] Formatting, Clippy, stylesheet smoke testing, Audit, and multi-platform build validation are part of the final validation pass.

## Deliberate scope boundaries

The following are intentionally **not** claimed as part of this Vizia Level 2 implementation:

- A browser DOM or a full Web Animations `Animation` object model.
- The CSS per-keyframe `animation-composition` descriptor. Vizia currently applies composition per
  CSS animation occurrence using the `animation-composition` list.
- The full CSS named-timeline declaration family (`scroll-timeline-*`, `view-timeline-*`, timeline
  scopes/ranges). Named scroll sources are exposed through the Vizia-native
  `ScrollView::timeline_name(...)` API, while `animation-timeline` remains CSS.
- Playback-rate magnitude changing an externally supplied scroll/view progress source. A negative
  rate reverses progress; the source itself remains controlled by scrolling/visibility.
- Browser-defined SVG path-data interpolation. The Widget Gallery Heart/Star demo is a Vizia-native
  geometric vector morph used to demonstrate interactive animation UI; it is not presented as a CSS
  `d`-property implementation.

Those boundaries keep the implementation aligned with Vizia's entity, style-store, signal, and
`ScrollView` architecture while leaving room for future standards work without replacing this
foundation.
