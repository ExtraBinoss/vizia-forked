use std::{cell::Cell, rc::Rc, time::Instant};

use vizia::{
    icons::{ICON_HEART, ICON_STAR},
    prelude::*,
    vg,
};

const ANIMATION_PAGE_ID: &str = "animation-showcase-page";
const RUNTIME_TARGET_ID: &str = "animation-runtime-target";
const REPLACE_TARGET_ID: &str = "animation-replace-target";
const ADD_TARGET_ID: &str = "animation-add-target";
const ACCUMULATE_TARGET_ID: &str = "animation-accumulate-target";
const RUNTIME_DURATION: f32 = 8.0;

const DOCUMENT_TARGET_IDS: &[&str] = &[
    RUNTIME_TARGET_ID,
    REPLACE_TARGET_ID,
    ADD_TARGET_ID,
    ACCUMULATE_TARGET_ID,
];

const DEMOS: &[(&str, &str)] = &[
    (
        "Shorthand + delay + fill",
        "Negative delay, alternate direction and fill mode on a single CSS animation shorthand.",
    ),
    (
        "Iterations + direction",
        "The same keyframes run with alternate and alternate-reverse directions.",
    ),
    (
        "Steps easing",
        "A steps() timing function advances discretely instead of interpolating continuously.",
    ),
    (
        "Play state",
        "The first marker runs while the second copy stays paused halfway through the same keyframes.",
    ),
    (
        "Multiple animations",
        "Two named Level 1 animations affect one element with different periods.",
    ),
    (
        "Layout invalidation",
        "Width, padding and gap animate with stepped timing so layout changes are easy to inspect.",
    ),
    (
        "Visual interpolation",
        "Background, text color, radius, border and shadow interpolate on the same surface.",
    ),
    (
        "Transform family",
        "Translate, rotate and scale move through multiple keyframes.",
    ),
    (
        "Filter blur",
        "filter: blur() interpolates between crisp and blurred states.",
    ),
    (
        "Backdrop filter",
        "backdrop-filter blurs moving content behind a translucent surface.",
    ),
];

const HEART_POINTS: [(f32, f32); 16] = [
    (0.0, -0.48),
    (-0.28, -0.86),
    (-0.68, -0.92),
    (-0.98, -0.62),
    (-1.0, -0.18),
    (-0.84, 0.18),
    (-0.58, 0.45),
    (-0.29, 0.72),
    (0.0, 1.0),
    (0.29, 0.72),
    (0.58, 0.45),
    (0.84, 0.18),
    (1.0, -0.18),
    (0.98, -0.62),
    (0.68, -0.92),
    (0.28, -0.86),
];

const STAR_POINTS: [(f32, f32); 16] = [
    (0.0, -1.0),
    (0.16, -0.38),
    (0.71, -0.71),
    (0.38, -0.16),
    (1.0, 0.0),
    (0.38, 0.16),
    (0.71, 0.71),
    (0.16, 0.38),
    (0.0, 1.0),
    (-0.16, 0.38),
    (-0.71, 0.71),
    (-0.38, 0.16),
    (-1.0, 0.0),
    (-0.38, -0.16),
    (-0.71, -0.71),
    (-0.16, -0.38),
];

struct MorphIcon {
    progress: Signal<f32>,
}

impl MorphIcon {
    fn new(cx: &mut Context, progress: Signal<f32>) -> Handle<'_, Self> {
        let handle = Self { progress }.build(cx, |_| {});
        let entity = handle.entity();
        handle.bind(progress, move |handle| {
            let _ = progress.get();
            handle.context().needs_redraw(entity);
        })
    }
}

