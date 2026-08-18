from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


write(
    "crates/vizia_core/src/animation/animation_event.rs",
    r'''use crate::entity::Entity;

/// Lifecycle stage emitted by a CSS keyframe animation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AnimationEventKind {
    Start,
    Iteration,
    End,
    Cancel,
}

/// Event emitted once per `animation-name`, not once per animated property.
#[derive(Debug, Clone, PartialEq)]
pub struct AnimationEvent {
    pub kind: AnimationEventKind,
    pub name: String,
    pub elapsed_time: f32,
    pub entity: Entity,
}
''',
)

write(
    "crates/vizia_core/src/style/css_animation.rs",
    r'''use super::Style;
use crate::{
    animation::{
        Animation, AnimationEvent, AnimationEventKind, CssAnimationClock, CssAnimationPhase,
        CssAnimationTiming, TimingFunction,
    },
    context::Context,
    entity::Entity,
};
use std::time::Instant;
use vizia_style::{
    AnimationDirection, AnimationFillMode, AnimationIterationCount, AnimationName,
    AnimationPlayState, EasingFunction,
};

#[derive(Clone, Debug)]
pub(crate) struct CssAnimationInstance {
    pub name: String,
    pub animation: Animation,
    pub clock: CssAnimationClock,
    pub default_timing: TimingFunction,
    pub started: bool,
    pub last_iteration: u64,
    pub ended: bool,
}

#[derive(Clone, Debug)]
struct ResolvedCssAnimation {
    name: String,
    animation: Animation,
    timing: CssAnimationTiming,
    default_timing: TimingFunction,
}

fn repeated<T: Clone>(items: &[T], index: usize, default: T) -> T {
    if items.is_empty() { default } else { items[index % items.len()].clone() }
}

impl Style {
    fn resolved_css_animations(&self, entity: Entity) -> Vec<ResolvedCssAnimation> {
        let Some(names) = self.animation_name.get(entity) else {
            return Vec::new();
        };
        let durations = self.animation_duration.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let delays = self.animation_delay.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let easings = self
            .animation_timing_function
            .get(entity)
            .map(|v| v.0.as_slice())
            .unwrap_or(&[]);
        let iterations = self
            .animation_iteration_count
            .get(entity)
            .map(|v| v.0.as_slice())
            .unwrap_or(&[]);
        let directions = self.animation_direction.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let fills = self.animation_fill_mode.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let states = self.animation_play_state.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let reduce_motion = self.reduced_motion_override.unwrap_or(self.system_reduced_motion);

        names
            .0
            .iter()
            .enumerate()
            .filter_map(|(index, name)| {
                let AnimationName::Custom(name) = name else {
                    return None;
                };
                let animation = *self.animations.get(name)?;
                let mut duration = repeated(durations, index, vizia_style::AnimationDuration::default()).0.0;
                let mut delay = repeated(delays, index, vizia_style::AnimationTime::default()).0;
                if reduce_motion {
                    duration = 0.0;
                    delay = 0.0;
                }
                let easing = repeated(easings, index, EasingFunction::Ease);
                Some(ResolvedCssAnimation {
                    name: name.clone(),
                    animation,
                    timing: CssAnimationTiming {
                        duration,
                        delay,
                        iteration_count: repeated(
                            iterations,
                            index,
                            AnimationIterationCount::Number(1.0),
                        ),
                        direction: repeated(directions, index, AnimationDirection::Normal),
                        fill_mode: repeated(fills, index, AnimationFillMode::None),
                        play_state: repeated(states, index, AnimationPlayState::Running),
                    },
                    default_timing: TimingFunction::from_easing(easing),
                })
            })
            .collect()
    }

    fn play_css_on_stores(&mut self, entity: Entity, spec: &ResolvedCssAnimation, start_time: Instant) {
        let timeline = self.animation_timelines.get(&spec.animation).cloned().unwrap_or_default();
        macro_rules! play {
            ($store:expr) => {
                $store.play_css_animation(
                    entity,
                    spec.animation,
                    start_time,
                    spec.timing,
                    spec.default_timing,
                    &timeline,
                );
            };
        }
        play!(self.display);
        play!(self.opacity);
        play!(self.clip_path);
        play!(self.filter);
        play!(self.backdrop_filter);
        play!(self.transform);
        play!(self.transform_origin);
        play!(self.translate);
        play!(self.rotate);
        play!(self.scale);
        play!(self.border_top_width);
        play!(self.border_right_width);
        play!(self.border_bottom_width);
        play!(self.border_left_width);
        play!(self.border_top_color);
        play!(self.border_right_color);
        play!(self.border_bottom_color);
        play!(self.border_left_color);
        play!(self.corner_top_left_radius);
        play!(self.corner_top_right_radius);
        play!(self.corner_bottom_left_radius);
        play!(self.corner_bottom_right_radius);
        play!(self.corner_top_left_smoothing);
        play!(self.corner_top_right_smoothing);
        play!(self.corner_bottom_left_smoothing);
        play!(self.corner_bottom_right_smoothing);
        play!(self.outline_width);
        play!(self.outline_color);
        play!(self.outline_offset);
        play!(self.background_color);
        play!(self.background_image);
        play!(self.background_position);
        play!(self.background_repeat);
        play!(self.background_size);
        play!(self.shadow);
        play!(self.font_color);
        play!(self.font_size);
        play!(self.letter_spacing);
        play!(self.line_height);
        play!(self.caret_color);
        play!(self.selection_color);
        play!(self.text_decoration_color);
        play!(self.fill);
        play!(self.left);
        play!(self.right);
        play!(self.top);
        play!(self.bottom);
        play!(self.padding_left);
        play!(self.padding_right);
        play!(self.padding_top);
        play!(self.padding_bottom);
        play!(self.horizontal_gap);
        play!(self.vertical_gap);
        play!(self.width);
        play!(self.height);
        play!(self.min_width);
        play!(self.max_width);
        play!(self.min_height);
        play!(self.max_height);
        play!(self.min_horizontal_gap);
        play!(self.max_horizontal_gap);
        play!(self.min_vertical_gap);
        play!(self.max_vertical_gap);
        for store in self.custom_color_props.values_mut() { play!(store); }
        for store in self.custom_length_props.values_mut() { play!(store); }
        for store in self.custom_font_size_props.values_mut() { play!(store); }
        for store in self.custom_letter_spacing_props.values_mut() { play!(store); }
        for store in self.custom_line_height_props.values_mut() { play!(store); }
        for store in self.custom_units_props.values_mut() { play!(store); }
        for store in self.custom_opacity_props.values_mut() { play!(store); }
        for store in self.custom_shadow_props.values_mut() { play!(store); }
    }

    fn update_css_on_stores(&mut self, entity: Entity, spec: &ResolvedCssAnimation, now: Instant) {
        macro_rules! update {
            ($store:expr) => {
                $store.update_css_animation(
                    entity,
                    spec.animation,
                    spec.timing,
                    spec.default_timing,
                    now,
                );
            };
        }
        update!(self.display);
        update!(self.opacity);
        update!(self.clip_path);
        update!(self.filter);
        update!(self.backdrop_filter);
        update!(self.transform);
        update!(self.transform_origin);
        update!(self.translate);
        update!(self.rotate);
        update!(self.scale);
        update!(self.border_top_width);
        update!(self.border_right_width);
        update!(self.border_bottom_width);
        update!(self.border_left_width);
        update!(self.border_top_color);
        update!(self.border_right_color);
        update!(self.border_bottom_color);
        update!(self.border_left_color);
        update!(self.corner_top_left_radius);
        update!(self.corner_top_right_radius);
        update!(self.corner_bottom_left_radius);
        update!(self.corner_bottom_right_radius);
        update!(self.corner_top_left_smoothing);
        update!(self.corner_top_right_smoothing);
        update!(self.corner_bottom_left_smoothing);
        update!(self.corner_bottom_right_smoothing);
        update!(self.outline_width);
        update!(self.outline_color);
        update!(self.outline_offset);
        update!(self.background_color);
        update!(self.background_image);
        update!(self.background_position);
        update!(self.background_repeat);
        update!(self.background_size);
        update!(self.shadow);
        update!(self.font_color);
        update!(self.font_size);
        update!(self.letter_spacing);
        update!(self.line_height);
        update!(self.caret_color);
        update!(self.selection_color);
        update!(self.text_decoration_color);
        update!(self.fill);
        update!(self.left);
        update!(self.right);
        update!(self.top);
        update!(self.bottom);
        update!(self.padding_left);
        update!(self.padding_right);
        update!(self.padding_top);
        update!(self.padding_bottom);
        update!(self.horizontal_gap);
        update!(self.vertical_gap);
        update!(self.width);
        update!(self.height);
        update!(self.min_width);
        update!(self.max_width);
        update!(self.min_height);
        update!(self.max_height);
        update!(self.min_horizontal_gap);
        update!(self.max_horizontal_gap);
        update!(self.min_vertical_gap);
        update!(self.max_vertical_gap);
        for store in self.custom_color_props.values_mut() { update!(store); }
        for store in self.custom_length_props.values_mut() { update!(store); }
        for store in self.custom_font_size_props.values_mut() { update!(store); }
        for store in self.custom_letter_spacing_props.values_mut() { update!(store); }
        for store in self.custom_line_height_props.values_mut() { update!(store); }
        for store in self.custom_units_props.values_mut() { update!(store); }
        for store in self.custom_opacity_props.values_mut() { update!(store); }
        for store in self.custom_shadow_props.values_mut() { update!(store); }
    }

    fn stop_css_on_stores(&mut self, entity: Entity, animation: Animation) {
        macro_rules! stop { ($store:expr) => { $store.stop_animation(entity, animation); }; }
        stop!(self.display);
        stop!(self.opacity);
        stop!(self.clip_path);
        stop!(self.filter);
        stop!(self.backdrop_filter);
        stop!(self.transform);
        stop!(self.transform_origin);
        stop!(self.translate);
        stop!(self.rotate);
        stop!(self.scale);
        stop!(self.border_top_width);
        stop!(self.border_right_width);
        stop!(self.border_bottom_width);
        stop!(self.border_left_width);
        stop!(self.border_top_color);
        stop!(self.border_right_color);
        stop!(self.border_bottom_color);
        stop!(self.border_left_color);
        stop!(self.corner_top_left_radius);
        stop!(self.corner_top_right_radius);
        stop!(self.corner_bottom_left_radius);
        stop!(self.corner_bottom_right_radius);
        stop!(self.corner_top_left_smoothing);
        stop!(self.corner_top_right_smoothing);
        stop!(self.corner_bottom_left_smoothing);
        stop!(self.corner_bottom_right_smoothing);
        stop!(self.outline_width);
        stop!(self.outline_color);
        stop!(self.outline_offset);
        stop!(self.background_color);
        stop!(self.background_image);
        stop!(self.background_position);
        stop!(self.background_repeat);
        stop!(self.background_size);
        stop!(self.shadow);
        stop!(self.font_color);
        stop!(self.font_size);
        stop!(self.letter_spacing);
        stop!(self.line_height);
        stop!(self.caret_color);
        stop!(self.selection_color);
        stop!(self.text_decoration_color);
        stop!(self.fill);
        stop!(self.left);
        stop!(self.right);
        stop!(self.top);
        stop!(self.bottom);
        stop!(self.padding_left);
        stop!(self.padding_right);
        stop!(self.padding_top);
        stop!(self.padding_bottom);
        stop!(self.horizontal_gap);
        stop!(self.vertical_gap);
        stop!(self.width);
        stop!(self.height);
        stop!(self.min_width);
        stop!(self.max_width);
        stop!(self.min_height);
        stop!(self.max_height);
        stop!(self.min_horizontal_gap);
        stop!(self.max_horizontal_gap);
        stop!(self.min_vertical_gap);
        stop!(self.max_vertical_gap);
        for store in self.custom_color_props.values_mut() { stop!(store); }
        for store in self.custom_length_props.values_mut() { stop!(store); }
        for store in self.custom_font_size_props.values_mut() { stop!(store); }
        for store in self.custom_letter_spacing_props.values_mut() { stop!(store); }
        for store in self.custom_line_height_props.values_mut() { stop!(store); }
        for store in self.custom_units_props.values_mut() { stop!(store); }
        for store in self.custom_opacity_props.values_mut() { stop!(store); }
        for store in self.custom_shadow_props.values_mut() { stop!(store); }
    }

    fn cancel_event(instance: &CssAnimationInstance, entity: Entity, now: Instant) -> AnimationEvent {
        let active_duration = instance.clock.timing.active_duration();
        let elapsed = (instance.clock.effective_elapsed(now) - instance.clock.timing.delay)
            .max(0.0)
            .min(active_duration);
        AnimationEvent {
            kind: AnimationEventKind::Cancel,
            name: instance.name.clone(),
            elapsed_time: elapsed,
            entity,
        }
    }

    pub(crate) fn sync_css_animations(&mut self, entity: Entity, now: Instant) {
        let specs = self.resolved_css_animations(entity);
        let mut old = self.css_animation_instances.remove(&entity).unwrap_or_default();
        let old_signature: Vec<_> = old.iter().map(|i| (i.name.clone(), i.animation)).collect();
        let new_signature: Vec<_> = specs.iter().map(|i| (i.name.clone(), i.animation)).collect();
        let structural_change = old_signature != new_signature;
        let old_animation_ids: Vec<_> = old.iter().map(|i| i.animation).collect();
        let mut used = vec![false; old.len()];
        let mut reversed = Vec::with_capacity(specs.len());

        for spec in specs.iter().rev() {
            let matched = old
                .iter()
                .enumerate()
                .rev()
                .find(|(index, instance)| !used[*index] && instance.name == spec.name)
                .map(|(index, _)| index);
            if let Some(index) = matched {
                used[index] = true;
                let mut instance = old[index].clone();
                if instance.animation == spec.animation {
                    instance.clock.update_timing(spec.timing, now);
                    instance.default_timing = spec.default_timing;
                    reversed.push(instance);
                } else {
                    self.pending_animation_events.push(Self::cancel_event(&instance, entity, now));
                    reversed.push(CssAnimationInstance {
                        name: spec.name.clone(),
                        animation: spec.animation,
                        clock: CssAnimationClock::new(spec.timing, now),
                        default_timing: spec.default_timing,
                        started: false,
                        last_iteration: 0,
                        ended: false,
                    });
                }
            } else {
                reversed.push(CssAnimationInstance {
                    name: spec.name.clone(),
                    animation: spec.animation,
                    clock: CssAnimationClock::new(spec.timing, now),
                    default_timing: spec.default_timing,
                    started: false,
                    last_iteration: 0,
                    ended: false,
                });
            }
        }

        for (index, instance) in old.iter().enumerate() {
            if !used[index] {
                self.pending_animation_events.push(Self::cancel_event(instance, entity, now));
            }
        }

        reversed.reverse();
        if structural_change {
            for animation in old_animation_ids {
                self.stop_css_on_stores(entity, animation);
            }
            for (spec, instance) in specs.iter().zip(reversed.iter()) {
                self.play_css_on_stores(entity, spec, instance.clock.start_time);
            }
        } else {
            for spec in &specs {
                self.update_css_on_stores(entity, spec, now);
            }
        }

        if !reversed.is_empty() {
            self.css_animation_instances.insert(entity, reversed);
        }
    }

    pub(crate) fn cancel_css_animations(&mut self, entity: Entity, now: Instant) {
        if let Some(instances) = self.css_animation_instances.remove(&entity) {
            for instance in instances {
                self.stop_css_on_stores(entity, instance.animation);
                if !instance.ended {
                    self.pending_animation_events.push(Self::cancel_event(&instance, entity, now));
                }
            }
        }
    }

    pub(crate) fn tick_css_animation_events(&mut self, now: Instant) -> Vec<AnimationEvent> {
        let mut events = std::mem::take(&mut self.pending_animation_events);
        for (entity, instances) in self.css_animation_instances.iter_mut() {
            for instance in instances.iter_mut() {
                if instance.ended {
                    continue;
                }
                let sample = instance.clock.sample(now);
                if !instance.started && sample.phase != CssAnimationPhase::Before {
                    instance.started = true;
                    instance.last_iteration = sample.current_iteration;
                    events.push(AnimationEvent {
                        kind: AnimationEventKind::Start,
                        name: instance.name.clone(),
                        elapsed_time: (-instance.clock.timing.delay)
                            .max(0.0)
                            .min(instance.clock.timing.active_duration()),
                        entity: *entity,
                    });
                }

                if instance.started && sample.phase == CssAnimationPhase::Active {
                    if sample.current_iteration > instance.last_iteration
                        && instance.clock.timing.duration > 0.0
                    {
                        for iteration in (instance.last_iteration + 1)..=sample.current_iteration {
                            let elapsed = iteration as f32 * instance.clock.timing.duration;
                            if elapsed < instance.clock.timing.active_duration() {
                                events.push(AnimationEvent {
                                    kind: AnimationEventKind::Iteration,
                                    name: instance.name.clone(),
                                    elapsed_time: elapsed,
                                    entity: *entity,
                                });
                            }
                        }
                    }
                    instance.last_iteration = sample.current_iteration;
                }

                if sample.finished {
                    if !instance.started {
                        instance.started = true;
                        events.push(AnimationEvent {
                            kind: AnimationEventKind::Start,
                            name: instance.name.clone(),
                            elapsed_time: (-instance.clock.timing.delay)
                                .max(0.0)
                                .min(instance.clock.timing.active_duration()),
                            entity: *entity,
                        });
                    }
                    instance.ended = true;
                    events.push(AnimationEvent {
                        kind: AnimationEventKind::End,
                        name: instance.name.clone(),
                        elapsed_time: instance.clock.timing.active_duration(),
                        entity: *entity,
                    });
                }
            }
        }
        events
    }
}

impl Context {
    /// Override the system reduced-motion preference for CSS animations.
    /// `None` follows the operating-system preference.
    pub fn set_reduced_motion_override(&mut self, value: Option<bool>) {
        if self.style.reduced_motion_override != value {
            self.style.reduced_motion_override = value;
            self.needs_restyle(Entity::root());
        }
    }

    pub fn reduced_motion(&self) -> bool {
        self.style.reduced_motion_override.unwrap_or(self.style.system_reduced_motion)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use vizia_style::{
        AnimationDelays, AnimationDirections, AnimationDurations, AnimationFillModes,
        AnimationIterationCounts, AnimationNames, AnimationPlayStates, AnimationTime,
        AnimationTimingFunctions, AnimationDuration,
    };

    #[test]
    fn list_values_repeat_to_match_animation_name_length() {
        let mut style = Style::default();
        let entity = Entity::root();
        style.animation_name.insert(entity, AnimationNames(vec![
            AnimationName::Custom("a".into()),
            AnimationName::Custom("b".into()),
            AnimationName::Custom("c".into()),
        ]));
        style.animation_duration.insert(entity, AnimationDurations(vec![AnimationDuration(AnimationTime(2.0))]));
        style.animation_delay.insert(entity, AnimationDelays(vec![AnimationTime(-0.5)]));
        style.animation_timing_function.insert(entity, AnimationTimingFunctions(vec![EasingFunction::Linear]));
        style.animation_iteration_count.insert(entity, AnimationIterationCounts(vec![AnimationIterationCount::Number(2.0)]));
        style.animation_direction.insert(entity, AnimationDirections(vec![AnimationDirection::Alternate]));
        style.animation_fill_mode.insert(entity, AnimationFillModes(vec![AnimationFillMode::Both]));
        style.animation_play_state.insert(entity, AnimationPlayStates(vec![AnimationPlayState::Paused]));
        for name in ["a", "b", "c"] {
            let id = style.animation_manager.create();
            style.animations.insert(name.into(), id);
        }
        let resolved = style.resolved_css_animations(entity);
        assert_eq!(resolved.len(), 3);
        assert!(resolved.iter().all(|item| item.timing.duration == 2.0));
        assert!(resolved.iter().all(|item| item.timing.delay == -0.5));
        assert!(resolved.iter().all(|item| item.timing.play_state == AnimationPlayState::Paused));
    }
}
''',
)

