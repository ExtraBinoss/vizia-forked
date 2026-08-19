use vizia::{icons::ICON_HEART, prelude::*};

const DOC_RUNTIME_TARGET_ID: &str = "animation-doc-runtime-target";
const DOC_RUNTIME_DURATION: f32 = 6.0;

#[derive(Clone, Copy, PartialEq, Eq)]
enum ExampleKind {
    Motion,
    Duration,
    Delay,
    Steps,
    Iterations,
    Direction,
    FillMode,
    Paused,
    Composition,
    DocumentTimeline,
    ScrollTimeline,
    ViewTimeline,
    PercentageKeyframes,
    Multiple,
    Opacity,
    Transform,
    TransformOrigin,
    Translate,
    Rotate,
    Scale,
    ClipPath,
    Filter,
    BackdropFilter,
    BackgroundColor,
    BackgroundGeometry,
    BorderWidth,
    BorderColor,
    CornerRadius,
    Outline,
    Shadow,
    TextColor,
    FontSize,
    LetterSpacing,
    LineHeight,
    TextPaint,
    Fill,
    Position,
    Padding,
    Gap,
    Size,
    Constraints,
    Display,
    StaticInfo,
    Runtime,
    Popover,
    Throbber,
}

struct DocEntry {
    category: &'static str,
    title: &'static str,
    css: &'static str,
    description: &'static str,
    example: ExampleKind,
}

const DOCS: &[DocEntry] = &[
    DocEntry {
        category: "Animation properties",
        title: "animation",
        css: r#"@keyframes move {
  from { translate: -110px 0; opacity: .45; }
  to   { translate: 110px 0; opacity: 1; }
}

.target {
  animation: move 1.6s ease-in-out
             -300ms infinite alternate both;
}"#,
        description: "The shorthand wires name, duration, easing, delay, iteration count, direction, fill mode and play state into one CSS animation occurrence.",
        example: ExampleKind::Motion,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-name",
        css: r#".target {
  animation-name: move;
  animation-duration: 1.6s;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}"#,
        description: "Selects the @keyframes rule by name. Vizia starts, updates and cancels the CSS animation automatically from computed style.",
        example: ExampleKind::Motion,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-duration",
        css: r#".target {
  animation-name: move;
  animation-duration: 3.5s;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}"#,
        description: "Controls the active interval for one iteration. Negative durations are rejected.",
        example: ExampleKind::Duration,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-delay",
        css: r#".target {
  animation: move 1.6s ease-in-out;
  animation-delay: -800ms;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}"#,
        description: "Positive and negative delays are supported. A negative delay begins as if the animation had already been running.",
        example: ExampleKind::Delay,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-timing-function",
        css: r#".target {
  animation: move 1.8s
    cubic-bezier(.2, .8, .2, 1)
    infinite alternate;
}"#,
        description: "Supports CSS easing keywords, validated cubic-bezier() and steps() timing functions.",
        example: ExampleKind::Motion,
    },
    DocEntry {
        category: "Animation properties",
        title: "steps() / step-start / step-end",
        css: r#".target {
  animation: move 1.8s
    steps(6, end)
    infinite alternate;
}"#,
        description: "Discrete timing functions jump between sampled positions instead of interpolating continuously.",
        example: ExampleKind::Steps,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-iteration-count",
        css: r#".target {
  animation: move 900ms ease-in-out;
  animation-iteration-count: 3;
  animation-fill-mode: forwards;
}"#,
        description: "Finite, fractional and infinite iteration counts are supported. This example runs three times and keeps its final value.",
        example: ExampleKind::Iterations,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-direction",
        css: r#".target {
  animation: move 1.4s ease-in-out
             infinite alternate-reverse;
}"#,
        description: "normal, reverse, alternate and alternate-reverse affect iteration progress without changing the keyframe data.",
        example: ExampleKind::Direction,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-fill-mode",
        css: r#".target {
  animation: settle 900ms ease-out;
  animation-fill-mode: forwards;
}"#,
        description: "none, forwards, backwards and both control whether sampled values apply before or after the active phase.",
        example: ExampleKind::FillMode,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-play-state",
        css: r#".target {
  animation: move 1.6s ease-in-out
             -800ms infinite alternate;
  animation-play-state: paused;
}"#,
        description: "running and paused operate on the same CSS occurrence and preserve local progress when resumed.",
        example: ExampleKind::Paused,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-composition",
        css: r#".target {
  animation:
    move-x 1.8s infinite alternate,
    move-y 1.1s infinite alternate;

  animation-composition: add, add;
}"#,
        description: "replace, add and accumulate are resolved inside Vizia's property stores using a stable per-property effect stack.",
        example: ExampleKind::Composition,
    },
    DocEntry {
        category: "Animation properties",
        title: "animation-timeline",
        css: r#".target {
  animation: reveal 1s linear both;
  animation-timeline: auto;
}

