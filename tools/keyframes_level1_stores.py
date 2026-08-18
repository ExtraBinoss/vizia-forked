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
        offsets.dedup_by(|a, b| {
            if (a.0 - b.0).abs() <= f32::EPSILON {
                // Later keyframe timing declarations win at duplicate offsets.
                a.1 = b.1;
                true
            } else {
                false
            }
        });

        offsets
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

        let active_anim_index = self.inline_data.sparse[entity_index].anim_index as usize;
        if active_anim_index < self.active_animations.len() {
            self.active_animations[active_anim_index].entities.remove(&entity);
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
        self.inline_data.sparse[entity_index].anim_index = self.active_animations.len() as u32;
        self.active_animations.push(anim_state);
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

        let active_anim_index = self.inline_data.sparse[entity_index].anim_index as usize;
        if active_anim_index < self.active_animations.len() {
            self.active_animations[active_anim_index].entities.remove(&entity);
        }

        let mut state = description;
        state.keyframes = Self::normalize_css_keyframes(&state, timeline, underlying);
        state.configure_css(timing, default_timing, start_time);
        state.output = None;
        state.entities.insert(entity);
        self.inline_data.sparse[entity_index].anim_index = self.active_animations.len() as u32;
        self.active_animations.push(state);
    }

    pub(crate) fn update_css_animation(
        &mut self,
        entity: Entity,
        animation: Animation,
        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        now: Instant,
    ) {
        let entity_index = entity.index();
        if entity_index >= self.inline_data.sparse.len() {
            return;
        }
        let active_anim_index = self.inline_data.sparse[entity_index].anim_index as usize;
        if let Some(state) = self.active_animations.get_mut(active_anim_index) {
            if state.id == animation && state.css_clock.is_some() {
                state.update_css_timing(timing, default_timing, now);
            }
        }
    }

    /// Stop an active animation for the given entity.
    pub(crate) fn stop_animation(&mut self, entity: Entity, animation: Animation) {
        let entity_index = entity.index();
        if entity_index >= self.inline_data.sparse.len() {
            return;
        }
        let active_anim_index = self.inline_data.sparse[entity_index].anim_index as usize;
        if active_anim_index < self.active_animations.len()
            && self.active_animations[active_anim_index].id == animation
        {
            self.active_animations[active_anim_index].entities.remove(&entity);
            self.inline_data.sparse[entity_index].anim_index = u32::MAX;
        }
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
                let eased = timing.value_with_before(local, sample.phase == CssAnimationPhase::Before);
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
    replace_once(
        path,
        "            if animation_index < self.active_animations.len() {\n                return self.active_animations[animation_index].get_output();\n            }",
        "            if animation_index < self.active_animations.len() {\n                if let Some(output) = self.active_animations[animation_index].get_output() {\n                    return Some(output);\n                }\n            }",
    )

print("CSS animation storage runtime applied")