impl View for MorphIcon {
    fn element(&self) -> Option<&'static str> {
        Some("morph-icon")
    }

    fn draw(&self, cx: &mut DrawContext, canvas: &Canvas) {
        cx.draw_background(canvas);
        let bounds = cx.bounds();
        if bounds.w <= 0.0 || bounds.h <= 0.0 {
            return;
        }

        let t = self.progress.get().clamp(0.0, 1.0);
        let radius = bounds.w.min(bounds.h) * 0.34;
        let center_x = bounds.x + bounds.w * 0.5;
        let center_y = bounds.y + bounds.h * 0.5;

        let mut path = vg::PathBuilder::new();
        for index in 0..HEART_POINTS.len() {
            let a = HEART_POINTS[index];
            let b = STAR_POINTS[index];
            let x = center_x + (a.0 + (b.0 - a.0) * t) * radius;
            let y = center_y + (a.1 + (b.1 - a.1) * t) * radius;
            let point = vg::Point::new(x, y);
            if index == 0 {
                path.move_to(point);
            } else {
                path.line_to(point);
            }
        }
        path.close();

        let mut paint = vg::Paint::default();
        paint.set_color(cx.font_color());
        paint.set_style(vg::PaintStyle::Stroke);
        paint.set_stroke_width(3.0 * cx.scale_factor());
        paint.set_stroke_cap(vg::PaintCap::Round);
        paint.set_stroke_join(vg::PaintJoin::Round);
        paint.set_anti_alias(true);
        canvas.draw_path(&path.detach(), &paint);
    }
}

fn section_header(cx: &mut Context, title: &'static str, description: &'static str) {
    VStack::new(cx, |cx| {
        Label::new(cx, title).class("animation-section-title");
        Label::new(cx, description).class("animation-section-description");
    })
    .class("animation-section-header");
}

fn baseline_track(cx: &mut Context, class: &'static str) {
    ZStack::new(cx, move |cx| {
        Element::new(cx).class("baseline-orb").class(class);
    })
    .class("baseline-track");
}

fn render_demo_visual(cx: &mut Context, index: usize) {
    match index {
        0 => {
            Label::new(cx, "@KEYFRAMES")
                .class("baseline-surface")
                .class("baseline-entrance");
        }
        1 => {
            VStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "alternate").class("baseline-track-label");
                    baseline_track(cx, "baseline-alternate");
                })
                .class("baseline-track-row");
                HStack::new(cx, |cx| {
                    Label::new(cx, "alternate-reverse").class("baseline-track-label");
                    baseline_track(cx, "baseline-alternate-reverse");
                })
                .class("baseline-track-row");
            })
            .class("baseline-track-stack");
        }
        2 => {
            ZStack::new(cx, |cx| {
                Element::new(cx).class("baseline-step-cursor").class("baseline-steps");
            })
            .class("baseline-step-stage");
        }
        3 => {
            VStack::new(cx, |cx| {
                HStack::new(cx, |cx| {
                    Label::new(cx, "running").class("baseline-track-label");
                    baseline_track(cx, "baseline-running");
                })
                .class("baseline-track-row");
                HStack::new(cx, |cx| {
                    Label::new(cx, "paused at 50%").class("baseline-track-label");
                    baseline_track(cx, "baseline-paused");
                })
                .class("baseline-track-row");
            })
            .class("baseline-track-stack");
        }
        4 => {
            Label::new(cx, "TWO EFFECTS")
                .class("baseline-surface")
                .class("baseline-multiple");
        }
        5 => {
            HStack::new(cx, |cx| {
                Element::new(cx).class("baseline-layout-box");
                Element::new(cx).class("baseline-layout-static");
            })
            .class("baseline-layout-row");
        }
        6 => {
            Label::new(cx, "STYLE")
                .class("baseline-surface")
                .class("baseline-style");
        }
        7 => {
            Element::new(cx).class("baseline-transform");
        }
        8 => {
            Label::new(cx, "FILTER  /  BLUR")
                .class("baseline-filter-sample")
                .class("baseline-filter");
        }
        9 => {
            ZStack::new(cx, |cx| {
                Element::new(cx).class("baseline-backdrop-orb").class("backdrop-orb-one");
                Element::new(cx).class("baseline-backdrop-orb").class("backdrop-orb-two");
                VStack::new(cx, |cx| {
                    Label::new(cx, "Backdrop filter").class("baseline-glass-title");
                    Label::new(cx, "blur over moving content").class("baseline-glass-copy");
                })
                .class("baseline-glass")
                .class("baseline-backdrop");
            })
            .class("baseline-backdrop-stage");
        }
        _ => {}
    }
}