/* Also supported:
   --named-timeline
   scroll(nearest block)
   view(block)
*/"#,
        description: "The effect can be sampled from document time, a named scroll source, scroll() or view() progress.",
        example: ExampleKind::DocumentTimeline,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "@keyframes",
        css: r#"@keyframes pulse {
  from {
    opacity: .35;
    scale: .8;
  }
  to {
    opacity: 1;
    scale: 1.15;
  }
}"#,
        description: "from/to and percentage offsets are parsed into the same animation storage used by Rust-side animations and transitions.",
        example: ExampleKind::Motion,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "percentage keyframes",
        css: r#"@keyframes orbit {
  0%   { translate: -120px 0; }
  35%  { translate: -20px -35px; }
  70%  { translate: 80px 24px; }
  100% { translate: 120px 0; }
}

.target {
  animation: orbit 1.8s ease-in-out
             infinite alternate;
}"#,
        description: "Multiple offsets, duplicate offsets, implicit endpoints and underlying values are normalized by the CSS animation runtime.",
        example: ExampleKind::PercentageKeyframes,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "multiple animations",
        css: r#".target {
  animation:
    move 1.6s ease-in-out infinite alternate,
    color 2.4s linear infinite alternate;
}"#,
        description: "Comma-separated animation lists create independent occurrences. CSS list repetition rules resolve shorter longhand lists.",
        example: ExampleKind::Multiple,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "document timeline",
        css: r#".target {
  animation: move 2s linear infinite alternate;
  animation-timeline: auto;
}"#,
        description: "The default document timeline advances from wall-clock time and requests frames only while sampled values are changing.",
        example: ExampleKind::DocumentTimeline,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "named scroll timeline",
        css: r#".target {
  animation: reveal 1s linear both;
  animation-timeline: --docs-scroll;
}

