# Vizia animation / Widget Gallery gotchas

These notes capture concrete pitfalls encountered while implementing and documenting CSS animations in
this fork. They are intentionally practical and repository-specific so they can be reused in future
agent/skill instructions.

## Classes are not whitespace-split

`StyleModifiers::class(name: &str)` adds exactly one class token. Passing several names in one string
does **not** behave like HTML `class="a b"`.

```rust
// Wrong: this becomes one class named "card animated".
Label::new(cx, "Demo").class("card animated");

// Correct.
Label::new(cx, "Demo").class("card").class("animated");
```

If a selector appears correct but only some demos style/animate, check this first.

## Vizia CSS is CSS-like, not browser CSS

Do not assume arbitrary browser properties or syntax exist. Prefer properties that are present in
`vizia_style::Property` / the value modules and verify them with a runtime stylesheet smoke test.
For spacing in Widget Gallery code, the normal Vizia layout tools (`gap`, padding, explicit sizing)
are safer than assuming browser margin behavior.

A useful regression test is:

```rust
let mut cx = Context::default();
cx.add_stylesheet(include_style!("resources/themes/animation.css"))?;
```

This catches syntax/property mistakes that a Rust-only compile cannot.

## Prefer class-only selectors for demo-specific styling

Widget Gallery examples are composed from Rust views and wrappers. For demo-only CSS, prefer a stable
class selector such as `.animation-doc-surface-target` over unnecessarily type-qualified selectors
such as `label.animation-doc-surface-target` or `vstack.animation-doc-backdrop-glass`.

A type-qualified selector can silently stop matching if a view wrapper emits a different semantic
element name. That can make configured width, padding, transparency, or animation declarations appear
to be ignored even though the class itself is present.

## CSS animations must use the existing property stores

Animation is tightly coupled to `AnimatableSet` / `AnimatableVarSet`. Do not build a parallel
"computed animation value" layer for CSS. Start/update/control CSS animation occurrences through the
same stores used by normal styles, transitions, and Rust animations.

This also means every newly supported property needs all of the following wired consistently:

- keyframe registration / storage,
- CSS occurrence playback and updates,
- interpolation/composition semantics,
- the correct invalidation path (redraw, retransform, reclip, reflow, or relayout).

## Compatible transform functions need real interpolation

Do not implement `Transform::interpolate` as a blanket `end.clone()`. Compatible transform functions
(`translate`, `translateX/Y`, `scale`, `rotate`, `skew`, and matrix pairs) need component-wise
interpolation. Only incompatible function pairs should fall back to a discrete switch.

A transform demo that is already rotated but never visibly travels is a strong signal to inspect the
interpolator rather than only the CSS parser or frame scheduler.

## Invalidation category matters for performance

A visually small animation can be expensive if it is routed through layout or text reconstruction.
Examples from this work:

- `translate` / `rotate` / `scale` should use retransform, not relayout;
- color/opacity/filter paint changes should redraw only;
- font-size / letter-spacing / line-height require text reconstruction;
- width/height/padding/gap and constraints affect layout.

When adding an animated property, treat its invalidation category as part of the feature, not a later
optimization.

## Do not relayout stepped/paused layout animations every frame

Animation clocks may need to keep advancing even while a stepped or paused animation samples the same
visible value. For layout-affecting `AnimatableVarSet`s, use change-aware ticking (`tick_changed` in
this branch) so the frame loop stays alive without requesting redundant layout work.

## Progress timelines should not fan out when nothing changed

Document-time animations (`animation-timeline: auto`) do not need timeline progress propagated into
every property store every frame. Likewise, scroll/view progress should only propagate when the
resolved timeline kind/progress changed.

Keep the timeline source sampling sparse and avoid a full-tree scan or all-store fan-out on every
frame.

## Filters/backdrop filters need sparse draw tracking

Do not scan the entire layout tree every draw just to discover filter/backdrop-filter entities. Keep a
sparse set of entities that can require filter-aware dirty-bound work and remove stale entries when
entities disappear or no longer have those values.