fn runtime_animation_id(cx: &EventContext) -> Option<CssAnimationId> {
    let entity = cx.resolve_entity_identifier(RUNTIME_TARGET_ID)?;
    cx.css_animations(entity).into_iter().next().map(|snapshot| snapshot.id)
}

fn runtime_snapshot_text(cx: &EventContext) -> String {
    let Some(entity) = cx.resolve_entity_identifier(RUNTIME_TARGET_ID) else {
        return "Document timeline is starting…".to_string();
    };
    let Some(snapshot) = cx.css_animations(entity).into_iter().next() else {
        return "No active CSS animation occurrence".to_string();
    };
    let progress = snapshot
        .progress
        .map(|value| format!("{:.0}%", value * 100.0))
        .unwrap_or_else(|| "—".to_string());
    format!(
        "{:?}  ·  {}  ·  {:.1}×  ·  id {}",
        snapshot.state,
        progress,
        snapshot.playback_rate,
        snapshot.id.get(),
    )
}

fn collect_document_animation_ids(cx: &EventContext) -> Vec<CssAnimationId> {
    DOCUMENT_TARGET_IDS
        .iter()
        .filter_map(|identifier| cx.resolve_entity_identifier(identifier))
        .flat_map(|entity| cx.css_animations(entity).into_iter().map(|snapshot| snapshot.id))
        .collect()
}

fn pause_document_animations(cx: &mut EventContext) {
    for id in collect_document_animation_ids(cx) {
        let _ = cx.pause_css_animation(id);
    }
}

fn resume_document_animations(cx: &mut EventContext) {
    for id in collect_document_animation_ids(cx) {
        let _ = cx.resume_css_animation(id);
    }
}

fn level_two_composition(cx: &mut Context) {
    VStack::new(cx, |cx| {
        HStack::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "Replace").class("animation-example-title");
                Label::new(cx, "The later translate effect replaces the earlier one.")
                    .class("animation-example-copy");
                ZStack::new(cx, |cx| {
                    Element::new(cx)
                        .id(REPLACE_TARGET_ID)
                        .class("composition-target")
                        .class("composition-replace");
                })
                .class("composition-stage");
            })
            .class("animation-example-column");

            VStack::new(cx, |cx| {
                Label::new(cx, "Add").class("animation-example-title");
                Label::new(cx, "Both translate effects remain in the effect stack.")
                    .class("animation-example-copy");
                ZStack::new(cx, |cx| {
                    Element::new(cx)
                        .id(ADD_TARGET_ID)
                        .class("composition-target")
                        .class("composition-add");
                })
                .class("composition-stage");
            })
            .class("animation-example-column");
        })
        .class("composition-comparison");

        VStack::new(cx, |cx| {
            Label::new(cx, "Accumulate").class("animation-example-title");
            Label::new(cx, "Two rotate effects accumulate while scale stays an independent effect.")
                .class("animation-example-copy");
            ZStack::new(cx, |cx| {
                Label::new(cx, "A + B")
                    .id(ACCUMULATE_TARGET_ID)
                    .class("accumulate-target");
            })
            .class("accumulate-stage");
        })
        .class("animation-example-column");
    })
    .class("composition-content");
}