/* Rust source */
ScrollView::new(cx, content)
  .timeline_name("--docs-scroll");"#,
        description: "A Vizia ScrollView can publish a named normalized progress source that CSS animations consume directly.",
        example: ExampleKind::ScrollTimeline,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "scroll()",
        css: r#".target {
  animation: reveal 1s linear both;
  animation-timeline:
    scroll(nearest block);
}"#,
        description: "scroll() uses the selected scroll source and axis as the animation clock. Stop scrolling and the animation freezes.",
        example: ExampleKind::ScrollTimeline,
    },
    DocEntry {
        category: "Keyframes & timelines",
        title: "view()",
        css: r#".target {
  animation: reveal 1s linear both;
  animation-timeline: view(block);
}"#,
        description: "view() derives progress from the subject entering and leaving its nearest scroll viewport.",
        example: ExampleKind::ViewTimeline,
    },
    DocEntry {
        category: "Animated values",
        title: "opacity",
        css: r#"@keyframes demo {
  from { opacity: .15; }
  to   { opacity: 1; }
}"#,
        description: "Paint-only interpolation. It does not require layout or text reconstruction.",
        example: ExampleKind::Opacity,
    },
    DocEntry {
        category: "Animated values",
        title: "transform",
        css: r#"@keyframes demo {
  from { transform: translateX(-90px) rotate(-25deg); }
  to   { transform: translateX(90px) rotate(335deg); }
}"#,
        description: "Transform lists are sampled through the retransform path rather than layout.",
        example: ExampleKind::Transform,
    },
    DocEntry {
        category: "Animated values",
        title: "transform-origin",
        css: r#"@keyframes demo {
  from { transform-origin: 0% 50%; rotate: -35deg; }
  to   { transform-origin: 100% 50%; rotate: 35deg; }
}"#,
        description: "Transform origin is store-backed and participates in the same animation clock as transforms.",
        example: ExampleKind::TransformOrigin,
    },
    DocEntry {
        category: "Animated values",
        title: "translate",
        css: r#"@keyframes demo {
  from { translate: -110px 0; }
  to   { translate: 110px 0; }
}"#,
        description: "Individual translate is independently animatable and supports additive effect composition.",
        example: ExampleKind::Translate,
    },
    DocEntry {
        category: "Animated values",
        title: "rotate",
        css: r#"@keyframes demo {
  from { rotate: -30deg; }
  to   { rotate: 330deg; }
}"#,
        description: "Individual rotate is independently animatable and supports add/accumulate composition.",
        example: ExampleKind::Rotate,
    },
    DocEntry {
        category: "Animated values",
        title: "scale",
        css: r#"@keyframes demo {
  from { scale: .65; }
  to   { scale: 1.25; }
}"#,
        description: "Individual scale is independently animatable and participates in transform invalidation.",
        example: ExampleKind::Scale,
    },
    DocEntry {
        category: "Animated values",
        title: "clip-path",
        css: r#"@keyframes demo {
  from { clip-path: inset(18px); }
  to   { clip-path: inset(0px); }
}"#,
        description: "Clip path changes use the reclip path. Incompatible shapes fall back deterministically.",
        example: ExampleKind::ClipPath,
    },
    DocEntry {
        category: "Animated values",
        title: "filter",
        css: r#"@keyframes demo {
  from { filter: blur(0px); }
  50%  { filter: blur(10px); }
  to   { filter: blur(0px); }
}"#,
        description: "Compatible filter lists interpolate; incompatible lists use discrete fallback.",
        example: ExampleKind::Filter,
    },
    DocEntry {
        category: "Animated values",
        title: "backdrop-filter",
        css: r#"@keyframes demo {
  from { backdrop-filter: blur(1px); }
  to   { backdrop-filter: blur(12px); }
}"#,
        description: "Backdrop filter interpolation is tracked sparsely so only filter-bearing entities take the filter-aware draw path.",
        example: ExampleKind::BackdropFilter,
    },
    DocEntry {
        category: "Animated values",
        title: "background-color",
        css: r#"@keyframes demo {
  from { background-color: #3b82f6; }
  to   { background-color: #8b5cf6; }
}"#,
        description: "Background colors interpolate as paint-only values.",
        example: ExampleKind::BackgroundColor,
    },
    DocEntry {
        category: "Animated values",
        title: "background-image / position / repeat / size",
        css: r#"@keyframes demo {
  from {
    background-position: 0% 50%;
    background-size: 90% 90%;
  }
  to {
    background-position: 100% 50%;
    background-size: 125% 125%;
  }
}"#,
        description: "The background image, position, repeat and size stores participate in keyframe playback. Incompatible image/repeat values use deterministic fallback.",
        example: ExampleKind::BackgroundGeometry,
    },
    DocEntry {
        category: "Animated values",
        title: "border-top/right/bottom/left-width",
        css: r#"@keyframes demo {
  from { border-top-width: 1px; }
  to   { border-top-width: 12px; }
}"#,
        description: "All four border width stores are animatable. Width changes are layout-affecting and use change-aware relayout ticking.",
        example: ExampleKind::BorderWidth,
    },
    DocEntry {
        category: "Animated values",
        title: "border-top/right/bottom/left-color",
        css: r#"@keyframes demo {
  from { border-color: #3b82f6; }
  to   { border-color: #f43f5e; }
}"#,
        description: "All four border colors interpolate as paint values.",
        example: ExampleKind::BorderColor,
    },
    DocEntry {
        category: "Animated values",
        title: "corner-*-radius / smoothing",
        css: r#"@keyframes demo {
  from { corner-radius: 4px; }
  to   { corner-radius: 34px; }
}"#,
        description: "Per-corner radius and smoothing stores are animatable. Radius changes also trigger rounded re-clipping.",
        example: ExampleKind::CornerRadius,
    },
    DocEntry {
        category: "Animated values",
        title: "outline-width / color / offset",
        css: r#"@keyframes demo {
  from {
    outline-width: 1px;
    outline-color: #3b82f6;
    outline-offset: 1px;
  }
  to {
    outline-width: 6px;
    outline-color: #a855f7;
    outline-offset: 8px;
  }
}"#,
        description: "Outline width, color and offset are all backed by animatable stores.",
        example: ExampleKind::Outline,
    },
    DocEntry {
        category: "Animated values",
        title: "shadow",
        css: r#"@keyframes demo {
  from { shadow: 0px 2px 6px #22000000; }
  to   { shadow: 0px 16px 34px #55000000; }
}"#,
        description: "Compatible shadow lists interpolate and redraw without relayout.",
        example: ExampleKind::Shadow,
    },
    DocEntry {
        category: "Animated values",
        title: "color",
        css: r#"@keyframes demo {
  from { color: #3b82f6; }
  to   { color: #f43f5e; }
}"#,
        description: "Font color is a paint-only text property and does not reconstruct text layout.",
        example: ExampleKind::TextColor,
    },
    DocEntry {
        category: "Animated values",
        title: "font-size",
        css: r#"@keyframes demo {
  from { font-size: 20px; }
  to   { font-size: 42px; }
}"#,
        description: "Font size animation requests text reconstruction because glyph metrics change.",
        example: ExampleKind::FontSize,
    },
    DocEntry {
        category: "Animated values",
        title: "letter-spacing",
        css: r#"@keyframes demo {
  from { letter-spacing: 0px; }
  to   { letter-spacing: 8px; }
}"#,
        description: "Letter spacing is reflow-affecting and uses the text construction path.",
        example: ExampleKind::LetterSpacing,
    },
    DocEntry {
        category: "Animated values",
        title: "line-height",
        css: r#"@keyframes demo {
  from { line-height: 1; }
  to   { line-height: 1.8; }
}"#,
        description: "Line height is reflow-affecting and shares the animation clock with other text properties.",
        example: ExampleKind::LineHeight,
    },
    DocEntry {
        category: "Animated values",
        title: "caret / selection / text-decoration color",
        css: r#"@keyframes demo {
  from {
    caret-color: #3b82f6;
    selection-color: #3b82f6;
    text-decoration-color: #3b82f6;
  }
  to {
    caret-color: #f43f5e;
    selection-color: #f43f5e;
    text-decoration-color: #f43f5e;
  }
}"#,
        description: "These text paint stores are animatable without text reconstruction.",
        example: ExampleKind::TextPaint,
    },
    DocEntry {
        category: "Animated values",
        title: "fill",
        css: r#"@keyframes demo {
  from { fill: #3b82f6; }
  to   { fill: #22c55e; }
}"#,
        description: "The fill color store is animatable and redraw-only.",
        example: ExampleKind::Fill,
    },
    DocEntry {
        category: "Animated values",
        title: "left / right / top / bottom",
        css: r#"@keyframes demo {
  from { left: 12px; top: 8px; }
  to   { left: 110px; top: 36px; }
}"#,
        description: "Position offsets are layout-affecting. The runtime only requests relayout when the sampled value actually changes.",
        example: ExampleKind::Position,
    },
    DocEntry {
        category: "Animated values",
        title: "padding-left/right/top/bottom",
        css: r#"@keyframes demo {
  from { padding: 6px; }
  to   { padding: 28px; }
}"#,
        description: "All four padding stores are animatable and layout-affecting.",
        example: ExampleKind::Padding,
    },
    DocEntry {
        category: "Animated values",
        title: "horizontal-gap / vertical-gap",
        css: r#"@keyframes demo {
  from { horizontal-gap: 6px; }
  to   { horizontal-gap: 44px; }
}"#,
        description: "Row/column gaps are animatable layout values and participate in change-aware relayout ticking.",
        example: ExampleKind::Gap,
    },
    DocEntry {
        category: "Animated values",
        title: "width / height",
        css: r#"@keyframes demo {
  from { width: 90px; height: 58px; }
  to   { width: 240px; height: 92px; }
}"#,
        description: "Width and height support keyframe interpolation, including the existing auto-size animation resolution path.",
        example: ExampleKind::Size,
    },
    DocEntry {
        category: "Animated values",
        title: "min/max width/height + min/max gaps",
        css: r#"@keyframes demo {
  from { min-width: 90px; max-width: 140px; }
  to   { min-width: 180px; max-width: 280px; }
}"#,
        description: "Constraint stores and min/max horizontal/vertical gap stores participate in CSS animation playback.",
        example: ExampleKind::Constraints,
    },
    DocEntry {
        category: "Animated values",
        title: "display",
        css: r#"@keyframes demo {
  0%, 49% { display: none; }
  50%, 100% { display: flex; }
}"#,
        description: "Display is store-backed but fundamentally discrete rather than numerically interpolated.",
        example: ExampleKind::Display,
    },
    DocEntry {
        category: "Animated values",
        title: "typed custom properties",
        css: r#"/* Vizia typed custom-property stores share
   the same CSS animation clock for:
   color, length, font-size, letter-spacing,
   line-height, units, opacity and shadow. */"#,
        description: "Typed Vizia custom property families use the same animation/composition machinery as built-in properties.",
        example: ExampleKind::StaticInfo,
    },
    DocEntry {
        category: "Runtime & UI patterns",
        title: "runtime controls",
        css: r#".target {
  animation: move 6s linear infinite alternate;
}

