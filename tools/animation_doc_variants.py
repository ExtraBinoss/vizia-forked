from pathlib import Path
import re

# 1. Fix transform-list interpolation in the engine.
interp = Path('crates/vizia_core/src/animation/interpolator.rs')
text = interp.read_text()
old = '''impl Interpolator for Transform {
    fn interpolate(_start: &Self, end: &Self, _t: f32) -> Self {
        end.clone()
    }
}
'''
new = '''impl Interpolator for Transform {
    fn interpolate(start: &Self, end: &Self, t: f32) -> Self {
        match (start, end) {
            (Transform::Translate((sx, sy)), Transform::Translate((ex, ey))) => {
                Transform::Translate((
                    LengthOrPercentage::interpolate(sx, ex, t),
                    LengthOrPercentage::interpolate(sy, ey, t),
                ))
            }
            (Transform::TranslateX(start), Transform::TranslateX(end)) => {
                Transform::TranslateX(LengthOrPercentage::interpolate(start, end, t))
            }
            (Transform::TranslateY(start), Transform::TranslateY(end)) => {
                Transform::TranslateY(LengthOrPercentage::interpolate(start, end, t))
            }
            (Transform::Scale((sx, sy)), Transform::Scale((ex, ey))) => Transform::Scale((
                PercentageOrNumber::interpolate(sx, ex, t),
                PercentageOrNumber::interpolate(sy, ey, t),
            )),
            (Transform::ScaleX(start), Transform::ScaleX(end)) => {
                Transform::ScaleX(PercentageOrNumber::interpolate(start, end, t))
            }
            (Transform::ScaleY(start), Transform::ScaleY(end)) => {
                Transform::ScaleY(PercentageOrNumber::interpolate(start, end, t))
            }
            (Transform::Rotate(start), Transform::Rotate(end)) => {
                Transform::Rotate(Angle::interpolate(start, end, t))
            }
            (Transform::Skew(sx, sy), Transform::Skew(ex, ey)) => Transform::Skew(
                Angle::interpolate(sx, ex, t),
                Angle::interpolate(sy, ey, t),
            ),
            (Transform::SkewX(start), Transform::SkewX(end)) => {
                Transform::SkewX(Angle::interpolate(start, end, t))
            }
            (Transform::SkewY(start), Transform::SkewY(end)) => {
                Transform::SkewY(Angle::interpolate(start, end, t))
            }
            (Transform::Matrix(start), Transform::Matrix(end)) => {
                Transform::Matrix(Matrix::interpolate(start, end, t))
            }
            _ if t < 0.5 => start.clone(),
            _ => end.clone(),
        }
    }
}
'''
if old not in text:
    raise SystemExit('Transform interpolator anchor not found')
interp.write_text(text.replace(old, new, 1))

# 2. Add documentation variants backed by native ButtonGroup/ToggleButton controls.
rust = Path('examples/widget_gallery/src/views/animation.rs')
text = rust.read_text()

# Additional preview kinds.
text = text.replace(
    '    BackgroundGeometry,\n    BorderWidth,\n    BorderColor,\n    CornerRadius,',
    '''    BackgroundGeometry,
    BackgroundPosition,
    BackgroundSize,
    BackgroundRepeat,
    BorderWidth,
    BorderWidthTop,
    BorderWidthRight,
    BorderWidthBottom,
    BorderWidthLeft,
    BorderWidthAll,
    BorderColor,
    BorderColorTop,
    BorderColorRight,
    BorderColorBottom,
    BorderColorLeft,
    BorderColorAll,
    CornerRadius,
    CornerRadiusTopLeft,
    CornerRadiusTopRight,
    CornerRadiusBottomLeft,
    CornerRadiusBottomRight,
    CornerRadiusAll,''',
    1,
)

# Insert variant data before runtime helpers.
marker = '\nfn runtime_animation_id(cx: &EventContext) -> Option<CssAnimationId> {'
if marker not in text:
    raise SystemExit('runtime helper marker not found')