replace_once(
    "crates/vizia_core/src/animation/mod.rs",
    "mod animation_id;\npub use animation_id::{AnimId, Animation};\n",
    "mod animation_id;\npub use animation_id::{AnimId, Animation};\n\nmod animation_event;\npub use animation_event::{AnimationEvent, AnimationEventKind};\n",
)
replace_once(
    "crates/vizia_core/src/lib.rs",
    "    pub use super::animation::{Animation, AnimationBuilder, KeyframeBuilder};",
    "    pub use super::animation::{\n        Animation, AnimationBuilder, AnimationEvent, AnimationEventKind, KeyframeBuilder,\n    };",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "mod transform;\npub(crate) use transform::*;\n",
    "mod transform;\npub(crate) use transform::*;\n\nmod css_animation;\npub(crate) use css_animation::CssAnimationInstance;\n",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "use crate::animation::{AnimationState, Interpolator, Keyframe, TimingFunction};",
    "use crate::animation::{\n    AnimationEvent, AnimationState, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n};",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    BlendMode, EasingFunction, KeyframeSelector, ParserOptions, Property, Selectors, StyleSheet,\n    TokenList, TokenOrValue, Variable,\n",
    "    AnimationDelays, AnimationDirections, AnimationDurations, AnimationFillModes,\n    AnimationIterationCounts, AnimationNames, AnimationPlayStates, AnimationTimingFunctions,\n    BlendMode, EasingFunction, KeyframeSelector, ParserOptions, Property, Selectors, StyleSheet,\n    TokenList, TokenOrValue, Variable,\n",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    // List of animations to be started on the next frame\n    pub(crate) pending_animations: Vec<(Entity, Animation, Duration, Duration)>,\n",
    "    // List of animations to be started on the next frame\n    pub(crate) pending_animations: Vec<(Entity, Animation, Duration, Duration)>,\n\n    // CSS Animations Level 1 computed declaration lists.\n    pub(crate) animation_name: StyleSet<AnimationNames>,\n    pub(crate) animation_duration: StyleSet<AnimationDurations>,\n    pub(crate) animation_delay: StyleSet<AnimationDelays>,\n    pub(crate) animation_timing_function: StyleSet<AnimationTimingFunctions>,\n    pub(crate) animation_iteration_count: StyleSet<AnimationIterationCounts>,\n    pub(crate) animation_direction: StyleSet<AnimationDirections>,\n    pub(crate) animation_fill_mode: StyleSet<AnimationFillModes>,\n    pub(crate) animation_play_state: StyleSet<AnimationPlayStates>,\n    pub(crate) css_animation_instances: HashMap<Entity, Vec<CssAnimationInstance>>,\n    pub(crate) animation_timelines: HashMap<Animation, Vec<(f32, TimingFunction)>>,\n    pub(crate) pending_animation_events: Vec<AnimationEvent>,\n    pub(crate) system_reduced_motion: bool,\n    pub(crate) reduced_motion_override: Option<bool>,\n",
)