/* Rust */
cx.pause_css_animation(id);
cx.resume_css_animation(id);
cx.seek_css_animation(id, seconds);
cx.reverse_css_animation(id);
cx.set_css_animation_playback_rate(id, 2.0);"#,
        description: "Runtime control operates on the same stable CSS occurrence and the same property-store clocks that render the effect.",
        example: ExampleKind::Runtime,
    },
    DocEntry {
        category: "Runtime & UI patterns",
        title: "blur reveal popover",
        css: r#"@keyframes reveal {
  from {
    opacity: 0;
    filter: blur(8px);
    translate: 0 -5px;
  }
  to {
    opacity: 1;
    filter: blur(0);
    translate: 0 0;
  }
}

popover {
  animation: reveal 180ms ease-out both;
}"#,
        description: "A native Vizia Popover can use the same CSS animation engine for a short entrance effect.",
        example: ExampleKind::Popover,
    },
    DocEntry {
        category: "Runtime & UI patterns",
        title: "text throbber",
        css: r#".dot {
  animation: throb 900ms ease-in-out
             infinite alternate;
}

.dot:nth-child(2) { animation-delay: -300ms; }
.dot:nth-child(3) { animation-delay: -600ms; }"#,
        description: "A small staggered loading indicator uses independent animation occurrences and negative delays.",
        example: ExampleKind::Throbber,
    },
];

