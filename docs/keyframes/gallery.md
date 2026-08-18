# Animation Gallery and Verification

The widget gallery owns a top-level **Animation** page. Every example must be replayable so visual
regressions can be inspected without restarting the application.

## Level 1 example matrix

- [x] Entrance: opacity + translate + scale.
- [x] Style interpolation: background color + corner radius.
- [ ] Layout: width/height or gap with visible neighboring content.
- [x] Multi-keyframe motion: at least three offsets.
- [ ] Segment easing: visibly different timing functions.
- [ ] Delay and negative delay.
- [ ] Iteration and alternate direction.
- [ ] Fill modes.
- [ ] Pause and resume.
- [x] Filter blur reveal.
- [x] Rounded backdrop-filter reveal over high-contrast content.
- [ ] Multiple animations on one entity.
- [ ] Lifecycle event log.
- [ ] Reduced-motion behavior.

## Interaction rules

1. Give each example its own replay button and stable entity ID.
2. Show the relevant CSS beside or directly below the visual result when practical.
3. Use high-contrast geometry for blur, clipping, and transform demonstrations.
4. Do not animate automatically forever when opening the page.
5. Keep examples independent so replaying one does not reset another.
6. Include the Animation page in gallery search and the all-items overview.

## Acceptance

- Clicking replay always starts from the first frame.
- Rapid repeated clicks restart deterministically.
- Resizing the gallery during playback does not panic or corrupt layout.
- Filter examples remain clipped to rounded bounds.
- The page behaves in light, dark, LTR, RTL, and HiDPI configurations.
- Examples compile on all supported window backends.
