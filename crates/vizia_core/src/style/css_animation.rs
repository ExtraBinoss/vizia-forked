use super::Style;
use crate::{
    animation::{
        Animation, AnimationEvent, AnimationEventKind, CssAnimationClock, CssAnimationPhase,
        CssAnimationTiming, TimingFunction,
    },
    context::Context,
    entity::Entity,
};
use std::time::Instant;
use vizia_id::GenerationalId;
use vizia_style::{
    AnimationComposition, AnimationDirection, AnimationFillMode, AnimationIterationCount,
    AnimationName, AnimationPlayState, EasingFunction,
};

#[derive(Clone, Debug)]
pub(crate) struct CssAnimationInstance {
    pub instance_id: u64,
    pub name: String,
    pub animation: Animation,
    pub clock: CssAnimationClock,
    pub default_timing: TimingFunction,
    pub composition: AnimationComposition,
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
    composition: AnimationComposition,
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
        let easings =
            self.animation_timing_function.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let iterations =
            self.animation_iteration_count.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let directions =
            self.animation_direction.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let fills = self.animation_fill_mode.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let states = self.animation_play_state.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let compositions =
            self.animation_composition.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
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
                let mut duration =
                    repeated(durations, index, vizia_style::AnimationDuration::default()).0.0;
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
                    composition: repeated(compositions, index, AnimationComposition::Replace),
                })
            })
            .collect()
    }

    fn play_css_on_stores(
        &mut self,
        entity: Entity,
        spec: &ResolvedCssAnimation,
        instance_id: u64,
        order: usize,
        start_time: Instant,
    ) {
        let timeline = self.animation_timelines.get(&spec.animation).cloned().unwrap_or_default();
        macro_rules! play {
            ($store:expr) => {
                $store.play_css_animation(
                    entity,
                    spec.animation,
                    instance_id,
                    order,
                    start_time,
                    spec.timing,
                    spec.default_timing,
                    spec.composition,
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
        for store in self.custom_color_props.values_mut() {
            play!(store);
        }
        for store in self.custom_length_props.values_mut() {
            play!(store);
        }
        for store in self.custom_font_size_props.values_mut() {
            play!(store);
        }
        for store in self.custom_letter_spacing_props.values_mut() {
            play!(store);
        }
        for store in self.custom_line_height_props.values_mut() {
            play!(store);
        }
        for store in self.custom_units_props.values_mut() {
            play!(store);
        }
        for store in self.custom_opacity_props.values_mut() {
            play!(store);
        }
        for store in self.custom_shadow_props.values_mut() {
            play!(store);
        }
    }

    fn update_css_on_stores(
        &mut self,
        entity: Entity,
        spec: &ResolvedCssAnimation,
        instance_id: u64,
        order: usize,
        now: Instant,
    ) {
        macro_rules! update {
            ($store:expr) => {
                $store.update_css_animation(
                    entity,
                    instance_id,
                    order,
                    spec.timing,
                    spec.default_timing,
                    spec.composition,
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
        for store in self.custom_color_props.values_mut() {
            update!(store);
        }
        for store in self.custom_length_props.values_mut() {
            update!(store);
        }
        for store in self.custom_font_size_props.values_mut() {
            update!(store);
        }
        for store in self.custom_letter_spacing_props.values_mut() {
            update!(store);
        }
        for store in self.custom_line_height_props.values_mut() {
            update!(store);
        }
        for store in self.custom_units_props.values_mut() {
            update!(store);
        }
        for store in self.custom_opacity_props.values_mut() {
            update!(store);
        }
        for store in self.custom_shadow_props.values_mut() {
            update!(store);
        }
    }

    fn stop_css_on_stores(&mut self, entity: Entity, instance_id: u64) {
        macro_rules! stop {
            ($store:expr) => {
                $store.stop_css_animation(entity, instance_id);
            };
        }
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
        for store in self.custom_color_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_length_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_font_size_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_letter_spacing_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_line_height_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_units_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_opacity_props.values_mut() {
            stop!(store);
        }
        for store in self.custom_shadow_props.values_mut() {
            stop!(store);
        }
    }

    fn cancel_event(
        instance: &CssAnimationInstance,
        entity: Entity,
        now: Instant,
    ) -> AnimationEvent {
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
        let old = self.css_animation_instances.remove(&entity).unwrap_or_default();
        let mut used = vec![false; old.len()];
        let mut next_reversed = Vec::with_capacity(specs.len());

        // CSS Animations matching is performed from the end so duplicate names retain the correct
        // occurrence identity when list lengths or ordering change.
        for (reverse_index, spec) in specs.iter().rev().enumerate() {
            let order = specs.len() - 1 - reverse_index;
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
                    instance.composition = spec.composition;
                    self.update_css_on_stores(entity, spec, instance.instance_id, order, now);
                    next_reversed.push(instance);
                    continue;
                }

                self.pending_animation_events.push(Self::cancel_event(&instance, entity, now));
                self.stop_css_on_stores(entity, instance.instance_id);
            }

            let instance_id = self.next_css_animation_instance_id;
            self.next_css_animation_instance_id =
                self.next_css_animation_instance_id.wrapping_add(1);
            let instance = CssAnimationInstance {
                instance_id,
                name: spec.name.clone(),
                animation: spec.animation,
                clock: CssAnimationClock::new(spec.timing, now),
                default_timing: spec.default_timing,
                composition: spec.composition,
                started: false,
                last_iteration: 0,
                ended: false,
            };
            self.play_css_on_stores(entity, spec, instance_id, order, now);
            next_reversed.push(instance);
        }

        for (index, instance) in old.iter().enumerate() {
            if !used[index] {
                self.pending_animation_events.push(Self::cancel_event(instance, entity, now));
                self.stop_css_on_stores(entity, instance.instance_id);
            }
        }

        next_reversed.reverse();
        if !next_reversed.is_empty() {
            self.css_animation_instances.insert(entity, next_reversed);
        }
    }

    pub(crate) fn cancel_css_animations(&mut self, entity: Entity, now: Instant) {
        if let Some(instances) = self.css_animation_instances.remove(&entity) {
            for instance in instances {
                self.stop_css_on_stores(entity, instance.instance_id);
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
        AnimationDelays, AnimationDirections, AnimationDuration, AnimationDurations,
        AnimationFillModes, AnimationIterationCounts, AnimationNames, AnimationPlayStates,
        AnimationTime, AnimationTimingFunctions,
    };

    #[test]
    fn list_values_repeat_to_match_animation_name_length() {
        let mut style = Style::default();
        let entity = Entity::root();
        style.animation_name.insert(
            entity,
            AnimationNames(vec![
                AnimationName::Custom("a".into()),
                AnimationName::Custom("b".into()),
                AnimationName::Custom("c".into()),
            ]),
        );
        style
            .animation_duration
            .insert(entity, AnimationDurations(vec![AnimationDuration(AnimationTime(2.0))]));
        style.animation_delay.insert(entity, AnimationDelays(vec![AnimationTime(-0.5)]));
        style
            .animation_timing_function
            .insert(entity, AnimationTimingFunctions(vec![EasingFunction::Linear]));
        style
            .animation_iteration_count
            .insert(entity, AnimationIterationCounts(vec![AnimationIterationCount::Number(2.0)]));
        style
            .animation_direction
            .insert(entity, AnimationDirections(vec![AnimationDirection::Alternate]));
        style.animation_fill_mode.insert(entity, AnimationFillModes(vec![AnimationFillMode::Both]));
        style
            .animation_play_state
            .insert(entity, AnimationPlayStates(vec![AnimationPlayState::Paused]));
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
