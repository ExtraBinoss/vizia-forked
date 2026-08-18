from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:160]!r}")
    p.write_text(text.replace(old, new, 1))


def replace_between(path: str, start: str, end: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"start anchor not found in {path}: {start!r}")
    b = text.find(end, a)
    if b < 0:
        raise RuntimeError(f"end anchor not found in {path}: {end!r}")
    p.write_text(text[:a] + new + text[b:])


COMMON_PLAY_AND_TICK = r'''    fn get_base(&self, entity: Entity) -> Option<&T> {
        let entity_index = entity.index();
        if entity_index >= self.inline_data.sparse.len() {
            return None;
        }
        let data_index = self.inline_data.sparse[entity_index].data_index;
        if data_index.is_inline() {
            if data_index.index() < self.inline_data.dense.len() {
                return Some(&self.inline_data.dense[data_index.index()].value);
            }
        } else if data_index.index() < self.shared_data.dense.len() {
            return Some(&self.shared_data.dense[data_index.index()].value);
        }
        None
    }

    fn normalize_css_keyframes(
        description: &AnimationState<T>,
        timeline: &[(f32, TimingFunction)],
        underlying: T,
    ) -> Vec<Keyframe<T>> {
        let mut offsets: Vec<(f32, TimingFunction)> = timeline.to_vec();
        if offsets.is_empty() {
            offsets.extend(
                description
                    .keyframes
                    .iter()
                    .map(|key| (key.time, key.timing_function)),
            );
        }
        if !offsets.iter().any(|(time, _)| (*time).abs() <= f32::EPSILON) {
            offsets.push((0.0, TimingFunction::AnimationDefault));
        }
        if !offsets.iter().any(|(time, _)| (*time - 1.0).abs() <= f32::EPSILON) {
            offsets.push((1.0, TimingFunction::AnimationDefault));
        }
        offsets.sort_by(|a, b| a.0.total_cmp(&b.0));
        let mut normalized_offsets: Vec<(f32, TimingFunction)> = Vec::with_capacity(offsets.len());
        for (time, timing) in offsets {
            if let Some(last) = normalized_offsets.last_mut() {
                if (last.0 - time).abs() <= f32::EPSILON {
                    last.1 = timing;
                    continue;
                }
            }
            normalized_offsets.push((time, timing));
        }

        normalized_offsets
            .into_iter()
            .map(|(time, timing_function)| {
                let value = description
                    .keyframes
                    .iter()
                    .rev()
                    .find(|key| (key.time - time).abs() <= f32::EPSILON)
                    .map(|key| key.value.clone())
                    .unwrap_or_else(|| underlying.clone());
                Keyframe { time, value, timing_function }
            })
            .collect()
    }

    fn refresh_animation_index(&mut self, entity: Entity) {
        let entity_index = entity.index();
        if entity_index >= self.inline_data.sparse.len() {
            return;
        }
        self.inline_data.sparse[entity_index].anim_index = self
            .active_animations
            .iter()
            .enumerate()
            .rev()
            .find(|(_, state)| state.entities.contains(&entity))
            .map(|(index, _)| index as u32)
            .unwrap_or(u32::MAX);
    }

    /// Play an animation for a given entity through the legacy Rust animation API.
    pub(crate) fn play_animation(
        &mut self,
        entity: Entity,
        animation: Animation,
        start_time: Instant,
        duration: Duration,
        delay: Duration,
    ) {
        let entity_index = entity.index();
        let Some(description) = self.animations.get(animation).cloned() else {
            return;
        };
        if description.keyframes.is_empty() {
            return;
        }

        if entity_index >= self.inline_data.sparse.len() {
            self.inline_data.sparse.resize(entity_index + 1, InlineIndex::null());
        }

        // Preserve legacy single-animation behavior without destroying CSS animations that may
        // have higher cascade precedence on the same property.
        for state in self.active_animations.iter_mut() {
            if state.css_clock.is_none() && state.entities.contains(&entity) {
                state.entities.remove(&entity);
            }
        }

        let mut anim_state = description;
        anim_state.duration = duration;
        anim_state.id = animation;
        anim_state.delay = delay;
        anim_state.dt = if duration.is_zero() {
            0.0
        } else {
            delay.as_secs_f32() / duration.as_secs_f32()
        };
        anim_state.start_time = start_time;
        anim_state.output = anim_state.keyframes.first().map(|key| key.value.clone());
        anim_state.active = true;
        anim_state.t = 0.0;
        anim_state.entities.insert(entity);
        self.active_animations.push(anim_state);
        self.refresh_animation_index(entity);
    }

    pub(crate) fn play_css_animation(
        &mut self,
        entity: Entity,
        animation: Animation,
        start_time: Instant,
        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        timeline: &[(f32, TimingFunction)],
    ) {
        let entity_index = entity.index();
        let Some(description) = self.animations.get(animation).cloned() else {
            return;
        };

        let underlying = self.get_base(entity).cloned().unwrap_or_default();
        if entity_index >= self.inline_data.sparse.len() {
            self.inline_data.sparse.resize(entity_index + 1, InlineIndex::null());
        }

        // Restarting the same named animation replaces only that instance. Other CSS animations
        // keep progressing underneath so later list entries can temporarily override them.
        for state in self.active_animations.iter_mut() {
            if state.css_clock.is_some() && state.id == animation {
                state.entities.remove(&entity);
            }
        }

        let mut state = description;
        state.keyframes = Self::normalize_css_keyframes(&state, timeline, underlying);
        state.configure_css(timing, default_timing, start_time);
        state.output = None;
        state.entities.insert(entity);
        self.active_animations.push(state);
        self.refresh_animation_index(entity);
    }

    pub(crate) fn update_css_animation(
        &mut self,
        entity: Entity,
        animation: Animation,
        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        now: Instant,
    ) {
        for state in self.active_animations.iter_mut() {
            if state.css_clock.is_some() && state.id == animation && state.entities.contains(&entity) {
                state.update_css_timing(timing, default_timing, now);
            }
        }
    }

    /// Stop an active animation for the given entity.
    pub(crate) fn stop_animation(&mut self, entity: Entity, animation: Animation) {
        for state in self.active_animations.iter_mut() {
            if state.id == animation {
                state.entities.remove(&entity);
            }
        }
        self.refresh_animation_index(entity);
    }

    /// Tick the animation for the given time and return entities whose animated value may change.
    pub fn tick(&mut self, time: Instant) -> Vec<Entity> {
        self.remove_innactive_animations();

        if !self.has_animations() {
            return Vec::new();
        }

        for state in self.active_animations.iter_mut() {
            if state.t == 1.0 {
                continue;
            }

            if let Some(clock) = &state.css_clock {
                let sample = clock.sample(time);
                state.t = if sample.finished { 1.0 } else { 0.0 };
                let Some(progress) = sample.progress else {
                    state.output = None;
                    continue;
                };

                if state.keyframes.is_empty() {
                    state.output = None;
                    continue;
                }
                if state.keyframes.len() == 1 || progress <= state.keyframes[0].time {
                    state.output = Some(state.keyframes[0].value.clone());
                    continue;
                }
                if progress >= state.keyframes.last().unwrap().time {
                    state.output = Some(state.keyframes.last().unwrap().value.clone());
                    continue;
                }

                let mut i = 0;
                while i + 1 < state.keyframes.len() && state.keyframes[i + 1].time < progress {
                    i += 1;
                }
                let start = &state.keyframes[i];
                let end = &state.keyframes[i + 1];
                let span = end.time - start.time;
                let local = if span.abs() <= f32::EPSILON {
                    1.0
                } else {
                    ((progress - start.time) / span).clamp(0.0, 1.0)
                };
                let timing = if start.timing_function == TimingFunction::AnimationDefault {
                    state.css_default_timing
                } else {
                    start.timing_function
                };
                let eased = timing.value_with_before(local, sample.before);
                state.output = Some(T::interpolate(&start.value, &end.value, eased));
                continue;
            }

            if state.keyframes.is_empty() {
                state.output = None;
                state.t = 1.0;
                continue;
            }
            if state.keyframes.len() == 1 {
                state.output = Some(state.keyframes[0].value.clone());
                let elapsed = time.saturating_duration_since(state.start_time);
                if elapsed >= state.delay.saturating_add(state.duration) {
                    state.t = 1.0;
                }
                continue;
            }

            let elapsed_time = time.saturating_duration_since(state.start_time);
            let mut normalised_time = if state.duration.is_zero() {
                1.0
            } else {
                (elapsed_time.as_secs_f32() / state.duration.as_secs_f32()) - state.dt
            };
            normalised_time = normalised_time.clamp(0.0, 1.0);

            let mut i = 0;
            while i + 1 < state.keyframes.len() && state.keyframes[i + 1].time < normalised_time {
                i += 1;
            }
            let start = &state.keyframes[i];
            let end = &state.keyframes[(i + 1).min(state.keyframes.len() - 1)];
            let span = end.time - start.time;
            let local = if span.abs() <= f32::EPSILON {
                1.0
            } else {
                ((normalised_time - start.time) / span).clamp(0.0, 1.0)
            };
            state.t = normalised_time;
            let timing_t = start.timing_function.value(local);
            state.output = Some(T::interpolate(&start.value, &end.value, timing_t));
        }

        self.active_animations
            .iter()
            .filter(|state| state.t < 1.0)
            .flat_map(|state| state.entities.iter().copied())
            .collect()
    }

'''

