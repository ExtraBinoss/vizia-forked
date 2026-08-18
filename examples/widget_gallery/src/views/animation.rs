use vizia::prelude::*;

use crate::DemoRegion;

const ENTRANCE_ANIMATION: &str = "gallery-entrance";
const ENTRANCE_TARGET: &str = "gallery-entrance-target";
const STYLE_ANIMATION: &str = "gallery-style";
const STYLE_TARGET: &str = "gallery-style-target";
const MOTION_ANIMATION: &str = "gallery-motion";
const MOTION_TARGET: &str = "gallery-motion-target";
const FILTER_ANIMATION: &str = "gallery-filter-reveal";
const FILTER_TARGET: &str = "gallery-filter-target";
const BACKDROP_ANIMATION: &str = "gallery-backdrop-reveal";
const BACKDROP_TARGET: &str = "gallery-backdrop-target";

fn replay_button(cx: &mut Context, animation: &'static str, target: &'static str) {
    Button::new(cx, |cx| Label::new(cx, "Replay")).on_press(move |cx| {
        cx.play_animation_for(animation, target, Duration::from_millis(700), Duration::default())
    });
}

fn animation_demo(
    cx: &mut Context,
    title: &'static str,
    animation: &'static str,
    target: &'static str,
    content: impl Fn(&mut Context) + Copy + 'static,
) {
    DemoRegion::new(cx, title, move |cx| {
        VStack::new(cx, move |cx| {
            HStack::new(cx, content).class("animation-stage").alignment(Alignment::Center);
            replay_button(cx, animation, target);
        })
        .class("animation-demo")
        .height(Auto)
        .width(Stretch(1.0));
    });
}

pub fn animation(cx: &mut Context) {
    VStack::new(cx, |cx| {
        Label::new(cx, "Animation").class("panel-title");
        Label::new(
            cx,
            "Replayable CSS keyframes covering transforms, style interpolation, motion, and GPU filters.",
        )
        .class("panel-description");

        Divider::new(cx);

        animation_demo(cx, "Entrance", ENTRANCE_ANIMATION, ENTRANCE_TARGET, |cx| {
            Label::new(cx, "Hello, Vizia")
                .id(ENTRANCE_TARGET)
                .class("animation-card");
        });

        animation_demo(cx, "Style interpolation", STYLE_ANIMATION, STYLE_TARGET, |cx| {
            Label::new(cx, "Color + radius")
                .id(STYLE_TARGET)
                .class("animation-card animation-style-target");
        });

        animation_demo(cx, "Multi-keyframe motion", MOTION_ANIMATION, MOTION_TARGET, |cx| {
            Element::new(cx).id(MOTION_TARGET).class("animation-orb");
        });

        animation_demo(cx, "Filter blur reveal", FILTER_ANIMATION, FILTER_TARGET, |cx| {
            Label::new(cx, "Sharp focus")
                .id(FILTER_TARGET)
                .class("animation-card animation-filter-target");
        });

        animation_demo(
            cx,
            "Backdrop-filter reveal",
            BACKDROP_ANIMATION,
            BACKDROP_TARGET,
            |cx| {
                ZStack::new(cx, |cx| {
                    HStack::new(cx, |cx| {
                        Element::new(cx).class("animation-backdrop-swatch swatch-one");
                        Element::new(cx).class("animation-backdrop-swatch swatch-two");
                        Element::new(cx).class("animation-backdrop-swatch swatch-three");
                    })
                    .size(Stretch(1.0));

                    Label::new(cx, "GPU glass")
                        .id(BACKDROP_TARGET)
                        .class("animation-backdrop-target");
                })
                .class("animation-backdrop-scene");
            },
        );
    })
    .class("panel");
}
