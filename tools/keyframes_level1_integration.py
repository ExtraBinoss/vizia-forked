from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


# Resolve CSS animation declarations for every restyled entity, including the empty-rule case so
# removing a matching selector cancels the animation.
replace_once(
    "crates/vizia_core/src/systems/style.rs",
    "    shared_inheritance_system(cx, &mut redraw_entities);\n",
    r'''    let animation_sync_time = Instant::now();
    for entity in entities.iter().copied() {
        let rules = matched_rules.get(&entity).unwrap_or(&[]);
        cx.style.animation_name.link(entity, rules);
        cx.style.animation_duration.link(entity, rules);
        cx.style.animation_delay.link(entity, rules);
        cx.style.animation_timing_function.link(entity, rules);
        cx.style.animation_iteration_count.link(entity, rules);
        cx.style.animation_direction.link(entity, rules);
        cx.style.animation_fill_mode.link(entity, rules);
        cx.style.animation_play_state.link(entity, rules);
        cx.style.sync_css_animations(entity, animation_sync_time);
    }

    shared_inheritance_system(cx, &mut redraw_entities);
''',
)

# Complete ticking/invalidation for every animatable property family and emit lifecycle events.
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    "    // Corner Radius\n    redraw_entities.extend(cx.style.corner_top_left_radius.tick(time));\n    redraw_entities.extend(cx.style.corner_top_right_radius.tick(time));\n    redraw_entities.extend(cx.style.corner_bottom_left_radius.tick(time));\n    redraw_entities.extend(cx.style.corner_bottom_right_radius.tick(time));\n",
    r'''    // Corner Radius and smoothing. Radius changes also affect rounded clipping.
    let corner_top_left = cx.style.corner_top_left_radius.tick(time);
    let corner_top_right = cx.style.corner_top_right_radius.tick(time);
    let corner_bottom_left = cx.style.corner_bottom_left_radius.tick(time);
    let corner_bottom_right = cx.style.corner_bottom_right_radius.tick(time);
    redraw_entities.extend(corner_top_left.iter().copied());
    redraw_entities.extend(corner_top_right.iter().copied());
    redraw_entities.extend(corner_bottom_left.iter().copied());
    redraw_entities.extend(corner_bottom_right.iter().copied());
    reclip_entities.extend(corner_top_left);
    reclip_entities.extend(corner_top_right);
    reclip_entities.extend(corner_bottom_left);
    reclip_entities.extend(corner_bottom_right);
    redraw_entities.extend(cx.style.corner_top_left_smoothing.tick(time));
    redraw_entities.extend(cx.style.corner_top_right_smoothing.tick(time));
    redraw_entities.extend(cx.style.corner_bottom_left_smoothing.tick(time));
    redraw_entities.extend(cx.style.corner_bottom_right_smoothing.tick(time));
''',
)
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    "    redraw_entities.extend(cx.style.background_image.tick(time));\n    redraw_entities.extend(cx.style.background_size.tick(time));\n",
    "    redraw_entities.extend(cx.style.background_image.tick(time));\n    redraw_entities.extend(cx.style.background_position.tick(time));\n    redraw_entities.extend(cx.style.background_repeat.tick(time));\n    redraw_entities.extend(cx.style.background_size.tick(time));\n",
)
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    "    // Font Color\n    reflow_entities.extend(cx.style.font_color.tick(time));\n",
    r'''    // Pure paint text properties do not require text reconstruction.
    redraw_entities.extend(cx.style.font_color.tick(time));
    redraw_entities.extend(cx.style.caret_color.tick(time));
    redraw_entities.extend(cx.style.selection_color.tick(time));
    redraw_entities.extend(cx.style.text_decoration_color.tick(time));
''',
)
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    "    // Tick animations on custom opacity properties\n    for store in cx.style.custom_opacity_props.values_mut() {\n        redraw_entities.extend(store.tick(time));\n    }\n",
    r'''    // Tick animations on custom opacity properties
    for store in cx.style.custom_opacity_props.values_mut() {
        redraw_entities.extend(store.tick(time));
    }
    // Tick animations on custom shadow properties.
    for store in cx.style.custom_shadow_props.values_mut() {
        redraw_entities.extend(store.tick(time));
    }
''',
)
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    "    for entity in relayout_entities.iter() {\n",
    r'''    // CSS animation lifecycle events are emitted once per named animation.
    let lifecycle_events = cx.style.tick_css_animation_events(time);
    for lifecycle_event in lifecycle_events {
        let entity = lifecycle_event.entity;
        cx.event_queue.push_back(
            Event::new(lifecycle_event)
                .target(entity)
                .origin(entity)
                .propagate(Propagation::Up),
        );
    }

    for entity in relayout_entities.iter() {
''',
)