variant_block = r'''

#[derive(Clone, Copy)]
struct DocVariant {
    label: &'static str,
    css: &'static str,
    example: ExampleKind,
}

const TRANSFORM_VARIANTS: &[DocVariant] = &[
    DocVariant {
        label: "Translate",
        css: "@keyframes demo {\n  from { transform: translateX(-120px); }\n  to   { transform: translateX(120px); }\n}\n\n.target { animation: demo 1.5s ease-in-out infinite alternate; }",
        example: ExampleKind::Transform,
    },
    DocVariant {
        label: "Rotate",
        css: "@keyframes demo {\n  from { transform: rotate(-35deg); }\n  to   { transform: rotate(325deg); }\n}\n\n.target { animation: demo 1.8s linear infinite; }",
        example: ExampleKind::Transform,
    },
    DocVariant {
        label: "Combined",
        css: "@keyframes demo {\n  from { transform: translate(-100px, 0px) rotate(-25deg) scale(.78, .78); }\n  to   { transform: translate(100px, 0px) rotate(335deg) scale(1.12, 1.12); }\n}\n\n.target { animation: demo 1.8s ease-in-out infinite alternate; }",
        example: ExampleKind::Transform,
    },
];

const BACKGROUND_VARIANTS: &[DocVariant] = &[
    DocVariant {
        label: "Position",
        css: "@keyframes demo {\n  from { background-position: 0% 50%; }\n  to   { background-position: 100% 50%; }\n}\n\n.target {\n  background-size: 48% 82%;\n  background-repeat: no-repeat;\n  animation: demo 1.6s ease-in-out infinite alternate;\n}",
        example: ExampleKind::BackgroundPosition,
    },
    DocVariant {
        label: "Size",
        css: "@keyframes demo {\n  from { background-size: 30% 55%; }\n  to   { background-size: 100% 100%; }\n}\n\n.target {\n  background-position: center;\n  background-repeat: no-repeat;\n  animation: demo 1.6s ease-in-out infinite alternate;\n}",
        example: ExampleKind::BackgroundSize,
    },
    DocVariant {
        label: "Repeat",
        css: "@keyframes demo {\n  0%, 45% { background-repeat: no-repeat; }\n  55%, 100% { background-repeat: repeat; }\n}\n\n.target {\n  background-size: 56px 56px;\n  animation: demo 1.8s steps(1, end) infinite alternate;\n}",
        example: ExampleKind::BackgroundRepeat,
    },
];

const BORDER_WIDTH_VARIANTS: &[DocVariant] = &[
    DocVariant { label: "Top", css: "@keyframes demo {\n  from { border-top-width: 2px; }\n  to   { border-top-width: 24px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthTop },
    DocVariant { label: "Right", css: "@keyframes demo {\n  from { border-right-width: 2px; }\n  to   { border-right-width: 24px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthRight },
    DocVariant { label: "Bottom", css: "@keyframes demo {\n  from { border-bottom-width: 2px; }\n  to   { border-bottom-width: 24px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthBottom },
    DocVariant { label: "Left", css: "@keyframes demo {\n  from { border-left-width: 2px; }\n  to   { border-left-width: 24px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthLeft },
    DocVariant { label: "All", css: "@keyframes demo {\n  from { border-width: 2px; }\n  to   { border-width: 18px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthAll },
];

const BORDER_COLOR_VARIANTS: &[DocVariant] = &[
    DocVariant { label: "Top", css: "@keyframes demo {\n  from { border-top-color: #3b82f6; }\n  to   { border-top-color: #f97316; }\n}\n\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorTop },
    DocVariant { label: "Right", css: "@keyframes demo {\n  from { border-right-color: #3b82f6; }\n  to   { border-right-color: #f43f5e; }\n}\n\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorRight },
    DocVariant { label: "Bottom", css: "@keyframes demo {\n  from { border-bottom-color: #22c55e; }\n  to   { border-bottom-color: #a855f7; }\n}\n\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorBottom },
    DocVariant { label: "Left", css: "@keyframes demo {\n  from { border-left-color: #06b6d4; }\n  to   { border-left-color: #eab308; }\n}\n\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorLeft },
    DocVariant { label: "All", css: "@keyframes demo {\n  from { border-color: #3b82f6; }\n  to   { border-color: #f43f5e; }\n}\n\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorAll },
];

const CORNER_RADIUS_VARIANTS: &[DocVariant] = &[
    DocVariant { label: "All", css: "@keyframes demo {\n  from { corner-radius: 6px; }\n  to   { corner-radius: 72px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusAll },
    DocVariant { label: "Top left", css: "@keyframes demo {\n  from { corner-top-left-radius: 4px; }\n  to   { corner-top-left-radius: 90px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusTopLeft },
    DocVariant { label: "Top right", css: "@keyframes demo {\n  from { corner-top-right-radius: 4px; }\n  to   { corner-top-right-radius: 90px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusTopRight },
    DocVariant { label: "Bottom left", css: "@keyframes demo {\n  from { corner-bottom-left-radius: 4px; }\n  to   { corner-bottom-left-radius: 90px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusBottomLeft },
    DocVariant { label: "Bottom right", css: "@keyframes demo {\n  from { corner-bottom-right-radius: 4px; }\n  to   { corner-bottom-right-radius: 90px; }\n}\n\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusBottomRight },
];

fn doc_variants(title: &str) -> &'static [DocVariant] {
    match title {
        "transform" => TRANSFORM_VARIANTS,
        "background-image / position / repeat / size" => BACKGROUND_VARIANTS,
        "border-top/right/bottom/left-width" => BORDER_WIDTH_VARIANTS,
        "border-top/right/bottom/left-color" => BORDER_COLOR_VARIANTS,
        "corner-*-radius / smoothing" => CORNER_RADIUS_VARIANTS,
        _ => &[],
    }
}

fn selected_variant<'a>(doc: &'a DocEntry, variants: &'a [DocVariant], index: usize) -> (&'a str, ExampleKind) {
    variants
        .get(index)
        .map(|variant| (variant.css, variant.example))
        .unwrap_or((doc.css, doc.example))
}

fn render_variant_picker(cx: &mut Context, variants: &'static [DocVariant], selected: Signal<usize>) {
    if variants.len() < 2 {
        return;
    }

    ButtonGroup::new(cx, move |cx| {
        for (index, variant) in variants.iter().enumerate() {
            ToggleButton::new(
                cx,
                selected.map(move |current| *current == index),
                move |cx| Label::new(cx, variant.label),
            )
            .on_toggle(move |_cx| selected.set(index));
        }
    })
    .class("animation-doc-variant-tabs");
}
'''
text = text.replace(marker, variant_block + marker, 1)

