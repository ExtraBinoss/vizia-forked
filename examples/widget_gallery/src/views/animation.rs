use vizia::prelude::*;

use crate::DemoRegion;

const ANIMATION_FEATURES: &[&str] = &[
    "01 · Shorthand + negative delay + fill mode",
    "02 · Infinite iterations + alternate directions",
    "03 · steps() easing",
    "04 · running vs animation-play-state: paused",
    "05 · Multiple named animations on one entity",
    "06 · Layout invalidation: width + padding + gap",
    "07 · Color + radius + border + shadow interpolation",
    "08 · Translate + rotate + scale",
    "09 · filter: blur() interpolation",
    "10 · backdrop-filter blur over moving content",
];

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

fn feature_list(cx: &mut Context) {
    let features = Signal::new(
        ANIMATION_FEATURES
            .iter()
            .map(|feature| (*feature).to_string())
            .collect::<Vec<_>>(),
    );

    DemoRegion::new(cx, "Level 1 live matrix", move |cx| {
        VStack::new(cx, move |cx| {
            Label::new(
                cx,
                "Everything below is CSS-driven and loops continuously. This VirtualList is the index of what should be visibly working.",
            )
            .class("animation-demo-description");

            VirtualList::new(cx, features, 44.0, |cx, _index, item| {
                Label::new(cx, item).class("animation-feature-row")
            })
            .class("animation-feature-list")
            .width(Stretch(1.0));
        })
        .height(Auto)
        .width(Stretch(1.0));
    });
}

pub fn animation(cx: &mut Context) {
    cx.add_stylesheet(include_style!("resources/themes/animation.css"))
        .expect("Failed to add CSS Animations Level 1 gallery stylesheet");

    VStack::new(cx, |cx| {
        Label::new(cx, "CSS Animations Level 1 — Live").class("panel-title");
        Label::new(
            cx,
            "All running examples loop forever using CSS @keyframes + animation-* only. No Rust play_animation_for calls drive this page.",
        )
        .class("panel-description");

        Divider::new(cx);
        feature_list(cx);

        css_animation_demo(
            cx,
            "Shorthand + delay + fill",
            "A single animation: shorthand contains duration, easing, negative delay, infinite iterations, alternate direction, fill and running state.",
            |cx| {
                Label::new(cx, "CSS ONLY")
                    .class("animation-card css-animation-entrance");
            },
        );

        css_animation_demo(
            cx,
            "Iterations + direction",
            "Green uses alternate; orange uses alternate-reverse. Both run forever so direction changes are obvious.",
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
            "The yellow orb jumps in six discrete steps instead of moving continuously.",
            |cx| {
                Element::new(cx).class("animation-orb css-animation-steps");
            },
        );

        css_animation_demo(
            cx,
            "Play state",
            "Green is running continuously. Red is the same animation frozen halfway using a -500ms delay + animation-play-state: paused.",
            |cx| {
                VStack::new(cx, |cx| {
                    HStack::new(cx, |cx| {
                        Label::new(cx, "RUNNING").width(Pixels(80.0));
                        HStack::new(cx, |cx| {
                            Element::new(cx).class("animation-orb css-animation-running");
                        })
                        .class("animation-play-state-track");
                    })
                    .height(Pixels(78.0));

                    HStack::new(cx, |cx| {
                        Label::new(cx, "PAUSED").width(Pixels(80.0));
                        HStack::new(cx, |cx| {
                            Element::new(cx).class("animation-orb css-animation-paused");
                        })
                        .class("animation-play-state-track");
                    })
                    .height(Pixels(78.0));
                })
                .width(Stretch(1.0))
                .height(Auto);
            },
        );

        css_animation_demo(
            cx,
            "Multiple animation composition",
            "Two named animations run on the same entity at different periods: pulse/motion plus color/radius.",
            |cx| {
                Label::new(cx, "2 ANIMATIONS")
                    .class("animation-card css-animation-composed");
            },
        );

        css_animation_demo(
            cx,
            "Layout invalidation",
            "The cyan box continuously changes width/padding while the row changes gap. The gray box stays fixed so relayout is easy to see.",
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
            "Background, text color, corner radius, border width/color and shadow all interpolate continuously.",
            |cx| {
                Label::new(cx, "STYLE MORPH")
                    .class("animation-card css-animation-style");
            },
        );

        css_animation_demo(
            cx,
            "Transform family",
            "The pink square continuously translates, rotates and scales through three keyframes.",
            |cx| {
                Element::new(cx).class("css-animation-transform");
            },
        );

        css_animation_demo(
            cx,
            "Filter blur",
            "This card visibly cycles between heavily blurred and sharp using filter: blur().",
            |cx| {
                Label::new(cx, "BLUR → SHARP → BLUR")
                    .class("animation-card css-animation-filter");
            },
        );

        css_animation_demo(
            cx,
            "Backdrop / GPU glass",
            "Three bright blobs move constantly behind the glass plate while backdrop-filter cycles between clear and strongly blurred.",
            |cx| {
                ZStack::new(cx, |cx| {
                    Element::new(cx).class("animation-gpu-orb one");
                    Element::new(cx).class("animation-gpu-orb two");
                    Element::new(cx).class("animation-gpu-orb three");

                    Label::new(cx, "LIVE BACKDROP BLUR")
                        .class("animation-backdrop-target css-animation-backdrop");
                })
                .class("animation-backdrop-scene");
            },
        );
    })
    .class("panel");
}
