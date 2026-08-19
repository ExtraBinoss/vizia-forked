# Animation Gallery and Verification

The Widget Gallery owns a top-level **Animation** page. It is a full-size visual stress-test: the
normal page scroll owns the showcase and there is no nested 600px `VirtualList` around the demos.
Running Level 1 examples intentionally loop continuously, while Level 2 progress-timeline examples
move only when their scroll/view source changes.

## Level 2 showcase

The Level 2 sections appear first and are intentionally large enough to make the new behavior
obvious without inspecting source code.

- [x] `replace` vs `add` side-by-side using two animations on the same `translate` property.
- [x] `accumulate` witness using two rotation effects plus a separate scale effect.
- [x] Named scroll timeline with a large local `ScrollView` and an independent progress marker.
- [x] View-progress timeline with a subject entering and leaving a large viewport.
- [x] Runtime-control lab with stable occurrence ID and visible time/progress/state/rate readout.
- [x] Pause, resume, reverse, seek, finish, cancel, 0.5x/1x/2x controls.
- [x] Large stages and high-contrast geometry rather than thumbnail-sized cards.

The named scroll demo is registered from Rust with `ScrollView::timeline_name("--l2-gallery-scroll")`
and consumed by CSS through `animation-timeline: --l2-gallery-scroll`. The view demo uses
`animation-timeline: view(block)`.

## Level 1 regression matrix

The original Level 1 witnesses remain directly in the page below the Level 2 sections.

- [x] Entrance: opacity + translate + scale.
- [x] Style interpolation: background/text color + corner radius + border + shadow.
- [x] Layout: width + padding + gap with visible neighboring content.
- [x] Multi-keyframe motion: at least three offsets.
- [x] Timing functions: continuous easing and visibly discrete `steps()` motion.
- [x] Delay and negative delay.
- [x] Infinite iteration and alternate / alternate-reverse direction.
- [x] Fill mode declarations in the shorthand and play-state examples.
- [x] Paused state shown beside the same animation running continuously.
- [x] Filter blur interpolation.
- [x] Rounded backdrop-filter animation over moving high-contrast content.
- [x] Multiple named animations on one entity.

## Interaction rules

1. Level 1 running examples loop continuously with short periods so movement is always visible.
2. The intentional Level 1 paused example is shown beside a running copy of the same animation.
3. Progress-timeline examples must stop immediately when the user stops scrolling.
4. Runtime controls operate on the same CSS animation occurrence; the demo does not call
   `Context::play_animation*` to fake CSS playback.
5. Use high-contrast geometry for blur, transforms, composition, layout, scroll and view progress.
6. Keep examples independent so one visual witness cannot replace another witness's CSS state.
7. Keep the Animation page searchable and present in the all-items overview.
8. Do not put the showcase back into a small nested list. The page itself is the scrolling surface.

## Acceptance

- The first Level 2 section immediately shows a visible difference between `replace` and `add`.
- Scrolling the named-timeline viewport moves both its subject and progress marker with no wall-clock drift.
- The view-timeline subject changes while entering/leaving its viewport and freezes when scrolling stops.
- Runtime pause freezes the current value; resume continues it; reverse preserves current progress and changes direction.
- Seeking after the finite runtime animation has finished re-samples the same occurrence instead of remaining stuck at its filled end value.
- Cancel removes the selected runtime occurrence and emits through the normal cancellation path.
- Level 1 running witnesses still move continuously after the Level 2 work.
- Resizing the gallery during playback does not panic or corrupt layout.
- Filter examples remain clipped to rounded bounds.
- The backdrop scene contains moving colored geometry behind the animated glass plate.
- The source compiles on all supported Widget Gallery backends, and the stylesheet passes the runtime load smoke test.