# Add preview arms after background geometry and grouped property arms.
text = text.replace(
    '''        ExampleKind::BackgroundGeometry => {
            surface_stage(cx, "background geometry", "animation-doc-background-geometry")
        }
        ExampleKind::BorderWidth => surface_stage(cx, "border width", "animation-doc-border-width"),
        ExampleKind::BorderColor => surface_stage(cx, "border color", "animation-doc-border-color"),
        ExampleKind::CornerRadius => surface_stage(cx, "radius", "animation-doc-radius"),
''',
    '''        ExampleKind::BackgroundGeometry => {
            surface_stage(cx, "background", "animation-doc-background-geometry")
        }
        ExampleKind::BackgroundPosition => surface_stage(cx, "position", "animation-doc-bg-position"),
        ExampleKind::BackgroundSize => surface_stage(cx, "size", "animation-doc-bg-size"),
        ExampleKind::BackgroundRepeat => surface_stage(cx, "repeat", "animation-doc-bg-repeat"),
        ExampleKind::BorderWidth => surface_stage(cx, "border width", "animation-doc-border-width-all"),
        ExampleKind::BorderWidthTop => surface_stage(cx, "TOP", "animation-doc-border-width-top"),
        ExampleKind::BorderWidthRight => surface_stage(cx, "RIGHT", "animation-doc-border-width-right"),
        ExampleKind::BorderWidthBottom => surface_stage(cx, "BOTTOM", "animation-doc-border-width-bottom"),
        ExampleKind::BorderWidthLeft => surface_stage(cx, "LEFT", "animation-doc-border-width-left"),
        ExampleKind::BorderWidthAll => surface_stage(cx, "ALL SIDES", "animation-doc-border-width-all"),
        ExampleKind::BorderColor => surface_stage(cx, "border color", "animation-doc-border-color-all"),
        ExampleKind::BorderColorTop => surface_stage(cx, "TOP", "animation-doc-border-color-top"),
        ExampleKind::BorderColorRight => surface_stage(cx, "RIGHT", "animation-doc-border-color-right"),
        ExampleKind::BorderColorBottom => surface_stage(cx, "BOTTOM", "animation-doc-border-color-bottom"),
        ExampleKind::BorderColorLeft => surface_stage(cx, "LEFT", "animation-doc-border-color-left"),
        ExampleKind::BorderColorAll => surface_stage(cx, "ALL SIDES", "animation-doc-border-color-all"),
        ExampleKind::CornerRadius => surface_stage(cx, "radius", "animation-doc-radius-all"),
        ExampleKind::CornerRadiusTopLeft => surface_stage(cx, "TOP LEFT", "animation-doc-radius-tl"),
        ExampleKind::CornerRadiusTopRight => surface_stage(cx, "TOP RIGHT", "animation-doc-radius-tr"),
        ExampleKind::CornerRadiusBottomLeft => surface_stage(cx, "BOTTOM LEFT", "animation-doc-radius-bl"),
        ExampleKind::CornerRadiusBottomRight => surface_stage(cx, "BOTTOM RIGHT", "animation-doc-radius-br"),
        ExampleKind::CornerRadiusAll => surface_stage(cx, "ALL CORNERS", "animation-doc-radius-all"),
''',
    1,
)