VAR_PLAY_AND_TICK = COMMON_PLAY_AND_TICK.replace(
    "return Some(&self.shared_data.dense[data_index.index()].value);",
    "return Some(&self.shared_data.dense[data_index.index()].value.value);",
)

for path, replacement in [
    ("crates/vizia_core/src/storage/animatable_set.rs", COMMON_PLAY_AND_TICK),
    ("crates/vizia_core/src/storage/animatable_var_set.rs", VAR_PLAY_AND_TICK),
]:
    replace_once(
        path,
        "use crate::animation::{AnimationState, Interpolator};",
        "use crate::animation::{\n    AnimationState, CssAnimationPhase, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n};",
    )
    replace_between(
        path,
        "    /// Play an animation for a given entity.\n",
        "    // Returns true if the given entity is linked to an active animation",
        replacement + "    // Returns true if the given entity is linked to an active animation",
    )

    # Animated CSS declarations outrank transitions/base style. For multiple CSS animations on the
    # same property, later list entries are stored later and therefore win while they apply a value.
    replace_once(
        path,
        "            // Animations override inline and shared styling\n            let animation_index = self.inline_data.sparse[entity_index].anim_index as usize;\n\n            if animation_index < self.active_animations.len() {\n                return self.active_animations[animation_index].get_output();\n            }",
        "            // CSS animations override transitions and base style; later CSS animations win.\n            for state in self.active_animations.iter().rev() {\n                if state.css_clock.is_some() && state.entities.contains(&entity) {\n                    if let Some(output) = state.get_output() {\n                        return Some(output);\n                    }\n                }\n            }\n\n            // Preserve the legacy/transition animation path when no CSS animation applies.\n            let animation_index = self.inline_data.sparse[entity_index].anim_index as usize;\n            if animation_index < self.active_animations.len() {\n                if let Some(output) = self.active_animations[animation_index].get_output() {\n                    return Some(output);\n                }\n            }",
    )

    # Removing an entity must detach it from every stacked animation, not only the currently winning
    # sparse index. The rest of the original remove method then deletes inline/base data as before.
    replace_once(
        path,
        "            let active_anim_index = self.inline_data.sparse[entity_index].anim_index as usize;\n\n            if active_anim_index < self.active_animations.len() {\n                let anim_state = &mut self.active_animations[active_anim_index];\n                anim_state.t = 1.0;\n\n                self.remove_innactive_animations();\n            }",
        "            for state in self.active_animations.iter_mut() {\n                state.entities.remove(&entity);\n            }\n            self.inline_data.sparse[entity_index].anim_index = u32::MAX;\n            self.remove_innactive_animations();",
    )

    # Membership queries must see any stacked animation, not just the sparse winner.
    replace_once(
        path,
        "        let entity_index = entity.index();\n        if entity_index < self.inline_data.sparse.len() {\n            let anim_index = self.inline_data.sparse[entity_index].anim_index as usize;\n            if anim_index < self.active_animations.len()\n                && self.active_animations[anim_index].id == animation\n            {\n                return true;\n            }\n        }\n\n        false",
        "        self.active_animations\n            .iter()\n            .any(|state| state.id == animation && state.entities.contains(&entity))",
    )

print("CSS animation storage runtime applied")
