use vizia::prelude::*;

const DEMOS: &[(&str, &str)] = &[
    (
        "Shorthand + delay + fill",
        "A large CSS card continuously fades, translates and scales. The shorthand also exercises a negative delay, alternate direction and fill mode.",
    ),
    (
        "Iterations + direction",
        "Green and orange travel on the same rail in opposite alternate directions so iteration and direction changes are immediately visible.",
    ),
    (
        "Steps easing",
        "The yellow marker jumps between discrete positions instead of gliding. The rail makes each steps() jump obvious.",
    ),
    (
        "Play state",
        "The green marker runs forever. The red marker uses the same keyframes but is frozen halfway with animation-play-state: paused.",
    ),
    (
        "Multiple animation composition",
        "Two named animations run on one card at different periods: motion/pulse plus color/radius morphing.",
    ),
    (
        "Layout invalidation",
        "The cyan block changes width and padding while the container gap changes. It uses stepped timing so the layout work is visible without relaying out the full gallery every frame.",
    ),
    (
        "Visual interpolation",
        "Background, text color, radius, border color and shadow morph continuously on the same surface.",
    ),
    (
        "Transform family",
        "The pink diamond translates, rotates and scales through three keyframes in a continuous loop.",
    ),
    (
        "Filter blur",
        "A high-contrast mini poster cycles from crisp to blurred and back using filter: blur().",
    ),
    (
        "Backdrop / GPU glass",
        "Moving neon blobs, stripes and text sit behind a glass panel while backdrop-filter continuously changes the blur radius.",
    ),
];

fn track(cx: &mut Context, class: &'static str) {
    ZStack::new(cx, move |cx| {
        Element::new(cx).class("animation-track-line");
        Element::new(cx).class("animation-orb").class(class);
    })
    .class("animation-track");
}

fn render_demo_visual(cx: &mut Context, index: usize) {
    match index {
        0 => {
            Label::new(cx, "CSS @KEYFRAMES")
                .class("animation-card")
                .class("css-animation-entrance");
        }
        1 => {
            VStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "alternate").class("animation-track-label");
                    track(cx, "css-animation-alternate");
                })
                .class("animation-track-row");
                HStack::new(cx, |cx| {
                    Label::new(cx, "alternate-reverse").class("animation-track-label");
                    track(cx, "css-animation-alternate-reverse");
                })
                .class("animation-track-row");
            })
            .class("animation-track-stack");
        }
        2 => {
            ZStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    for _ in 0..7 {
                        Element::new(cx).class("animation-step-marker");
                    }
                })
                .class("animation-step-grid");
                Element::new(cx).class("animation-step-cursor").class("css-animation-steps");
            })
            .class("animation-step-track");
        }
        3 => {
            VStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "RUNNING").class("animation-track-label");
                    track(cx, "css-animation-running");
                })
                .class("animation-track-row");
                HStack::new(cx, |cx| {
                    Label::new(cx, "PAUSED 50%").class("animation-track-label");
                    track(cx, "css-animation-paused");
                })
                .class("animation-track-row");
            })
            .class("animation-track-stack");
        }
        4 => {
            Label::new(cx, "2 ANIMATIONS").class("animation-card").class("css-animation-composed");
        }
        5 => {
            HStack::new(cx, |cx| {
                Element::new(cx).class("css-animation-layout-box");
                Element::new(cx).class("css-animation-layout-box-static");
            })
            .class("css-animation-layout-row");
        }
        6 => {
            Label::new(cx, "STYLE MORPH").class("animation-card").class("css-animation-style");
        }
        7 => {
            ZStack::new(cx, |cx| {
                Element::new(cx).class("animation-transform-guide");
                Element::new(cx).class("css-animation-transform");
            })
            .class("animation-transform-stage");
        }
        8 => {
            VStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    Element::new(cx).class("filter-stripe-a");
                    Element::new(cx).class("filter-stripe-b");
                    Element::new(cx).class("filter-stripe-c");
                    Element::new(cx).class("filter-stripe-d");
                })
                .class("filter-poster-stripes");
                Label::new(cx, "CRISP / BLUR").class("filter-poster-title");
            })
            .class("animation-filter-poster")
            .class("css-animation-filter");
        }
        9 => {
            ZStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    for i in 0..8 {
                        Element::new(cx).class(if i % 2 == 0 {
                            "backdrop-stripe-a"
                        } else {
                            "backdrop-stripe-b"
                        });
                    }
                })
                .class("animation-backdrop-stripes");

                Label::new(cx, "CSS  GPU  BLUR").class("animation-backdrop-copy");

                Element::new(cx).class("animation-gpu-orb").class("gpu-one");
                Element::new(cx).class("animation-gpu-orb").class("gpu-two");
                Element::new(cx).class("animation-gpu-orb").class("gpu-three");

                VStack::new(cx, |cx| {
                    Label::new(cx, "BACKDROP FILTER").class("glass-title");
                    Label::new(cx, "live glass over moving content").class("glass-subtitle");
                })
                .class("animation-backdrop-target")
                .class("css-animation-backdrop");
            })
            .class("animation-backdrop-scene");
        }
        _ => {}
    }
}

fn demo_row(cx: &mut Context, index: usize) -> Handle<'_, VStack> {
    let (title, description) = DEMOS[index];
    VStack::new(cx, move |cx| {
        HStack::new(cx, move |cx| {
            Label::new(cx, format!("{:02} · {}", index + 1, title)).class("animation-demo-title");
            Label::new(cx, "LIVE").class("animation-live-badge");
        })
        .class("animation-demo-header");

        Label::new(cx, description).class("animation-demo-description");

        HStack::new(cx, move |cx| render_demo_visual(cx, index))
            .class("animation-stage")
            .alignment(Alignment::Center);
    })
    .class("animation-demo-card")
}

pub fn animation(cx: &mut Context) {
    let demos = Signal::new((0..DEMOS.len()).collect::<Vec<_>>());

    VStack::new(cx, move |cx| {
        Label::new(cx, "CSS Animations Level 1 — Live").class("panel-title");
        Label::new(
            cx,
            "The real demos are virtualized below: only visible rows are mounted and animated. Every running example loops forever using CSS @keyframes + animation-* only.",
        )
        .class("panel-description");

        HStack::new(cx, |cx| {
            Label::new(cx, "10 live demos").class("animation-summary-pill");
            Label::new(cx, "VirtualList keeps off-screen animations asleep")
                .class("animation-summary-text");
        })
        .class("animation-summary");

        VirtualList::new(cx, demos, 292.0, |cx, index, _item| demo_row(cx, index))
            .class("animation-live-list")
            .width(Stretch(1.0))
            .height(Pixels(600.0));
    })
    .class("panel")
    .max_width(Pixels(820.0));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn animation_gallery_stylesheet_loads() {
        let mut cx = Context::default();
        cx.add_stylesheet(include_style!("resources/themes/animation.css"))
            .expect("animation gallery stylesheet should parse and load");
    }

    #[test]
    fn gallery_contains_all_level_one_demos() {
        assert_eq!(DEMOS.len(), 10);
    }
}
