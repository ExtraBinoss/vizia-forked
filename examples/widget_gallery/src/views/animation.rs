use vizia::prelude::*;

const RUNTIME_TARGET_ID: &str = "l2-runtime-target";
const RUNTIME_DURATION: f32 = 10.0;

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
        "Two named Level 1 animations run on one card at different periods: motion/pulse plus color/radius morphing.",
    ),
    (
        "Layout invalidation",
        "The cyan block changes width and padding while the container gap changes. Stepped timing makes the relayouts visible without doing redundant layout work between steps.",
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
            Label::new(cx, "LEVEL 1 · LIVE").class("animation-live-badge");
        })
        .class("animation-demo-header");
        Label::new(cx, description).class("animation-demo-description");
        HStack::new(cx, move |cx| render_demo_visual(cx, index))
            .class("animation-stage")
            .alignment(Alignment::Center);
    })
    .class("animation-demo-card")
}

fn runtime_animation_id(cx: &EventContext) -> Option<CssAnimationId> {
    let entity = cx.resolve_entity_identifier(RUNTIME_TARGET_ID)?;
    cx.css_animations(entity).into_iter().next().map(|snapshot| snapshot.id)
}

fn runtime_snapshot_text(cx: &EventContext) -> String {
    let Some(entity) = cx.resolve_entity_identifier(RUNTIME_TARGET_ID) else {
        return "runtime target is not mounted".to_string();
    };
    let Some(snapshot) = cx.css_animations(entity).into_iter().next() else {
        return "CANCELLED · no CSS animation occurrence is active".to_string();
    };
    let progress = snapshot
        .progress
        .map(|value| format!("{:.0}%", value * 100.0))
        .unwrap_or_else(|| "none".to_string());
    format!(
        "id={} · {:?} · t={:.2}s · progress={} · rate={:.2}x · timeline={}",
        snapshot.id.get(),
        snapshot.state,
        snapshot.current_time,
        progress,
        snapshot.playback_rate,
        if snapshot.timeline_driven { "progress" } else { "document" }
    )
}

fn refresh_runtime_readout(cx: &EventContext, readout: Signal<String>) {
    readout.set(runtime_snapshot_text(cx));
}

fn level_two_composition(cx: &mut Context) {
    VStack::new(cx, |cx| {
        HStack::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "REPLACE").class("l2-mini-title");
                Label::new(cx, "The second translate effect wins.").class("l2-mini-copy");
                ZStack::new(cx, |cx| {
                    Element::new(cx).class("l2-axis-x");
                    Element::new(cx).class("l2-axis-y");
                    Element::new(cx).class("l2-composition-orb").class("l2-replace-orb");
                })
                .class("l2-composition-stage");
            })
            .class("l2-composition-cell");

            VStack::new(cx, |cx| {
                Label::new(cx, "ADD").class("l2-mini-title");
                Label::new(cx, "Both translate effects compose into 2D motion.").class("l2-mini-copy");
                ZStack::new(cx, |cx| {
                    Element::new(cx).class("l2-axis-x");
                    Element::new(cx).class("l2-axis-y");
                    Element::new(cx).class("l2-composition-orb").class("l2-add-orb");
                })
                .class("l2-composition-stage");
            })
            .class("l2-composition-cell");
        })
        .class("l2-composition-row");

        HStack::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "ACCUMULATE").class("l2-mini-title");
                Label::new(
                    cx,
                    "Two rotate effects accumulate on the same property while a separate scale pulse keeps the card alive.",
                )
                .class("l2-mini-copy");
                ZStack::new(cx, |cx| {
                    Element::new(cx).class("l2-accumulate-ring");
                    Label::new(cx, "A + B").class("l2-accumulate-card");
                })
                .class("l2-accumulate-stage");
            })
            .class("l2-composition-cell")
            .width(Stretch(1.0));
        });
    })
    .class("l2-composition-content");
}