fn runtime_animation_id(cx: &EventContext) -> Option<CssAnimationId> {
    let entity = cx.resolve_entity_identifier(DOC_RUNTIME_TARGET_ID)?;
    cx.css_animations(entity).into_iter().next().map(|snapshot| snapshot.id)
}

fn runtime_snapshot_text(cx: &EventContext) -> String {
    let Some(entity) = cx.resolve_entity_identifier(DOC_RUNTIME_TARGET_ID) else {
        return "Animation not mounted yet".to_string();
    };
    let Some(snapshot) = cx.css_animations(entity).into_iter().next() else {
        return "No active CSS animation occurrence".to_string();
    };
    let progress = snapshot
        .progress
        .map(|value| format!("{:.0}%", value * 100.0))
        .unwrap_or_else(|| "—".to_string());
    format!(
        "id={}  ·  {:?}  ·  {:.2}s  ·  {}  ·  {:.2}×",
        snapshot.id.get(),
        snapshot.state,
        snapshot.current_time,
        progress,
        snapshot.playback_rate
    )
}

fn simple_stage(cx: &mut Context, label: &'static str, class: &'static str) {
    HStack::new(cx, move |cx| {
        Label::new(cx, label).class("animation-doc-target").class(class);
    })
    .class("animation-doc-stage")
    .alignment(Alignment::Center);
}

fn surface_stage(cx: &mut Context, label: &'static str, class: &'static str) {
    HStack::new(cx, move |cx| {
        Label::new(cx, label)
            .class("animation-doc-target")
            .class("animation-doc-surface-target")
            .class(class);
    })
    .class("animation-doc-stage")
    .alignment(Alignment::Center);
}

fn motion_track(cx: &mut Context, class: &'static str) {
    ZStack::new(cx, move |cx| {
        Element::new(cx).class("animation-doc-track-line");
        Element::new(cx).class("animation-doc-dot").class(class);
    })
    .class("animation-doc-track");
}

fn render_scroll_preview(cx: &mut Context) {
    ScrollView::new(cx, |cx| {
        VStack::new(cx, |cx| {
            Label::new(cx, "Scroll inside this result").class("animation-doc-hint");
            Element::new(cx).class("animation-doc-scroll-spacer");
            Label::new(cx, "SCROLL TIMELINE").class("animation-doc-scroll-subject");
            Element::new(cx).class("animation-doc-scroll-spacer");
            Label::new(cx, "End").class("animation-doc-hint");
        })
        .class("animation-doc-scroll-content");
    })
    .timeline_name("--docs-scroll")
    .show_horizontal_scrollbar(false)
    .show_vertical_scrollbar(false)
    .class("animation-doc-scrollview");
}

fn render_view_preview(cx: &mut Context) {
    ScrollView::new(cx, |cx| {
        VStack::new(cx, |cx| {
            Label::new(cx, "approach").class("animation-doc-hint");
            Element::new(cx).class("animation-doc-view-spacer");
            Label::new(cx, "VIEW TIMELINE").class("animation-doc-view-subject");
            Element::new(cx).class("animation-doc-view-spacer");
            Label::new(cx, "depart").class("animation-doc-hint");
        })
        .class("animation-doc-scroll-content");
    })
    .show_horizontal_scrollbar(false)
    .show_vertical_scrollbar(false)
    .class("animation-doc-scrollview");
}

