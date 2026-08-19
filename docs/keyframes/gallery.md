# Animation Gallery and Verification

The widget gallery owns a top-level **Animation** page. Its running examples intentionally loop
continuously so visual regressions are obvious as soon as the page opens. The page is a visual
stress-test of CSS-driven playback rather than a click-to-replay showcase.

A `VirtualList` at the top indexes the Level 1 demonstrations so the expected coverage is visible
without reading the source.

## Level 1 example matrix

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
- [ ] Lifecycle event log.
- [ ] Dedicated reduced-motion visual comparison.

## Interaction rules

1. Running examples loop continuously with short periods (roughly one second) so movement is always visible.
2. The intentional paused example must be shown beside a running copy of the same animation.
3. Use high-contrast geometry for blur, clipping, transform, composition, and layout demonstrations.
4. Keep examples independent so one demo cannot reset or replace another demo's CSS animation state.
5. Keep a `VirtualList` index of the visible Level 1 demonstrations at the top of the page.
6. Include the Animation page in gallery search and the all-items overview.
7. Drive the page with `@keyframes` and `animation-*`; do not use `Context::play_animation*` to fake CSS playback.

## Acceptance

- Motion is visible immediately after opening the Animation page without pressing a replay button.
- Infinite/alternate examples keep cycling deterministically.
- The paused comparison remains frozen while its running counterpart continues moving.
- Resizing the gallery during playback does not panic or corrupt layout.
- Filter examples remain clipped to rounded bounds.
- The backdrop scene visibly contains moving colored geometry behind the animated glass plate.
- The page behaves in light, dark, LTR, RTL, and HiDPI configurations.
- Examples compile on all supported window backends.
