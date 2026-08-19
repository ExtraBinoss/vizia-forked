from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


# Runtime controls must be able to revive a filled/finished effect when seeking or reversing it.
for store in [
    "crates/vizia_core/src/storage/animatable_set.rs",
    "crates/vizia_core/src/storage/animatable_var_set.rs",
]:
    replace_once(
        store,
        '''                if let Some(clock) = state.css_clock.as_mut() {
                    found |= clock.apply_control(control, now);
                }
''',
        '''                if let Some(clock) = state.css_clock.as_mut() {
                    let applied = clock.apply_control(control, now);
                    if applied
                        && matches!(
                            control,
                            crate::animation::CssAnimationControl::Resume
                                | crate::animation::CssAnimationControl::Seek(_)
                                | crate::animation::CssAnimationControl::SetPlaybackRate(_)
                                | crate::animation::CssAnimationControl::Reverse
                        )
                    {
                        state.t = 0.0;
                    }
                    found |= applied;
                }
''',
    )

replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    '''            if matches!(control, CssAnimationControl::Resume | CssAnimationControl::Reverse) {
                instance.ended = false;
            }
''',
    '''            if matches!(
                control,
                CssAnimationControl::Resume
                    | CssAnimationControl::Seek(_)
                    | CssAnimationControl::SetPlaybackRate(_)
                    | CssAnimationControl::Reverse
            ) {
                instance.ended = false;
            }
''',
)

animation_rs = r'''use vizia::prelude::*;

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
'''

Path("examples/widget_gallery/src/views/animation.rs").write_text(animation_rs)