fn render_runtime_preview(cx: &mut Context) {
    let readout =
        Signal::new("Use the controls, then inspect the stable occurrence snapshot.".to_string());
    let seek = Signal::new(0.0_f32);
    VStack::new(cx, move |cx| {
        HStack::new(cx, |cx| {
            Label::new(cx, "RUNTIME")
                .id(DOC_RUNTIME_TARGET_ID)
                .class("animation-doc-target")
                .class("animation-doc-runtime-target");
        })
        .class("animation-doc-stage")
        .alignment(Alignment::Center);
        HStack::new(cx, move |cx| {
            Button::new(cx, |cx| Label::new(cx, "Pause")).on_press(move |cx| {
                if let Some(id) = runtime_animation_id(cx) {
                    let _ = cx.pause_css_animation(id);
                }
                readout.set(runtime_snapshot_text(cx));
            });
            Button::new(cx, |cx| Label::new(cx, "Resume"))
                .variant(ButtonVariant::Secondary)
                .on_press(move |cx| {
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.resume_css_animation(id);
                    }
                    readout.set(runtime_snapshot_text(cx));
                });
            Button::new(cx, |cx| Label::new(cx, "Reverse"))
                .variant(ButtonVariant::Outline)
                .on_press(move |cx| {
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.reverse_css_animation(id);
                    }
                    readout.set(runtime_snapshot_text(cx));
                });
            Button::new(cx, |cx| Label::new(cx, "2×")).variant(ButtonVariant::Text).on_press(
                move |cx| {
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.set_css_animation_playback_rate(id, 2.0);
                    }
                    readout.set(runtime_snapshot_text(cx));
                },
            );
        })
        .class("animation-doc-controls");
        HStack::new(cx, move |cx| {
            Label::new(cx, "Seek").class("animation-doc-control-label");
            Slider::new(cx, seek)
                .on_change(move |cx, value| {
                    seek.set(value);
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.seek_css_animation(id, value * DOC_RUNTIME_DURATION);
                    }
                    readout.set(runtime_snapshot_text(cx));
                })
                .width(Stretch(1.0));
        })
        .class("animation-doc-seek-row");
        Label::new(cx, readout).class("animation-doc-runtime-readout");
    })
    .class("animation-doc-runtime");
}

fn render_popover_preview(cx: &mut Context) {
    let open = Signal::new(false);
    HStack::new(cx, move |cx| {
        Button::new(cx, |cx| Label::new(cx, "Open popover")).on_press(move |_cx| open.set(true));
        Binding::new(cx, open, move |cx| {
            if open.get() {
                Popover::new(cx, move |cx| {
                    VStack::new(cx, |cx| {
                        Label::new(cx, "Blur reveal").class("animation-doc-popover-title");
                        Label::new(cx, "Native Popover + CSS @keyframes")
                            .class("animation-doc-popover-copy");
                        Button::new(cx, |cx| Label::new(cx, "Close"))
                            .variant(ButtonVariant::Secondary)
                            .on_press(move |_cx| open.set(false));
                    })
                    .class("animation-doc-popover-content");
                })
                .class("animation-doc-popover")
                .on_blur(move |_cx| open.set(false))
                .placement(Placement::BottomStart)
                .show_arrow(false);
            }
        });
    })
    .class("animation-doc-stage")
    .alignment(Alignment::Center);
}

fn render_throbber_preview(cx: &mut Context) {
    HStack::new(cx, |cx| {
        Label::new(cx, "Thinking").class("animation-doc-throbber-label");
        for class in
            ["animation-doc-throbber-a", "animation-doc-throbber-b", "animation-doc-throbber-c"]
        {
            Element::new(cx).class("animation-doc-throbber-dot").class(class);
        }
    })
    .class("animation-doc-stage")
    .alignment(Alignment::Center);
}

