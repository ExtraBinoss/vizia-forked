use vizia::prelude::*;

use crate::DemoRegion;

fn css_animation_demo(
    cx: &mut Context,
    title: &'static str,
    description: &'static str,
    content: impl Fn(&mut Context) + Copy + 'static,
) {
    DemoRegion::new(cx, title, move |cx| {
        VStack::new(cx, move |cx| {
            Label::new(cx, description).class("animation-demo-description");
            HStack::new(cx, content).class("animation-stage").alignment(Alignment::Center);
        })
        .class("animation-demo")
        .height(Auto)
        .width(Stretch(1.0));
    });
}

pub fn animation(cx: &mut Context) {
    VStack::new(cx, |cx| {
        Label::new(cx, "CSS Animations Level 1").class("panel-title");
        Label::new(
            cx,
            "Declarative @keyframes demos. No Rust play_animation_for calls are used on this page.",
        )
        .class("panel-description");

        Divider::new(cx);

        css_animation_demo(
            cx,
            "Shorthand + delay + fill",
            "animation shorthand, negative delay and backwards/forwards fill behavior.",
            |cx| {
                Label::new(cx, "CSS entrance")
                    .class("animation-card css-animation-entrance");
            },
        );

        css_animation_demo(
            cx,
            "Iterations + direction",
            "Fractional/infinite iteration counts with alternate and alternate-reverse directions.",
            |cx| {
                HStack::new(cx, |cx| {
                    Element::new(cx).class("animation-orb css-animation-alternate");
                    Element::new(cx).class("animation-orb css-animation-alternate-reverse");
                })
                .class("animation-row");
            },
        );

        css_animation_demo(
            cx,
            "Steps easing",
            "steps(), step-start and per-keyframe timing-function discontinuities.",
            |cx| {
                Element::new(cx).class("animation-orb css-animation-steps");
            },
        );

        css_animation_demo(
            cx,
            "Paused play state",
            "animation-play-state: paused freezes both delay and active time.",
            |cx| {
                Label::new(cx, "Paused at negative delay")
                    .class("animation-card css-animation-paused");
            },
        );

        css_animation_demo(
            cx,
            "Multiple animation composition",
            "Two named animations run concurrently; the later animation wins when both target opacity.",
            |cx| {
                Label::new(cx, "pulse + color")
                    .class("animation-card css-animation-composed");
            },
        );

        css_animation_demo(
            cx,
            "Layout invalidation",
            "width, gap and padding keyframes exercise relayout while paint-only properties stay redraw-only.",
            |cx| {
                HStack::new(cx, |cx| {
                    Element::new(cx).class("css-animation-layout-box");
                    Element::new(cx).class("css-animation-layout-box static");
                })
                .class("css-animation-layout-row");
            },
        );

        css_animation_demo(
            cx,
            "Visual interpolation",
            "background color, corner radius, border, shadow and text color interpolate together.",
            |cx| {
                Label::new(cx, "style interpolation")
                    .class("animation-card css-animation-style");
            },
        );

        css_animation_demo(
            cx,
            "Transform family",
            "translate, rotate and scale animate independently across multiple keyframes.",
            |cx| {
                Element::new(cx).class("animation-orb css-animation-transform");
            },
        );

        css_animation_demo(
            cx,
            "Filter list interpolation",
            "Compatible blur() lists interpolate continuously; incompatible lists fall back discretely.",
            |cx| {
                Label::new(cx, "Sharp focus")
                    .class("animation-card css-animation-filter");
            },
        );

        css_animation_demo(
            cx,
            "Backdrop filter",
            "Backdrop blur shares the same CSS animation timing and invalidation path.",
            |cx| {
                ZStack::new(cx, |cx| {
                    HStack::new(cx, |cx| {
                        Element::new(cx).class("animation-backdrop-swatch swatch-one");
                        Element::new(cx).class("animation-backdrop-swatch swatch-two");
                        Element::new(cx).class("animation-backdrop-swatch swatch-three");
                    })
                    .size(Stretch(1.0));

                    Label::new(cx, "GPU glass")
                        .class("animation-backdrop-target css-animation-backdrop");
                })
                .class("animation-backdrop-scene");
            },
        );
    })
    .class("panel");
}