# Replace render_doc_content with variant-aware version.
start = text.index('fn render_doc_content(cx: &mut Context, index: usize) {')
end = text.index('\nfn build_doc_navigation', start)
replacement = r'''fn render_doc_content(cx: &mut Context, index: usize) {
    let doc = &DOCS[index];
    let variants = doc_variants(doc.title);
    let selected = Signal::new(0usize);

    VStack::new(cx, move |cx| {
        Label::new(cx, doc.title).class("animation-doc-title");
        Label::new(cx, doc.description).class("animation-doc-description");

        HStack::new(cx, move |cx| {
            VStack::new(cx, move |cx| {
                HStack::new(cx, move |cx| {
                    Label::new(cx, "CSS").class("animation-doc-pane-title");
                    Element::new(cx).width(Stretch(1.0));
                    render_variant_picker(cx, variants, selected);
                })
                .class("animation-doc-code-header");

                Binding::new(cx, selected, move |cx| {
                    let (css, _) = selected_variant(doc, variants, selected.get());
                    VStack::new(cx, move |cx| {
                        Label::new(cx, css)
                            .class("animation-doc-code")
                            .text_wrap(true);
                        Element::new(cx).height(Stretch(1.0));
                        HStack::new(cx, move |cx| {
                            Element::new(cx).width(Stretch(1.0));
                            Button::new(cx, |cx| Label::new(cx, "Copy CSS"))
                                .variant(ButtonVariant::Outline)
                                .class("animation-doc-copy-button")
                                .on_press(move |cx| {
                                    let (css, _) = selected_variant(doc, variants, selected.get());
                                    let _ = cx.set_clipboard(css.to_string());
                                });
                        })
                        .class("animation-doc-copy-row");
                    })
                    .class("animation-doc-code-body")
                    .alignment(Alignment::TopLeft);
                });
            })
            .class("animation-doc-code-pane");

            VStack::new(cx, move |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "Result").class("animation-doc-pane-title");
                })
                .class("animation-doc-result-header");

                Binding::new(cx, selected, move |cx| {
                    let (_, example) = selected_variant(doc, variants, selected.get());
                    VStack::new(cx, move |cx| render_preview(cx, example))
                        .class("animation-doc-result-body");
                });
            })
            .class("animation-doc-result-pane");
        })
        .class("animation-doc-example");

        VStack::new(cx, |cx| {
            Label::new(cx, "Implementation note").class("animation-doc-note-title");
            Label::new(cx, "CSS animations are sampled directly through Vizia's existing AnimatableSet / AnimatableVarSet property stores. Only the selected example and selected variant are mounted, so browsing the reference does not leave unrelated animation clocks running.").class("animation-doc-note-copy");
        })
        .class("animation-doc-note");
    })
    .class("animation-doc-content");
}
'''
text = text[:start] + replacement + text[end:]
rust.write_text(text)