# Handle animation declarations before the large property match. The existing wildcard then remains valid.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    fn insert_property(&mut self, rule_id: Rule, property: &Property) {\n",
    r'''    fn insert_property(&mut self, rule_id: Rule, property: &Property) {
        match property {
            Property::AnimationName(value) => {
                self.animation_name.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationDuration(value) => {
                self.animation_duration.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationDelay(value) => {
                self.animation_delay.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationTimingFunction(value) => {
                self.animation_timing_function.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationIterationCount(value) => {
                self.animation_iteration_count.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationDirection(value) => {
                self.animation_direction.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationFillMode(value) => {
                self.animation_fill_mode.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationPlayState(value) => {
                self.animation_play_state.insert_rule(rule_id, value.clone());
                return;
            }
            Property::Animation(value) => {
                self.animation_name.insert_rule(
                    rule_id,
                    AnimationNames(value.0.iter().map(|item| item.name.clone()).collect()),
                );
                self.animation_duration.insert_rule(
                    rule_id,
                    AnimationDurations(value.0.iter().map(|item| item.duration).collect()),
                );
                self.animation_delay.insert_rule(
                    rule_id,
                    AnimationDelays(value.0.iter().map(|item| item.delay).collect()),
                );
                self.animation_timing_function.insert_rule(
                    rule_id,
                    AnimationTimingFunctions(
                        value.0.iter().map(|item| item.timing_function).collect(),
                    ),
                );
                self.animation_iteration_count.insert_rule(
                    rule_id,
                    AnimationIterationCounts(
                        value.0.iter().map(|item| item.iteration_count).collect(),
                    ),
                );
                self.animation_direction.insert_rule(
                    rule_id,
                    AnimationDirections(value.0.iter().map(|item| item.direction).collect()),
                );
                self.animation_fill_mode.insert_rule(
                    rule_id,
                    AnimationFillModes(value.0.iter().map(|item| item.fill_mode).collect()),
                );
                self.animation_play_state.insert_rule(
                    rule_id,
                    AnimationPlayStates(value.0.iter().map(|item| item.play_state).collect()),
                );
                return;
            }
            _ => {}
        }
''',
)