css_path = Path("examples/widget_gallery/resources/themes/animation.css")
css = css_path.read_text()
marker = "/* ===== CSS Animations Level 2 full-size showcase ===== */"
if marker not in css:
    css += r'''

/* ===== CSS Animations Level 2 full-size showcase ===== */

@keyframes l2-translate-x {
    0% { translate: -125px 0px; }
    100% { translate: 125px 0px; }
}

@keyframes l2-translate-y {
    0% { translate: 0px -62px; }
    100% { translate: 0px 62px; }
}

@keyframes l2-rotate-a {
    0% { rotate: -25deg; }
    100% { rotate: 205deg; }
}

@keyframes l2-rotate-b {
    0% { rotate: 0deg; }
    100% { rotate: 110deg; }
}

@keyframes l2-accumulate-pulse {
    0% { scale: 0.82; }
    100% { scale: 1.22; }
}

@keyframes l2-scroll-reveal {
    0% {
        translate: -250px 30px;
        rotate: -18deg;
        scale: 0.62;
        opacity: 0.18;
        background-color: #0ea5e9;
        corner-radius: 10px;
    }
    50% {
        translate: 0px -18px;
        rotate: 0deg;
        scale: 1.18;
        opacity: 1;
        background-color: #8b5cf6;
        corner-radius: 34px;
    }
    100% {
        translate: 250px 30px;
        rotate: 18deg;
        scale: 0.72;
        opacity: 0.32;
        background-color: #f97316;
        corner-radius: 12px;
    }
}

@keyframes l2-scroll-progress {
    0% { translate: -390px 0px; scale: 0.75; }
    100% { translate: 390px 0px; scale: 1.25; }
}

@keyframes l2-view-reveal {
    0% {
        opacity: 0.12;
        translate: -170px 35px;
        rotate: -22deg;
        scale: 0.62;
        background-color: #06b6d4;
    }
    50% {
        opacity: 1;
        translate: 0px -18px;
        rotate: 0deg;
        scale: 1.22;
        background-color: #a855f7;
    }
    100% {
        opacity: 0.18;
        translate: 170px 35px;
        rotate: 22deg;
        scale: 0.68;
        background-color: #f43f5e;
    }
}

@keyframes l2-runtime-motion {
    0% {
        translate: -330px 35px;
        rotate: -12deg;
        scale: 0.76;
        opacity: 0.45;
        background-color: #0ea5e9;
        corner-radius: 12px;
    }
    35% {
        translate: -70px -42px;
        rotate: 120deg;
        scale: 1.18;
        opacity: 1;
        background-color: #8b5cf6;
        corner-radius: 38px;
    }
    70% {
        translate: 170px 26px;
        rotate: 245deg;
        scale: 0.92;
        opacity: 0.72;
        background-color: #f43f5e;
        corner-radius: 18px;
    }
    100% {
        translate: 330px -25px;
        rotate: 360deg;
        scale: 1.08;
        opacity: 1;
        background-color: #22c55e;
        corner-radius: 28px;
    }
}

.animation-page {
    width: 1s;
    height: auto;
    gap: 30px;
    padding-bottom: 52px;
}

.l2-hero {
    width: 1s;
    height: auto;
    gap: 12px;
    padding: 22px 24px;
    corner-radius: 18px;
    border-width: 1px;
    border-color: #334155;
    background-color: #0b1220;
}

.l2-hero-badge,
.l2-action-badge {
    width: auto;
    height: auto;
    padding: 5px 10px;
    corner-radius: 999px;
    background-color: #2563eb;
    color: white;
    font-size: 11px;
    font-weight: bold;
}

.l2-showcase-section,
.animation-level-one-stack {
    width: 1s;
    height: auto;
    gap: 14px;
    padding: 22px;
    corner-radius: 18px;
    border-width: 1px;
    border-color: var(--border);
    background-color: var(--background-alt);
}

.l2-timelines-section {
    min-height: 1040px;
}

.l2-section-title {
    width: 1s;
    height: auto;
    font-size: 22px;
    font-weight: bold;
}

.l2-section-copy {
    width: 1s;
    height: auto;
    color: var(--muted-foreground);
    font-size: 13px;
    text-wrap: true;
}

.l2-composition-content,
.l2-timeline-content,
.l2-runtime-content {
    width: 1s;
    height: auto;
    gap: 18px;
}

.l2-composition-row {
    width: 1s;
    height: 330px;
    horizontal-gap: 18px;
}

.l2-composition-cell {
    width: 1s;
    height: 1s;
    gap: 8px;
    padding: 14px;
    corner-radius: 16px;
    border-width: 1px;
    border-color: #334155;
    background-color: #0b1020;
}

.l2-mini-title {
    width: 1s;
    height: auto;
    color: #f8fafc;
    font-size: 15px;
    font-weight: bold;
}

.l2-mini-copy {
    width: 1s;
    height: auto;
    color: #94a3b8;
    font-size: 12px;
    text-wrap: true;
}

.l2-composition-stage {
    width: 1s;
    height: 230px;
    alignment: center;
    overflow: hidden;
    corner-radius: 14px;
    background-color: #020617;
}

.l2-axis-x,
.l2-axis-y {
    position-type: absolute;
    background-color: #334155;
}

.l2-axis-x { width: 78%; height: 2px; }
.l2-axis-y { width: 2px; height: 72%; }

.l2-composition-orb {
    width: 64px;
    height: 64px;
    corner-radius: 18px;
    border-width: 3px;
    border-color: #ccffffff;
    shadow: 0px 14px 30px #77000000;
}

.l2-replace-orb {
    background-color: #f97316;
    animation: l2-translate-x 2400ms ease-in-out 0s infinite alternate both running,
               l2-translate-y 1650ms ease-in-out 0s infinite alternate both running;
    animation-composition: replace, replace;
}

.l2-add-orb {
    background-color: #22c55e;
    animation: l2-translate-x 2400ms ease-in-out 0s infinite alternate both running,
               l2-translate-y 1650ms ease-in-out 0s infinite alternate both running;
    animation-composition: add, add;
}

.l2-accumulate-stage {
    width: 1s;
    height: 220px;
    alignment: center;
    overflow: hidden;
    corner-radius: 14px;
    background-color: #020617;
}

.l2-accumulate-ring {
    position-type: absolute;
    width: 170px;
    height: 170px;
    corner-radius: 50%;
    border-width: 2px;
    border-color: #334155;
}

.l2-accumulate-card {
    width: 118px;
    height: 72px;
    alignment: center;
    corner-radius: 18px;
    background-color: #8b5cf6;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-width: 2px;
    border-color: #c4b5fd;
    animation: l2-rotate-a 2200ms linear 0s infinite alternate both running,
               l2-rotate-b 1400ms ease-in-out 0s infinite alternate both running,
               l2-accumulate-pulse 900ms ease-in-out 0s infinite alternate both running;
    animation-composition: accumulate, accumulate, add;
}

.l2-timeline-lab {
    width: 1s;
    height: 492px;
    gap: 12px;
    padding: 16px;
    corner-radius: 16px;
    border-width: 1px;
    border-color: #334155;
    background-color: #07101f;
}

.l2-progress-stage {
    width: 1s;
    height: 44px;
    alignment: center;
    overflow: hidden;
    corner-radius: 22px;
    background-color: #020617;
}

.l2-progress-track {
    position-type: absolute;
    width: 82%;
    height: 4px;
    corner-radius: 2px;
    background-color: #334155;
}

.l2-progress-dot {
    position-type: absolute;
    width: 24px;
    height: 24px;
    corner-radius: 50%;
    background-color: #38bdf8;
    shadow: 0px 0px 20px #aa38bdf8;
}

.l2-scroll-progress-dot {
    animation: l2-scroll-progress 1s linear 0s 1 both running;
    animation-timeline: --l2-gallery-scroll;
}

.l2-timeline-scroll {
    width: 1s;
    height: 340px;
    corner-radius: 14px;
    border-width: 1px;
    border-color: #334155;
    background-color: #020617;
}

.l2-scroll-content,
.l2-view-content {
    width: 1s;
    height: auto;
    min-height: 1180px;
    alignment: center;
    gap: 20px;
    padding: 24px;
}

.l2-scroll-spacer {
    width: 1s;
    height: 360px;
}

.l2-scroll-caption {
    width: auto;
    height: auto;
    color: #64748b;
    font-size: 12px;
}

.l2-scroll-subject {
    width: 260px;
    height: 110px;
    alignment: center;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-width: 2px;
    border-color: #ccffffff;
    shadow: 0px 18px 36px #77000000;
    animation: l2-scroll-reveal 1s linear 0s 1 both running;
    animation-timeline: --l2-gallery-scroll;
}

.l2-view-filler {
    width: 78%;
    height: 150px;
    alignment: center;
    corner-radius: 18px;
    background-color: #111827;
    color: #64748b;
    border-width: 1px;
    border-color: #1e293b;
}

.l2-view-subject {
    width: 360px;
    height: 150px;
    alignment: center;
    corner-radius: 22px;
    color: white;
    font-size: 20px;
    font-weight: bold;
    border-width: 3px;
    border-color: #ccffffff;
    shadow: 0px 20px 42px #88000000;
    animation: l2-view-reveal 1s linear 0s 1 both running;
    animation-timeline: view(block);
}

.l2-runtime-stage {
    width: 1s;
    height: 310px;
    alignment: center;
    overflow: hidden;
    corner-radius: 18px;
    background-color: #020617;
    border-width: 1px;
    border-color: #334155;
}

.l2-runtime-grid {
    position-type: absolute;
    width: 88%;
    height: 72%;
    corner-radius: 16px;
    border-width: 1px;
    border-color: #1e293b;
    background-color: #07101f;
}

.l2-runtime-target {
    width: 190px;
    height: 82px;
    alignment: center;
    corner-radius: 14px;
    color: white;
    font-size: 15px;
    font-weight: bold;
    border-width: 2px;
    border-color: #ccffffff;
    shadow: 0px 16px 34px #77000000;
    animation: l2-runtime-motion 10s linear 0s 1 both running;
}

.l2-runtime-readout {
    width: 1s;
    height: auto;
    padding: 10px 12px;
    corner-radius: 10px;
    background-color: #0f172a;
    color: #bae6fd;
    font-family: "Cascadia Mono";
    font-size: 12px;
    text-wrap: true;
}

.l2-runtime-controls,
.l2-seek-row {
    width: 1s;
    height: auto;
    alignment: center-left;
    horizontal-gap: 8px;
}

.l2-runtime-controls > button {
    width: auto;
    min-width: 88px;
}

.l2-control-label {
    width: 110px;
    height: auto;
    color: var(--muted-foreground);
    font-size: 12px;
}

.l2-seek-slider {
    width: 1s;
}

.l2-seek-value {
    width: 54px;
    height: auto;
    text-align: center;
    font-size: 12px;
}

.l2-runtime-note {
    width: 1s;
    height: auto;
    color: #94a3b8;
    font-size: 11px;
    text-wrap: true;
}

/* Level 1 witnesses now occupy the page itself instead of a nested 600px VirtualList. */
.animation-level-one-stack {
    gap: 18px;
}

.animation-demo-card {
    height: 330px;
    min-height: 330px;
    padding: 18px;
}

hstack.animation-stage {
    height: 224px;
    padding: 20px;
}
'''
    css_path.write_text(css)