# 3. Make demo CSS robust and obvious.
css = Path('examples/widget_gallery/resources/themes/animation.css')
c = css.read_text()

# Class-only selectors are safer for composed gallery views whose semantic element name may differ.
for prefix in ('vstack', 'hstack', 'zstack', 'scrollview', 'label', 'button', 'element', 'svg', 'popup'):
    c = re.sub(rf'(?m)\b{prefix}\.(animation-doc-[A-Za-z0-9_-]+)', r'.\1', c)

# Give text/border demos actual breathing room.
c = re.sub(
    r'\.animation-doc-surface-target \{.*?\n\}',
    '''.animation-doc-surface-target {
    width: 300px;
    min-width: 300px;
    height: 150px;
    min-height: 150px;
    padding: 32px 40px;
    alignment: center;
    text-align: center;
    text-wrap: true;
    font-size: 18px;
}''',
    c,
    count=1,
    flags=re.S,
)

# Variant picker only controls spacing; the controls keep native gallery visuals.
if '.animation-doc-variant-tabs {' not in c:
    c = c.replace(
        '.animation-doc-pane-title {',
        '''.animation-doc-variant-tabs {
    width: auto;
    height: auto;
}

.animation-doc-pane-title {''',
        1,
    )

# Stronger, clearly-visible background demos.
c += r'''

/* Interactive reference variants. */
@keyframes doc-bg-position {
    from { background-position: 0% 50%; }
    to { background-position: 100% 50%; }
}
@keyframes doc-bg-size {
    from { background-size: 30% 55%; }
    to { background-size: 100% 100%; }
}
@keyframes doc-bg-repeat {
    0%, 45% { background-repeat: no-repeat; }
    55%, 100% { background-repeat: repeat; }
}
.animation-doc-bg-position,
.animation-doc-bg-size,
.animation-doc-bg-repeat {
    background-image: linear-gradient(90deg, #2563eb, #8b5cf6, #f97316);
    background-color: var(--background-alt);
    color: white;
}
.animation-doc-bg-position {
    background-size: 48% 82%;
    background-repeat: no-repeat;
    animation: doc-bg-position 1600ms ease-in-out infinite alternate;
}
.animation-doc-bg-size {
    background-position: center;
    background-repeat: no-repeat;
    animation: doc-bg-size 1600ms ease-in-out infinite alternate;
}
.animation-doc-bg-repeat {
    background-position: center;
    background-size: 56px 56px;
    animation: doc-bg-repeat 1800ms steps(1, end) infinite alternate;
}

@keyframes doc-border-width-top { from { border-top-width: 2px; } to { border-top-width: 24px; } }
@keyframes doc-border-width-right { from { border-right-width: 2px; } to { border-right-width: 24px; } }
@keyframes doc-border-width-bottom { from { border-bottom-width: 2px; } to { border-bottom-width: 24px; } }
@keyframes doc-border-width-left { from { border-left-width: 2px; } to { border-left-width: 24px; } }
@keyframes doc-border-width-all { from { border-width: 2px; } to { border-width: 18px; } }
.animation-doc-border-width-top,
.animation-doc-border-width-right,
.animation-doc-border-width-bottom,
.animation-doc-border-width-left,
.animation-doc-border-width-all {
    border-style: solid;
    border-color: #3b82f6;
    background-color: var(--background-alt);
    color: var(--foreground);
}
.animation-doc-border-width-top { animation: doc-border-width-top 1400ms ease-in-out infinite alternate; }
.animation-doc-border-width-right { animation: doc-border-width-right 1400ms ease-in-out infinite alternate; }
.animation-doc-border-width-bottom { animation: doc-border-width-bottom 1400ms ease-in-out infinite alternate; }
.animation-doc-border-width-left { animation: doc-border-width-left 1400ms ease-in-out infinite alternate; }
.animation-doc-border-width-all { animation: doc-border-width-all 1400ms ease-in-out infinite alternate; }

@keyframes doc-border-color-top { from { border-top-color: #3b82f6; } to { border-top-color: #f97316; } }
@keyframes doc-border-color-right { from { border-right-color: #3b82f6; } to { border-right-color: #f43f5e; } }
@keyframes doc-border-color-bottom { from { border-bottom-color: #22c55e; } to { border-bottom-color: #a855f7; } }
@keyframes doc-border-color-left { from { border-left-color: #06b6d4; } to { border-left-color: #eab308; } }
@keyframes doc-border-color-all { from { border-color: #3b82f6; } to { border-color: #f43f5e; } }
.animation-doc-border-color-top,
.animation-doc-border-color-right,
.animation-doc-border-color-bottom,
.animation-doc-border-color-left,
.animation-doc-border-color-all {
    border-style: solid;
    border-width: 12px;
    border-color: #475569;
    background-color: var(--background-alt);
    color: var(--foreground);
}
.animation-doc-border-color-top { animation: doc-border-color-top 1300ms ease-in-out infinite alternate; }
.animation-doc-border-color-right { animation: doc-border-color-right 1300ms ease-in-out infinite alternate; }
.animation-doc-border-color-bottom { animation: doc-border-color-bottom 1300ms ease-in-out infinite alternate; }
.animation-doc-border-color-left { animation: doc-border-color-left 1300ms ease-in-out infinite alternate; }
.animation-doc-border-color-all { animation: doc-border-color-all 1300ms ease-in-out infinite alternate; }

@keyframes doc-radius-tl { from { corner-top-left-radius: 4px; } to { corner-top-left-radius: 90px; } }
@keyframes doc-radius-tr { from { corner-top-right-radius: 4px; } to { corner-top-right-radius: 90px; } }
@keyframes doc-radius-bl { from { corner-bottom-left-radius: 4px; } to { corner-bottom-left-radius: 90px; } }
@keyframes doc-radius-br { from { corner-bottom-right-radius: 4px; } to { corner-bottom-right-radius: 90px; } }
@keyframes doc-radius-all { from { corner-radius: 6px; } to { corner-radius: 72px; } }
.animation-doc-radius-tl,
.animation-doc-radius-tr,
.animation-doc-radius-bl,
.animation-doc-radius-br,
.animation-doc-radius-all {
    background-color: #2563eb;
    color: white;
}
.animation-doc-radius-tl { animation: doc-radius-tl 1400ms ease-in-out infinite alternate; }
.animation-doc-radius-tr { animation: doc-radius-tr 1400ms ease-in-out infinite alternate; }
.animation-doc-radius-bl { animation: doc-radius-bl 1400ms ease-in-out infinite alternate; }
.animation-doc-radius-br { animation: doc-radius-br 1400ms ease-in-out infinite alternate; }
.animation-doc-radius-all { animation: doc-radius-all 1400ms ease-in-out infinite alternate; }
'''