fn render_preview(cx: &mut Context, example: ExampleKind) {
    match example {
        ExampleKind::Motion => motion_track(cx, "animation-doc-motion"),
        ExampleKind::Duration => motion_track(cx, "animation-doc-duration"),
        ExampleKind::Delay => motion_track(cx, "animation-doc-delay"),
        ExampleKind::Steps => motion_track(cx, "animation-doc-steps"),
        ExampleKind::Iterations => motion_track(cx, "animation-doc-iterations"),
        ExampleKind::Direction => motion_track(cx, "animation-doc-direction"),
        ExampleKind::FillMode => simple_stage(cx, "FORWARDS", "animation-doc-fill-mode"),
        ExampleKind::Paused => motion_track(cx, "animation-doc-paused"),
        ExampleKind::Composition => simple_stage(cx, "ADD", "animation-doc-composition"),
        ExampleKind::DocumentTimeline => motion_track(cx, "animation-doc-document"),
        ExampleKind::ScrollTimeline => render_scroll_preview(cx),
        ExampleKind::ViewTimeline => render_view_preview(cx),
        ExampleKind::PercentageKeyframes => motion_track(cx, "animation-doc-percentage"),
        ExampleKind::Multiple => simple_stage(cx, "TWO ANIMATIONS", "animation-doc-multiple"),
        ExampleKind::Opacity => simple_stage(cx, "opacity", "animation-doc-opacity"),
        ExampleKind::Transform => simple_stage(cx, "transform", "animation-doc-transform"),
        ExampleKind::TransformOrigin => {
            simple_stage(cx, "origin", "animation-doc-transform-origin")
        }
        ExampleKind::Translate => simple_stage(cx, "translate", "animation-doc-translate"),
        ExampleKind::Rotate => simple_stage(cx, "rotate", "animation-doc-rotate"),
        ExampleKind::Scale => simple_stage(cx, "scale", "animation-doc-scale"),
        ExampleKind::ClipPath => simple_stage(cx, "clip-path", "animation-doc-clip"),
        ExampleKind::Filter => simple_stage(cx, "FILTER", "animation-doc-filter"),
        ExampleKind::BackdropFilter => {
            ZStack::new(cx, |cx| {
                Element::new(cx)
                    .class("animation-doc-backdrop-blob")
                    .class("animation-doc-backdrop-a");
                Element::new(cx)
                    .class("animation-doc-backdrop-blob")
                    .class("animation-doc-backdrop-b");
                Element::new(cx)
                    .class("animation-doc-backdrop-blob")
                    .class("animation-doc-backdrop-c");
                Label::new(cx, "SHARP  CONTENT").class("animation-doc-backdrop-behind-text");
                VStack::new(cx, |cx| {
                    Label::new(cx, "BACKDROP FILTER").class("animation-doc-backdrop-title");
                    Label::new(cx, "blur() over moving content")
                        .class("animation-doc-backdrop-copy");
                })
                .class("animation-doc-backdrop-glass");
            })
            .class("animation-doc-backdrop-stage");
        }
        ExampleKind::BackgroundColor => {
            surface_stage(cx, "background", "animation-doc-background-color")
        }
        ExampleKind::BackgroundGeometry => {
            surface_stage(cx, "background geometry", "animation-doc-background-geometry")
        }
        ExampleKind::BorderWidth => surface_stage(cx, "border width", "animation-doc-border-width"),
        ExampleKind::BorderColor => surface_stage(cx, "border color", "animation-doc-border-color"),
        ExampleKind::CornerRadius => surface_stage(cx, "radius", "animation-doc-radius"),
        ExampleKind::Outline => surface_stage(cx, "outline", "animation-doc-outline"),
        ExampleKind::Shadow => surface_stage(cx, "shadow", "animation-doc-shadow"),
        ExampleKind::TextColor => surface_stage(cx, "Animated text", "animation-doc-text-color"),
        ExampleKind::FontSize => surface_stage(cx, "Font size", "animation-doc-font-size"),
        ExampleKind::LetterSpacing => surface_stage(cx, "Spacing", "animation-doc-letter-spacing"),
        ExampleKind::LineHeight => {
            VStack::new(cx, |cx| {
                Label::new(cx, "First line\nSecond line").class("animation-doc-line-height");
            })
            .class("animation-doc-stage")
            .alignment(Alignment::Center);
        }
        ExampleKind::TextPaint => surface_stage(cx, "Text paint", "animation-doc-text-paint"),
        ExampleKind::Fill => {
            HStack::new(cx, |cx| {
                Svg::new(cx, ICON_HEART).class("animation-doc-fill-icon");
            })
            .class("animation-doc-stage")
            .alignment(Alignment::Center);
        }
        ExampleKind::Position => {
            ZStack::new(cx, |cx| {
                Element::new(cx).class("animation-doc-position");
            })
            .class("animation-doc-stage");
        }
        ExampleKind::Padding => simple_stage(cx, "padding", "animation-doc-padding"),
        ExampleKind::Gap => {
            HStack::new(cx, |cx| {
                Element::new(cx).class("animation-doc-gap-item");
                Element::new(cx).class("animation-doc-gap-item");
                Element::new(cx).class("animation-doc-gap-item");
            })
            .class("animation-doc-stage")
            .class("animation-doc-gap-stage")
            .alignment(Alignment::Center);
        }
        ExampleKind::Size => simple_stage(cx, "size", "animation-doc-size"),
        ExampleKind::Constraints => simple_stage(cx, "constraints", "animation-doc-constraints"),
        ExampleKind::Display => {
            HStack::new(cx, |cx| {
                Label::new(cx, "discrete display").class("animation-doc-display");
            })
            .class("animation-doc-stage")
            .alignment(Alignment::Center);
        }
        ExampleKind::StaticInfo => {
            VStack::new(cx, |cx| { Label::new(cx, "Typed custom properties use the same stores").class("animation-doc-static-title"); Label::new(cx, "color · length · font-size · letter-spacing · line-height · units · opacity · shadow").class("animation-doc-static-copy"); }).class("animation-doc-stage").alignment(Alignment::Center);
        }
        ExampleKind::Runtime => render_runtime_preview(cx),
        ExampleKind::Popover => render_popover_preview(cx),
        ExampleKind::Throbber => render_throbber_preview(cx),
    }
}