fn document_timeline_demo(cx: &mut Context, readout: Signal<String>, seek: Signal<f32>) {
    VStack::new(cx, move |cx| {
        HStack::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "Document timeline · autoplay").class("animation-example-title");
                Label::new(
                    cx,
                    "This one is time-driven. The scrubber follows the animation continuously and can also seek it.",
                )
                .class("animation-example-copy");
            })
            .width(Stretch(1.0));

            HStack::new(cx, |cx| {
                Button::new(cx, |cx| Label::new(cx, "Play"))
                    .on_press(move |cx| {
                        if let Some(id) = runtime_animation_id(cx) {
                            let _ = cx.resume_css_animation(id);
                        }
                    });
                Button::new(cx, |cx| Label::new(cx, "Pause"))
                    .variant(ButtonVariant::Secondary)
                    .on_press(move |cx| {
                        if let Some(id) = runtime_animation_id(cx) {
                            let _ = cx.pause_css_animation(id);
                        }
                    });
                Button::new(cx, |cx| Label::new(cx, "Reverse"))
                    .variant(ButtonVariant::Outline)
                    .on_press(move |cx| {
                        if let Some(id) = runtime_animation_id(cx) {
                            let _ = cx.reverse_css_animation(id);
                        }
                    });
            })
            .class("animation-inline-controls");
        })
        .class("animation-example-heading");

        ZStack::new(cx, |cx| {
            Label::new(cx, "DOCUMENT TIMELINE")
                .id(RUNTIME_TARGET_ID)
                .class("runtime-target");
        })
        .class("runtime-stage");

        HStack::new(cx, move |cx| {
            Slider::new(cx, seek)
                .on_change(move |cx, value| {
                    seek.set(value);
                    if let Some(id) = runtime_animation_id(cx) {
                        let _ = cx.seek_css_animation(id, value * RUNTIME_DURATION);
                    }
                })
                .width(Stretch(1.0));
            Label::new(cx, seek.map(|value| format!("{:>3.0}%", value * 100.0)))
                .class("timeline-value");
        })
        .class("timeline-scrubber");

        HStack::new(cx, move |cx| {
            Label::new(cx, readout).class("runtime-readout");
            HStack::new(cx, |cx| {
                for (label, rate) in [("½×", 0.5_f32), ("1×", 1.0_f32), ("2×", 2.0_f32)] {
                    Button::new(cx, move |cx| Label::new(cx, label))
                        .variant(ButtonVariant::Text)
                        .on_press(move |cx| {
                            if let Some(id) = runtime_animation_id(cx) {
                                let _ = cx.set_css_animation_playback_rate(id, rate);
                            }
                        });
                }
                Button::new(cx, |cx| Label::new(cx, "Restart"))
                    .variant(ButtonVariant::Text)
                    .on_press(move |cx| {
                        if let Some(id) = runtime_animation_id(cx) {
                            let _ = cx.seek_css_animation(id, 0.0);
                            let _ = cx.resume_css_animation(id);
                        }
                    });
            })
            .class("animation-inline-controls");
        })
        .class("runtime-meta-row");
    })
    .class("timeline-document-demo");
}

fn scroll_timeline_demo(cx: &mut Context) {
    let progress = Signal::new(0.0_f32);

    VStack::new(cx, move |cx| {
        HStack::new(cx, move |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "Scroll timeline · scrubbed by scroll")
                    .class("animation-example-title");
                Label::new(
                    cx,
                    "This intentionally does not autoplay: scroll position is the clock. Stop scrolling and the effect freezes exactly there.",
                )
                .class("animation-example-copy");
            })
            .width(Stretch(1.0));
            Label::new(cx, progress.map(|value| format!("{:.0}%", value * 100.0)))
                .class("timeline-progress-copy");
        })
        .class("animation-example-heading");

        ScrollView::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "Scroll inside this area").class("timeline-hint");
                Element::new(cx).class("timeline-spacer");
                Label::new(cx, "SCROLL SCRUB")
                    .class("scroll-timeline-subject");
                Element::new(cx).class("timeline-spacer");
                Label::new(cx, "End").class("timeline-hint");
            })
            .class("scroll-timeline-content");
        })
        .timeline_name("--gallery-scroll")
        .on_scroll(move |_cx, _x, y| progress.set(y))
        .show_horizontal_scrollbar(false)
        .show_vertical_scrollbar(false)
        .class("timeline-scrollview");
    })
    .class("timeline-source-demo");
}