# Fix backdrop demo: transparent glass, moving content visible through it.
c = c.replace('background-color: #66ffffff;', 'background-color: #ffffff33;')

css.write_text(c)

# 4. Correct and extend gotchas.
gotchas = Path('docs/keyframes/gotchas.md')
g = gotchas.read_text()
g = g.replace(
    '''Concrete example from the animation gallery: `border-style` is not currently a Vizia CSS property in
this fork. A browser-style `border-style: solid` declaration therefore should not be copied blindly
into Vizia CSS; use the supported border width/color properties and verify the stylesheet in `Context`.

''',
    '',
)
if '## Compatible transform functions need real interpolation' not in g:
    g += '''

## Compatible transform functions need real interpolation

Do not implement `Transform::interpolate` as a blanket `end.clone()`. Compatible transform functions
(`translate`, `scale`, `rotate`, `skew`, and matrix pairs) need component-wise interpolation; only
incompatible function pairs should fall back to a discrete switch. A transform demo that appears
rotated but never actually moves is a useful signal to inspect the interpolator rather than the CSS
parser.

## Prefer class selectors for gallery-specific demo styling

Widget Gallery examples are composed from Rust views and wrappers. For demo-only styling, prefer a
stable class selector such as `.animation-doc-surface-target` over unnecessarily type-qualified forms
such as `label.animation-doc-surface-target` or `vstack.animation-doc-backdrop-glass`. This avoids
making a visual demo depend on the semantic element name emitted by a particular view wrapper.
'''
gotchas.write_text(g)