# Record a normalized timing timeline for all logical keyframe selectors, including duplicate offsets.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "                        let animation_id = self.animation_manager.create();\n\n                        for keyframes in keyframes_rule.keyframes {\n",
    "                        let animation_id = self.animation_manager.create();\n                        let mut animation_timeline = Vec::new();\n\n                        for keyframes in keyframes_rule.keyframes {\n",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "                                self.add_keyframe(\n                                    animation_id,\n                                    time,\n                                    &keyframes.declarations.declarations,\n                                );\n",
    r'''                                let keyframe_timing = keyframes
                                    .declarations
                                    .declarations
                                    .iter()
                                    .rev()
                                    .find_map(|property| match property {
                                        Property::AnimationTimingFunction(functions) => {
                                            functions.0.first().copied()
                                        }
                                        _ => None,
                                    })
                                    .map(TimingFunction::from_easing)
                                    .unwrap_or(TimingFunction::AnimationDefault);
                                animation_timeline.push((time, keyframe_timing));
                                self.add_keyframe(
                                    animation_id,
                                    time,
                                    &keyframes.declarations.declarations,
                                );
''',
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "                        self.animations.insert(name, animation_id);\n",
    "                        self.animation_timelines.insert(animation_id, animation_timeline);\n                        self.animations.insert(name, animation_id);\n",
)

# New easing enum variants, including steps(), are converted through the shared converter.
old_easing = r'''        let timing_function = match transition.timing_function {
            EasingFunction::Linear => TimingFunction::linear(),
            EasingFunction::Ease => TimingFunction::ease(),
            EasingFunction::EaseIn => TimingFunction::ease_in(),
            EasingFunction::EaseOut => TimingFunction::ease_out(),
            EasingFunction::EaseInOut => TimingFunction::ease_in_out(),
            EasingFunction::CubicBezier(x1, y1, x2, y2) => TimingFunction::new(x1, y1, x2, y2),
        };'''
if old_easing in (ROOT / "crates/vizia_core/src/style/mod.rs").read_text():
    replace_once(
        "crates/vizia_core/src/style/mod.rs",
        old_easing,
        "        let timing_function = TimingFunction::from_easing(transition.timing_function);",
    )

print("CSS animation declaration resolver applied")