fn view_timeline_demo(cx: &mut Context) {
    VStack::new(cx, |cx| {
        VStack::new(cx, |cx| {
            Label::new(cx, "View timeline · visibility progress")
                .class("animation-example-title");
            Label::new(
                cx,
                "The subject samples its own entry/exit progress through the local viewport. Scroll the viewport, then stop to freeze it.",
            )
            .class("animation-example-copy");
        })
        .class("animation-example-heading");

        ScrollView::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "approach").class("timeline-hint");
                Element::new(cx).class("view-timeline-spacer");
                Label::new(cx, "VIEW PROGRESS").class("view-timeline-subject");
                Element::new(cx).class("view-timeline-spacer");
                Label::new(cx, "depart").class("timeline-hint");
            })
            .class("view-timeline-content");
        })
        .show_horizontal_scrollbar(false)
        .show_vertical_scrollbar(false)
        .class("timeline-scrollview");
    })
    .class("timeline-source-demo");
}

fn morph_demo(
    cx: &mut Context,
    progress: Signal<f32>,
    target: Signal<f32>,
    active: Signal<bool>,
    autoplay: Signal<bool>,
) {
    VStack::new(cx, move |cx| {
        HStack::new(cx, |cx| {
            VStack::new(cx, |cx| {
                Label::new(cx, "Vector path morph · Tabler Heart ↔ Star")
                    .class("animation-example-title");
                Label::new(
                    cx,
                    "A single normalized vector contour is interpolated geometrically — not cross-faded. Scrub it manually or play the sequence.",
                )
                .class("animation-example-copy");
            })
            .width(Stretch(1.0));

            HStack::new(cx, move |cx| {
                Button::new(cx, |cx| {
                    HStack::new(cx, |cx| {
                        Svg::new(cx, ICON_HEART).class("icon");
                        Label::new(cx, "Heart");
                    })
                })
                .variant(ButtonVariant::Outline)
                .on_press(move |_cx| {
                    autoplay.set(false);
                    target.set(0.0);
                    active.set(true);
                });

                Button::new(cx, |cx| {
                    HStack::new(cx, |cx| {
                        Svg::new(cx, ICON_STAR).class("icon");
                        Label::new(cx, "Star");
                    })
                })
                .variant(ButtonVariant::Outline)
                .on_press(move |_cx| {
                    autoplay.set(false);
                    target.set(1.0);
                    active.set(true);
                });
            })
            .class("animation-inline-controls");
        })
        .class("animation-example-heading");

        MorphIcon::new(cx, progress).class("morph-stage");

        HStack::new(cx, move |cx| {
            Button::new(cx, |cx| Label::new(cx, "Play sequence")).on_press(move |_cx| {
                autoplay.set(true);
                if !active.get() {
                    target.set(if progress.get() >= 0.5 { 0.0 } else { 1.0 });
                    active.set(true);
                }
            });
            Button::new(cx, |cx| Label::new(cx, "Pause"))
                .variant(ButtonVariant::Secondary)
                .on_press(move |_cx| {
                    autoplay.set(false);
                    active.set(false);
                });
            Slider::new(cx, progress)
                .on_change(move |_cx, value| {
                    autoplay.set(false);
                    active.set(false);
                    progress.set(value);
                })
                .width(Stretch(1.0));
            Label::new(cx, progress.map(|value| format!("{:.0}%", value * 100.0)))
                .class("timeline-value");
        })
        .class("morph-controls");
    })
    .class("morph-demo");
}