This matters a lot once a filter animation keeps frames flowing continuously.

## A backdrop-filter demo needs visible content behind transparent glass

A backdrop filter is difficult to verify over a flat or opaque surface. Use moving, high-contrast
content behind a translucent overlay. The overlay itself must remain transparent enough that the
backdrop is visible; a misread 8-digit hex color can accidentally turn the glass into an opaque panel
and make a working blur look broken.

## `auto` size animation is inherently expensive

Animating width/height keyframes that contain `auto` may require a real measurement/layout pass to
resolve the target geometry. Do not use `auto` size animations as a baseline performance demo, and do
not extrapolate transform/paint performance from them.

## A documentation page should not mount every live animation

For an interactive reference, mount only the selected example. A long page with dozens of continuous
animations is a stress test, not representative documentation, and it makes normal scrolling look
worse than the engine actually is.

Similarly, avoid page-wide periodic timers just to update demo readouts/sliders. Let the animation
system own frame scheduling; update UI readouts on interaction unless a continuously-following control
is the subject of that specific example.

## Nested scroll views change both UX and performance

Widget Gallery already wraps normal view pages in its main `ScrollView`. Adding another large
`ScrollView` inside a demo creates a separate scroll gesture/viewport. Use nested scroll views only
when the demo specifically needs a scroll timeline/view timeline or an independently scrollable
reference rail.

Give nested scroll views an explicit bounded height; otherwise their content can expand the outer page
and defeat the point of the inner scrolling region. A long reference/navigation column should therefore
be bounded and independently scrollable instead of determining the height of the entire page.

## Fixed heights are safest on the actual viewport, not whole sections

Large fixed-height section/card wrappers caused overlapping headings and demos when text wrapped or
window width changed. Let document sections use content height. Reserve fixed heights for actual demo
canvases/scroll viewports where a stable coordinate system is required.

## Keep source and result panes structurally symmetrical

For MDN-style examples, give the code pane and result pane the same explicit body height. Put headers
in matching header rows and place the CSS text in a dedicated body aligned `TopLeft`.

A single label directly inside a stretching `VStack` can end up visually hugging the bottom or being
laid out unexpectedly, making the pane look empty even though the text exists.

## The code shown in a live reference must actually drive the preview

Do not display one `@keyframes` block while reusing an unrelated preview class. The source pane should
include the declaration that applies the shown keyframes (`animation: ...`) and the mounted result
should use the same keyframe shape/timing. Otherwise a static or mismatched demo looks like an engine
bug even when the animation system is working.

For grouped properties (for example border sides or background position/size/repeat), use explicit
variants rather than one ambiguous example. The selected variant should update both the source snippet
and the mounted preview.

## Text/border demos need a real surface

Animating `border-color`, `font-size`, `letter-spacing`, outline, shadow, etc. on a label sized only to
its text produces cramped, hard-to-read demos. Use a stable min-size plus generous padding so the
animated property has room to be perceived.

Also demonstrate properties on semantically relevant views when possible. For example, `fill` is much
clearer on an `Svg` than on a text label.

## Scroll/view timelines are not autoplay animations

A scroll or view timeline uses external progress as its clock. If scrolling stops, the animation must
stop at that sampled progress. Do not add a wall-clock fallback just because a demo appears "paused".

Keep document-time autoplay examples separate from scroll/view progress examples in UI and wording.

## Reduced motion changes CSS animation timing

The CSS animation runtime respects the environment's reduced-motion preference/override. When a demo
appears to skip motion entirely, check the effective reduced-motion setting before assuming the parser
or keyframes failed.

## Large gallery tests should distinguish engine cost from debug-build cost

Widget Gallery + Skia can be noticeably slower in debug builds. Always compare suspicious animation
or scrolling behavior with:

```bash
cargo run --release -p widget_gallery
```

A release build is not a substitute for profiling, but it avoids diagnosing debug-codegen overhead as
an animation-engine regression.