fn render_doc_content(cx: &mut Context, index: usize) {
    let doc = &DOCS[index];
    VStack::new(cx, move |cx| {
        Label::new(cx, doc.title).class("animation-doc-title");
        Label::new(cx, doc.description).class("animation-doc-description");

        HStack::new(cx, move |cx| {
            VStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "CSS").class("animation-doc-pane-title");
                })
                .class("animation-doc-code-header");

                VStack::new(cx, move |cx| {
                    Label::new(cx, doc.css)
                        .class("animation-doc-code")
                        .text_wrap(true);
                    Element::new(cx).height(Stretch(1.0));
                    HStack::new(cx, move |cx| {
                        Element::new(cx).width(Stretch(1.0));
                        Button::new(cx, |cx| Label::new(cx, "Copy CSS"))
                            .variant(ButtonVariant::Outline)
                            .class("animation-doc-copy-button")
                            .on_press(move |cx| {
                                let _ = cx.set_clipboard(doc.css.to_string());
                            });
                    })
                    .class("animation-doc-copy-row");
                })
                .class("animation-doc-code-body")
                .alignment(Alignment::TopLeft);
            })
            .class("animation-doc-code-pane");

            VStack::new(cx, move |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "Result").class("animation-doc-pane-title");
                })
                .class("animation-doc-result-header");

                VStack::new(cx, move |cx| render_preview(cx, doc.example))
                    .class("animation-doc-result-body");
            })
            .class("animation-doc-result-pane");
        })
        .class("animation-doc-example");

        VStack::new(cx, |cx| {
            Label::new(cx, "Implementation note").class("animation-doc-note-title");
            Label::new(cx, "CSS animations are sampled directly through Vizia's existing AnimatableSet / AnimatableVarSet property stores. The documentation mounts only the selected live example, so browsing the catalogue does not keep unrelated animations running in the background.").class("animation-doc-note-copy");
        })
        .class("animation-doc-note");
    })
    .class("animation-doc-content");
}

fn build_doc_navigation(cx: &mut Context, selected: Signal<usize>) {
    ScrollView::new(cx, move |cx| {
        VStack::new(cx, move |cx| {
            Label::new(cx, "Animation reference").class("animation-doc-nav-title");
            let mut category: Option<&'static str> = None;
            for (index, doc) in DOCS.iter().enumerate() {
                if category != Some(doc.category) {
                    category = Some(doc.category);
                    Label::new(cx, doc.category).class("animation-doc-nav-category");
                }
                Button::new(cx, move |cx| Label::new(cx, doc.title))
                    .variant(ButtonVariant::Text)
                    .class("animation-doc-nav-item")
                    .toggle_class(
                        "animation-doc-nav-item-active",
                        selected.map(move |current| *current == index),
                    )
                    .on_press(move |_cx| selected.set(index));
            }
        })
        .class("animation-doc-nav");
    })
    .show_horizontal_scrollbar(false)
    .class("animation-doc-nav-scroll");
}

pub fn animation(cx: &mut Context) {
    let selected = Signal::new(0_usize);
    VStack::new(cx, move |cx| {
        VStack::new(cx, |cx| {
            Label::new(cx, "CSS Animations").class("panel-title");
            Label::new(cx, "Interactive reference for the CSS animation properties, timelines, runtime controls and every property family currently wired into Vizia's keyframe storage.").class("panel-description");
        }).class("animation-doc-intro");
        Divider::new(cx);
        HStack::new(cx, move |cx| {
            build_doc_navigation(cx, selected);
            Binding::new(cx, selected, move |cx| { render_doc_content(cx, selected.get()); });
        }).class("animation-doc-layout").alignment(Alignment::TopLeft);
    }).class("animation-doc-page");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn animation_gallery_stylesheet_loads() {
        let mut cx = Context::default();
        cx.add_stylesheet(include_style!("resources/themes/animation.css"))
            .expect("animation gallery stylesheet should parse");
    }
}