fn interaction_examples(cx: &mut Context) {
    let popover_open = Signal::new(false);

    HStack::new(cx, move |cx| {
        VStack::new(cx, move |cx| {
            Label::new(cx, "Blur reveal popover").class("animation-example-title");
            Label::new(cx, "A native Vizia Popover gets a short CSS blur/opacity entrance.")
                .class("animation-example-copy");

            HStack::new(cx, move |cx| {
                Button::new(cx, |cx| Label::new(cx, "Open popover"))
                    .on_press(move |_cx| popover_open.set(true));

                Binding::new(cx, popover_open, move |cx| {
                    if popover_open.get() {
                        Popover::new(cx, move |cx| {
                            VStack::new(cx, |cx| {
                                Label::new(cx, "Blur reveal").class("animation-popover-title");
                                Label::new(cx, "Mounted once, animated by CSS @keyframes.")
                                    .class("animation-popover-copy");
                                Button::new(cx, |cx| Label::new(cx, "Close"))
                                    .variant(ButtonVariant::Secondary)
                                    .on_press(move |_cx| popover_open.set(false));
                            })
                            .class("animation-popover-content");
                        })
                        .class("animation-blur-popover")
                        .on_blur(move |_cx| popover_open.set(false))
                        .placement(Placement::BottomStart)
                        .show_arrow(false);
                    }
                });
            })
            .class("popover-anchor");
        })
        .class("interaction-example");

        VStack::new(cx, |cx| {
            Label::new(cx, "Text throbber").class("animation-example-title");
            Label::new(cx, "A small ChatGPT-style thinking indicator using staggered keyframes.")
                .class("animation-example-copy");
            HStack::new(cx, |cx| {
                Label::new(cx, "Thinking").class("throbber-label");
                for class in ["throbber-dot-a", "throbber-dot-b", "throbber-dot-c"] {
                    Element::new(cx).class("throbber-dot").class(class);
                }
            })
            .class("text-throbber");
        })
        .class("interaction-example");
    })
    .class("interaction-examples");
}

fn level_one_sampler(cx: &mut Context, selected: Signal<usize>) {
    VStack::new(cx, move |cx| {
        HStack::new(cx, move |cx| {
            VStack::new(cx, move |cx| {
                Label::new(
                    cx,
                    selected.map(|index| format!("{:02} · {}", *index + 1, DEMOS[*index].0)),
                )
                .class("animation-example-title");
                Label::new(cx, selected.map(|index| DEMOS[*index].1.to_string()))
                    .class("animation-example-copy");
            })
            .width(Stretch(1.0));

            HStack::new(cx, move |cx| {
                Button::new(cx, |cx| Label::new(cx, "Previous"))
                    .variant(ButtonVariant::Outline)
                    .on_press(move |_cx| {
                        selected.set((selected.get() + DEMOS.len() - 1) % DEMOS.len());
                    });
                Button::new(cx, |cx| Label::new(cx, "Next"))
                    .variant(ButtonVariant::Outline)
                    .on_press(move |_cx| {
                        selected.set((selected.get() + 1) % DEMOS.len());
                    });
            })
            .class("animation-inline-controls");
        })
        .class("animation-example-heading");

        Binding::new(cx, selected, move |cx| {
            let index = selected.get();
            HStack::new(cx, move |cx| render_demo_visual(cx, index))
                .class("baseline-sample-stage")
                .alignment(Alignment::Center);
        });
    })
    .class("baseline-sampler");
}

fn install_page_ticker(
    cx: &mut Context,
    readout: Signal<String>,
    seek: Signal<f32>,
    morph_progress: Signal<f32>,
    morph_target: Signal<f32>,
    morph_active: Signal<bool>,
    morph_autoplay: Signal<bool>,
) {
    let timer_slot = Rc::new(Cell::new(None));
    let timer_slot_for_callback = Rc::clone(&timer_slot);
    let last_tick = Rc::new(Cell::new(Instant::now()));
    let last_tick_for_callback = Rc::clone(&last_tick);

    let timer = cx.add_timer(std::time::Duration::from_millis(33), None, move |cx, _action| {
        if cx.resolve_entity_identifier(ANIMATION_PAGE_ID).is_none() {
            if let Some(timer) = timer_slot_for_callback.get() {
                cx.stop_timer(timer);
            }
            return;
        }

        let now = Instant::now();
        let dt = now.saturating_duration_since(last_tick_for_callback.get()).as_secs_f32();
        last_tick_for_callback.set(now);

        if morph_active.get() {
            let current = morph_progress.get();
            let target = morph_target.get();
            let direction = if target >= current { 1.0 } else { -1.0 };
            let mut next = current + direction * dt / 0.42;
            let reached = if direction > 0.0 { next >= target } else { next <= target };
            if reached {
                next = target;
            }
            morph_progress.set_if_changed(next.clamp(0.0, 1.0));

            if reached {
                if morph_autoplay.get() {
                    morph_target.set(if target >= 0.5 { 0.0 } else { 1.0 });
                } else {
                    morph_active.set(false);
                }
            }
        }

        if let Some(entity) = cx.resolve_entity_identifier(RUNTIME_TARGET_ID) {
            if let Some(snapshot) = cx.css_animations(entity).into_iter().next() {
                if let Some(progress) = snapshot.progress {
                    seek.set_if_changed(progress.clamp(0.0, 1.0));
                }
                readout.set_if_changed(runtime_snapshot_text(cx));
            }
        }
    });

    timer_slot.set(Some(timer));
    cx.start_timer(timer);
}