fn level_two_timelines(cx: &mut Context) {
    VStack::new(cx, |cx| {
        VStack::new(cx, |cx| {
            HStack::new(cx, |cx| {
                VStack::new(cx, |cx| {
                    Label::new(cx, "NAMED SCROLL TIMELINE").class("l2-mini-title");
                    Label::new(
                        cx,
                        "Scroll this large viewport. The card and progress marker are sampled from --l2-gallery-scroll, not from wall-clock time.",
                    )
                    .class("l2-mini-copy");
                })
                .width(Stretch(1.0));
                Label::new(cx, "SCROLL ME").class("l2-action-badge");
            });

            ZStack::new(cx, |cx| {
                Element::new(cx).class("l2-progress-track");
                Element::new(cx).class("l2-progress-dot").class("l2-scroll-progress-dot");
            })
            .class("l2-progress-stage");

            ScrollView::new(cx, |cx| {
                VStack::new(cx, |cx| {
                    Label::new(cx, "0% · source start").class("l2-scroll-caption");
                    Element::new(cx).class("l2-scroll-spacer");
                    Label::new(cx, "SCROLL DRIVEN").class("l2-scroll-subject");
                    Element::new(cx).class("l2-scroll-spacer");
                    Label::new(cx, "100% · source end").class("l2-scroll-caption");
                })
                .class("l2-scroll-content");
            })
            .timeline_name("--l2-gallery-scroll")
            .show_horizontal_scrollbar(false)
            .class("l2-timeline-scroll");
        })
        .class("l2-timeline-lab");

        VStack::new(cx, |cx| {
            HStack::new(cx, |cx| {
                VStack::new(cx, |cx| {
                    Label::new(cx, "VIEW PROGRESS").class("l2-mini-title");
                    Label::new(
                        cx,
                        "The subject animates as it enters and exits this viewport. Stop scrolling and the effect stops instantly.",
                    )
                    .class("l2-mini-copy");
                })
                .width(Stretch(1.0));
                Label::new(cx, "VIEW() TIMELINE").class("l2-action-badge");
            });

            ScrollView::new(cx, |cx| {
                VStack::new(cx, |cx| {
                    for index in 0..3 {
                        Label::new(cx, format!("approach / {}", index + 1)).class("l2-view-filler");
                    }
                    Label::new(cx, "VIEW PROGRESS SUBJECT").class("l2-view-subject");
                    for index in 0..3 {
                        Label::new(cx, format!("depart / {}", index + 1)).class("l2-view-filler");
                    }
                })
                .class("l2-view-content");
            })
            .show_horizontal_scrollbar(false)
            .class("l2-timeline-scroll")
            .class("l2-view-scroll");
        })
        .class("l2-timeline-lab");
    })
    .class("l2-timeline-content");
}

fn level_two_runtime(cx: &mut Context) {
    let readout = Signal::new(
        "Press Snapshot after the first frame · controls operate on the stable CSS occurrence ID"
            .to_string(),
    );
    let seek = Signal::new(0.0_f32);

    VStack::new(cx, move |cx| {
        ZStack::new(cx, |cx| {
            Element::new(cx).class("l2-runtime-grid");
            Label::new(cx, "RUNTIME CONTROL")
                .id(RUNTIME_TARGET_ID)
                .class("l2-runtime-target");
        })
        .class("l2-runtime-stage");

        Label::new(cx, readout).class("l2-runtime-readout");

        HStack::new(cx, move |cx| {
            Button::new(cx, |cx| Label::new(cx, "Snapshot")).on_press(move |cx| {
                refresh_runtime_readout(cx, readout);
            });
            Button::new(cx, |cx| Label::new(cx, "Pause")).on_press(move |cx| {
                if let Some(id) = runtime_animation_id(cx) {
                    let _ = cx.pause_css_animation(id);
                }
                refresh_runtime_readout(cx, readout);
            });
            Button::new(cx, |cx| Label::new(cx, "Resume")).on_press(move |cx| {
                if let Some(id) = runtime_animation_id(cx) {
                    let _ = cx.resume_css_animation(id);
                }
                refresh_runtime_readout(cx, readout);
            });
            Button::new(cx, |cx| Label::new(cx, "Reverse")).on_press(move |cx| {
                if let Some(id) = runtime_animation_id(cx) {
                    let _ = cx.reverse_css_animation(id);
                }
                refresh_runtime_readout(cx, readout);
            });
            Button::new(cx, |cx| Label::new(cx, "Finish")).on_press(move |cx| {
                if let Some(id) = runtime_animation_id(cx) {
                    let _ = cx.finish_css_animation(id);
                }
                refresh_runtime_readout(cx, readout);
            });
            Button::new(cx, |cx| Label::new(cx, "Cancel")).on_press(move |cx| {
                if let Some(id) = runtime_animation_id(cx) {
                    let _ = cx.cancel_css_animation(id);
                }
                refresh_runtime_readout(cx, readout);
            });
        })
        .class("l2-runtime-controls");

        HStack::new(cx, move |cx| {
            Label::new(cx, "Seek").class("l2-control-label");
            Slider::new(cx, seek)
                .on_change(move |cx, value| {
                    seek.set(value);
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.seek_css_animation(id, value * RUNTIME_DURATION);
                    }
                    refresh_runtime_readout(cx, readout);
                })
                .class("l2-seek-slider");
            Label::new(cx, seek.map(|value| format!("{:.0}%", value * 100.0)))
                .class("l2-seek-value");
        })
        .class("l2-seek-row");

        HStack::new(cx, move |cx| {
            Label::new(cx, "Playback rate").class("l2-control-label");
            for (label, rate) in [("0.5×", 0.5_f32), ("1×", 1.0_f32), ("2×", 2.0_f32)] {
                Button::new(cx, move |cx| Label::new(cx, label)).on_press(move |cx| {
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.set_css_animation_playback_rate(id, rate);
                    }
                    refresh_runtime_readout(cx, readout);
                });
            }
        })
        .class("l2-runtime-controls");

        Label::new(
            cx,
            "Cancel intentionally removes this occurrence. Reload/re-enter the Animation page to create a fresh CSS occurrence after testing cancel.",
        )
        .class("l2-runtime-note");
    })
    .class("l2-runtime-content");
}

