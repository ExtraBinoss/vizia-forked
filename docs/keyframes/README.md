# CSS Keyframe Animation Parity

Vizia already parses `@keyframes`, interpolates a useful subset of style values, and can play a
named animation from Rust. This project turns that foundation into a predictable CSS animation
system without coupling animation playback to a particular backend.

The work is split by specification level:

- [Level 1](level-1.md) covers the authoring and playback model applications expect from CSS
  animations: `animation-*`, timing, repetition, direction, fill, pause, lifecycle events, and
  broad property coverage.
- [Level 2](level-2.md) covers additive composition, multiple effect stacks, and non-time-based
  timelines after the Level 1 model is stable.
- [Gallery and verification](gallery.md) defines the interactive examples and acceptance matrix.

## Engineering rules

1. A feature is complete only when parsing, computed style, runtime playback, invalidation, tests,
   documentation, and a gallery example agree.
2. Preserve Rust playback APIs. CSS declarations are an additional authoring path, not a
   replacement for programmatic animation.
3. Keep time calculation independent from property interpolation and renderer invalidation.
4. Do not claim browser parity for unsupported behavior. Track every gap in these checklists.
5. Prefer CSS Animations Level 1 semantics over browser-specific behavior.

Primary specifications:

- <https://drafts.csswg.org/css-animations/>
- <https://drafts.csswg.org/web-animations-1/>
- <https://drafts.csswg.org/css-animations-2/>

## Delivery order

```text
property parsing
    -> computed animation declarations
    -> automatic lifecycle
    -> timing model
    -> property interpolation and invalidation
    -> lifecycle events
    -> gallery and conformance tests
    -> Level 2 composition and timelines
```