pub fn animation(cx: &mut Context) {
    let runtime_readout = Signal::new("Starting document timeline…".to_string());
    let runtime_seek = Signal::new(0.0_f32);
    let morph_progress = Signal::new(0.0_f32);
    let morph_target = Signal::new(1.0_f32);
    let morph_active = Signal::new(false);
    let morph_autoplay = Signal::new(false);
    let baseline_selected = Signal::new(0_usize);

    VStack::new(cx, move |cx| {
        VStack::new(cx, |cx| {
            Label::new(cx, "CSS Animations").class("panel-title");
            Label::new(
                cx,
                "Level 2 composition, timeline sources and runtime control, shown with the same native controls and spacing as the rest of Widget Gallery.",
            )
            .class("panel-description");

            HStack::new(cx, move |cx| {
                Button::new(cx, |cx| Label::new(cx, "Play document animations"))
                    .on_press(move |cx| {
                        resume_document_animations(cx);
                        morph_autoplay.set(true);
                        if !morph_active.get() {
                            morph_target.set(if morph_progress.get() >= 0.5 { 0.0 } else { 1.0 });
                            morph_active.set(true);
                        }
                    });
                Button::new(cx, |cx| Label::new(cx, "Pause document animations"))
                    .variant(ButtonVariant::Secondary)
                    .on_press(move |cx| {
                        pause_document_animations(cx);
                        morph_autoplay.set(false);
                        morph_active.set(false);
                    });
            })
            .class("animation-page-controls");
        })
        .class("animation-page-header");

        Divider::new(cx);

        VStack::new(cx, |cx| {
            section_header(
                cx,
                "Effect stack & composition",
                "The same property can now receive multiple ordered effects. Compare replacement with additive composition directly.",
            );
            level_two_composition(cx);
        })
        .class("animation-section");

        Divider::new(cx);

        VStack::new(cx, move |cx| {
            section_header(
                cx,
                "Timeline sources & runtime control",
                "Document time autoplays; scroll and view timelines intentionally scrub from user movement instead of wall-clock time.",
            );
            document_timeline_demo(cx, runtime_readout, runtime_seek);
            scroll_timeline_demo(cx);
            view_timeline_demo(cx);
        })
        .class("animation-section");

        Divider::new(cx);

        VStack::new(cx, move |cx| {
            section_header(
                cx,
                "Vector morph & interaction",
                "A geometric icon morph, a native blur-reveal popover and a lightweight text throbber exercise animation in actual UI patterns.",
            );
            morph_demo(cx, morph_progress, morph_target, morph_active, morph_autoplay);
            interaction_examples(cx);
        })
        .class("animation-section");

        Divider::new(cx);

        VStack::new(cx, move |cx| {
            section_header(
                cx,
                "Level 1 regression sampler",
                "Only one Level 1 witness is mounted at a time. This keeps the page smooth while preserving the complete regression set.",
            );
            level_one_sampler(cx, baseline_selected);
        })
        .class("animation-section");
    })
    .id(ANIMATION_PAGE_ID)
    .class("panel")
    .class("animation-page")
    .width(Stretch(1.0))
    .max_width(Pixels(1120.0));

    install_page_ticker(
        cx,
        runtime_readout,
        runtime_seek,
        morph_progress,
        morph_target,
        morph_active,
        morph_autoplay,
    );
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

    #[test]
    fn morph_paths_have_matching_topology() {
        assert_eq!(HEART_POINTS.len(), STAR_POINTS.len());
    }
}