pub fn animation(cx: &mut Context) {
    VStack::new(cx, |cx| {
        VStack::new(cx, |cx| {
            Label::new(cx, "CSS Animations — Level 1 + Level 2").class("panel-title");
            Label::new(
                cx,
                "The Animation gallery is now a full-size showcase. There is no nested 600px VirtualList: the app's normal page scroll owns the experience, and every stage has enough room to inspect the behavior.",
            )
            .class("panel-description");
            HStack::new(cx, |cx| {
                Label::new(cx, "LEVEL 2 LIVE").class("l2-hero-badge");
                Label::new(cx, "effect stacks · progress timelines · runtime control")
                    .class("animation-summary-text");
            })
            .class("animation-summary");
        })
        .class("l2-hero");

        VStack::new(cx, |cx| {
            Label::new(cx, "Level 2 · Effect stack & composition").class("l2-section-title");
            Label::new(
                cx,
                "Replace, add and accumulate are resolved inside the existing Vizia property stores. The side-by-side motion makes the effect-stack difference visible immediately.",
            )
            .class("l2-section-copy");
            level_two_composition(cx);
        })
        .class("l2-showcase-section");

        VStack::new(cx, |cx| {
            Label::new(cx, "Level 2 · Scroll & view timelines").class("l2-section-title");
            Label::new(
                cx,
                "These demos are intentionally large. Their progress is driven only by scrolling the local viewport, so stopping the gesture freezes the animation with no wall-clock drift.",
            )
            .class("l2-section-copy");
            level_two_timelines(cx);
        })
        .class("l2-showcase-section")
        .class("l2-timelines-section");

        VStack::new(cx, |cx| {
            Label::new(cx, "Level 2 · Runtime animation control").class("l2-section-title");
            Label::new(
                cx,
                "The controls below operate on the same CSS animation occurrence and the same AnimatableSet/AnimatableVarSet clocks that render the property values — no parallel animation manager.",
            )
            .class("l2-section-copy");
            level_two_runtime(cx);
        })
        .class("l2-showcase-section");

        VStack::new(cx, |cx| {
            Label::new(cx, "Level 1 baseline · full-size live stages").class("l2-section-title");
            Label::new(
                cx,
                "The Level 1 witnesses remain below for regression testing, but they now live directly in the page instead of inside a tiny nested list.",
            )
            .class("l2-section-copy");
            for index in 0..DEMOS.len() {
                demo_row(cx, index);
            }
        })
        .class("animation-level-one-stack");
    })
    .class("panel")
    .class("animation-page")
    .width(Stretch(1.0))
    .max_width(Pixels(1180.0));
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