# The expanded easing enum is shared by transitions and animations.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    r'''        let timing_function = transition
            .timing_function
            .map(|easing| match easing {
                EasingFunction::Linear => TimingFunction::linear(),
                EasingFunction::Ease => TimingFunction::ease(),
                EasingFunction::EaseIn => TimingFunction::ease_in(),
                EasingFunction::EaseOut => TimingFunction::ease_out(),
                EasingFunction::EaseInOut => TimingFunction::ease_in_out(),
                EasingFunction::CubicBezier(x1, y1, x2, y2) => TimingFunction::new(x1, y1, x2, y2),
            })
            .unwrap_or_default();''',
    r'''        let timing_function = transition
            .timing_function
            .map(TimingFunction::from_easing)
            .unwrap_or_default();''',
)

# Entity deletion and stylesheet reload are animation cancellation points. Also clean every
# animation declaration store just like the existing style properties.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    pub(crate) fn remove(&mut self, entity: Entity) {\n        self.relayout.remove(&entity);\n",
    r'''    pub(crate) fn remove(&mut self, entity: Entity) {
        self.cancel_css_animations(entity, Instant::now());
        self.animation_name.remove(entity);
        self.animation_duration.remove(entity);
        self.animation_delay.remove(entity);
        self.animation_timing_function.remove(entity);
        self.animation_iteration_count.remove(entity);
        self.animation_direction.remove(entity);
        self.animation_fill_mode.remove(entity);
        self.animation_play_state.remove(entity);
        self.relayout.remove(&entity);
''',
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "        for store in self.custom_opacity_props.values_mut() {\n            store.remove(entity);\n        }\n    }\n\n    pub(crate) fn needs_restyle",
    r'''        for store in self.custom_opacity_props.values_mut() {
            store.remove(entity);
        }
        for store in self.custom_shadow_props.values_mut() {
            store.remove(entity);
        }
    }

    pub(crate) fn needs_restyle''',
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    pub(crate) fn clear_style_rules(&mut self) {\n        self.disabled.clear_rules();\n",
    r'''    pub(crate) fn clear_style_rules(&mut self) {
        let now = Instant::now();
        let animated_entities: Vec<Entity> = self.css_animation_instances.keys().copied().collect();
        for entity in animated_entities {
            self.cancel_css_animations(entity, now);
        }
        self.animation_name.clear_rules();
        self.animation_duration.clear_rules();
        self.animation_delay.clear_rules();
        self.animation_timing_function.clear_rules();
        self.animation_iteration_count.clear_rules();
        self.animation_direction.clear_rules();
        self.animation_fill_mode.clear_rules();
        self.animation_play_state.clear_rules();
        self.animation_timelines.clear();
        self.animations.clear();
        self.disabled.clear_rules();
''',
)

# Reduced motion: mundy is cross-platform; expose the OS preference and keep an app override.
p = ROOT / "crates/vizia_core/Cargo.toml"
text = p.read_text()
text = text.replace("reqwest = { workspace = true, optional = true, features = [\"blocking\", \"json\"] }\n\n[target.'cfg(target_os = \"linux\")'.dependencies]\nmundy = \"0.2.3\"\n", "reqwest = { workspace = true, optional = true, features = [\"blocking\", \"json\"] }\nmundy = \"0.2.3\"\n")
p.write_text(text)

replace_once(
    "crates/vizia_core/src/environment.rs",
    "#[cfg(target_os = \"linux\")]\nuse mundy::Interest;\n#[cfg(target_os = \"linux\")]\nuse mundy::Preferences;\n",
    "use mundy::{Interest, Preferences, ReducedMotion};\n",
)
replace_once(
    "crates/vizia_core/src/environment.rs",
    "    /// Whether the layout debug overlay is enabled. When set, views which underwent layout in the\n    /// most recent layout pass are outlined in orange until the next layout pass.\n    pub debug_layout: bool,\n",
    "    /// Whether the layout debug overlay is enabled. When set, views which underwent layout in the\n    /// most recent layout pass are outlined in orange until the next layout pass.\n    pub debug_layout: bool,\n    /// Whether the operating system requests reduced motion.\n    pub prefers_reduced_motion: bool,\n",
)
replace_once(
    "crates/vizia_core/src/environment.rs",
    "fn detect_theme() -> ThemeMode {\n",
    r'''fn detect_reduced_motion() -> bool {
    let preferences = Preferences::once_blocking(Interest::ReducedMotion, Duration::from_millis(100));
    preferences.is_some_and(|preferences| preferences.reduced_motion == ReducedMotion::Reduce)
}

fn detect_theme() -> ThemeMode {
''',
)
replace_once(
    "crates/vizia_core/src/environment.rs",
    "        cx.style.debug_layout = false;\n        Self {\n",
    "        cx.style.debug_layout = false;\n        let prefers_reduced_motion = detect_reduced_motion();\n        cx.style.system_reduced_motion = prefers_reduced_motion;\n        Self {\n",
)
replace_once(
    "crates/vizia_core/src/environment.rs",
    "            debug_layout: false,\n        }\n",
    "            debug_layout: false,\n            prefers_reduced_motion,\n        }\n",
)
replace_once(
    "crates/vizia_core/src/environment.rs",
    "    /// Toggle the layout debug overlay on or off.\n    ToggleDebugLayout,\n",
    "    /// Toggle the layout debug overlay on or off.\n    ToggleDebugLayout,\n    /// Update the OS-reported reduced-motion preference.\n    SetReducedMotion(bool),\n",
)
replace_once(
    "crates/vizia_core/src/environment.rs",
    "            EnvironmentEvent::ToggleDebugLayout => {\n                self.debug_layout = !self.debug_layout;\n                cx.style.debug_layout = self.debug_layout;\n                if !self.debug_layout {\n                    cx.style.laid_out.clear();\n                }\n                cx.needs_redraw();\n            }\n",
    r'''            EnvironmentEvent::ToggleDebugLayout => {
                self.debug_layout = !self.debug_layout;
                cx.style.debug_layout = self.debug_layout;
                if !self.debug_layout {
                    cx.style.laid_out.clear();
                }
                cx.needs_redraw();
            }

            EnvironmentEvent::SetReducedMotion(reduced) => {
                if self.prefers_reduced_motion != reduced {
                    self.prefers_reduced_motion = reduced;
                    cx.style.system_reduced_motion = reduced;
                    cx.needs_restyle(Entity::root());
                }
            }
''',
)

print("CSS animation systems, cleanup, and reduced-motion integration applied")
