from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


def insert_before(path: str, marker: str, insertion: str) -> None:
    p = Path(path)
    text = p.read_text()
    if insertion in text:
        return
    if marker not in text:
        raise RuntimeError(f"marker not found in {path}: {marker[:180]!r}")
    p.write_text(text.replace(marker, insertion + marker, 1))


# Public runtime types.
mod = "crates/vizia_core/src/animation/mod.rs"
replace_once(
    mod,
    '''mod animation_event;
pub use animation_event::{AnimationEvent, AnimationEventKind};
''',
    '''mod animation_event;
pub use animation_event::{AnimationEvent, AnimationEventKind};

mod runtime;
pub use runtime::{CssAnimationId, CssAnimationPlaybackState, CssAnimationSnapshot};
pub(crate) use runtime::CssAnimationControl;
''',
)

lib = "crates/vizia_core/src/lib.rs"
replace_once(
    lib,
    '''        Animation, AnimationBuilder, AnimationEvent, AnimationEventKind, KeyframeBuilder,
''',
    '''        Animation, AnimationBuilder, AnimationEvent, AnimationEventKind, CssAnimationId,
        CssAnimationPlaybackState, CssAnimationSnapshot, KeyframeBuilder,
''',
)

# Refactor the CSS clock around a stable elapsed-time anchor. This keeps seek/rate/reverse
# deterministic and lets CSS play-state and runtime pause coexist.
clock = "crates/vizia_core/src/animation/css_timing.rs"
replace_once(
    clock,
    '''pub(crate) struct CssAnimationClock {
    pub timing: CssAnimationTiming,
    pub start_time: Instant,
    paused_at: Option<Instant>,
    paused_duration: Duration,
}
''',
    '''pub(crate) struct CssAnimationClock {
    pub timing: CssAnimationTiming,
    pub start_time: Instant,
    paused_at: Option<Instant>,
    paused_duration: Duration,
    playback_rate: f32,
    seek_offset: f32,
    runtime_paused: bool,
}
''',
)
replace_once(
    clock,
    '''        Self { timing, start_time, paused_at, paused_duration: Duration::ZERO }
''',
    '''        Self {
            timing,
            start_time,
            paused_at,
            paused_duration: Duration::ZERO,
            playback_rate: 1.0,
            seek_offset: 0.0,
            runtime_paused: false,
        }
''',
)
replace_once(
    clock,
    '''        end.saturating_duration_since(self.start_time)
            .saturating_sub(self.paused_duration)
            .as_secs_f32()
''',
    '''        self.seek_offset
            + end
                .saturating_duration_since(self.start_time)
                .saturating_sub(self.paused_duration)
                .as_secs_f32()
                * self.playback_rate
''',
)
replace_once(
    clock,
    '''        let should_pause = timing.play_state == AnimationPlayState::Paused;
''',
    '''        let should_pause = timing.play_state == AnimationPlayState::Paused || self.runtime_paused;
''',
)
insert_before(
    clock,
    "    pub fn update_timing(&mut self, timing: CssAnimationTiming, now: Instant) {\n",
    '''    pub fn playback_rate(&self) -> f32 {
        self.playback_rate
    }

    pub fn is_paused(&self) -> bool {
        self.paused_at.is_some()
    }

    fn reanchor(&mut self, now: Instant, elapsed: f32) {
        let paused = self.is_paused();
        self.start_time = now;
        self.paused_duration = Duration::ZERO;
        self.seek_offset = elapsed;
        self.paused_at = paused.then_some(now);
    }

    pub fn pause(&mut self, now: Instant) {
        self.runtime_paused = true;
        if self.paused_at.is_none() {
            self.paused_at = Some(now);
        }
    }

    pub fn resume(&mut self, now: Instant) {
        self.runtime_paused = false;
        if self.timing.play_state == AnimationPlayState::Running {
            if let Some(paused_at) = self.paused_at.take() {
                self.paused_duration += now.saturating_duration_since(paused_at);
            }
        }
    }

    pub fn seek(&mut self, seconds: f32, now: Instant) {
        let paused = self.is_paused();
        self.start_time = now;
        self.paused_duration = Duration::ZERO;
        self.seek_offset = if seconds.is_finite() { seconds } else { 0.0 };
        self.paused_at = paused.then_some(now);
    }

    pub fn set_playback_rate(&mut self, rate: f32, now: Instant) {
        if !rate.is_finite() {
            return;
        }
        let elapsed = self.effective_elapsed(now);
        self.reanchor(now, elapsed);
        self.playback_rate = rate;
    }

    pub fn reverse(&mut self, now: Instant) {
        let rate = if self.playback_rate.abs() <= f32::EPSILON {
            -1.0
        } else {
            -self.playback_rate
        };
        self.set_playback_rate(rate, now);
    }

    pub fn finish(&mut self, now: Instant) -> bool {
        let duration = self.timing.active_duration();
        if !duration.is_finite() {
            return false;
        }
        self.seek(self.timing.delay + duration, now);
        self.pause(now);
        true
    }

    pub fn map_timeline_progress(&self, progress: Option<f32>) -> Option<f32> {
        progress.map(|progress| {
            if self.playback_rate < 0.0 { 1.0 - progress } else { progress }.clamp(0.0, 1.0)
        })
    }

    pub(crate) fn apply_control(
        &mut self,
        control: crate::animation::CssAnimationControl,
        now: Instant,
    ) -> bool {
        use crate::animation::CssAnimationControl;
        match control {
            CssAnimationControl::Pause => self.pause(now),
            CssAnimationControl::Resume => self.resume(now),
            CssAnimationControl::Seek(seconds) => self.seek(seconds, now),
            CssAnimationControl::SetPlaybackRate(rate) => self.set_playback_rate(rate, now),
            CssAnimationControl::Reverse => self.reverse(now),
            CssAnimationControl::Finish => return self.finish(now),
        }
        true
    }

''',
)
insert_before(
    clock,
    "    #[test]\n    fn progress_timeline_is_reversible_and_ignores_wall_clock()",
    '''    #[test]
    fn runtime_seek_rate_reverse_and_pause_preserve_elapsed_time() {
        let start = Instant::now();
        let mut clock = CssAnimationClock::new(timing(), start);
        clock.seek(1.5, start);
        assert!((clock.effective_elapsed(start) - 1.5).abs() < 0.001);

        clock.set_playback_rate(2.0, start);
        assert!((clock.effective_elapsed(start + Duration::from_millis(250)) - 2.0).abs() < 0.001);

        clock.pause(start + Duration::from_millis(250));
        assert!((clock.effective_elapsed(start + Duration::from_secs(5)) - 2.0).abs() < 0.001);
        clock.resume(start + Duration::from_secs(5));
        assert!((clock.effective_elapsed(start + Duration::from_millis(5250)) - 2.5).abs() < 0.001);

        clock.reverse(start + Duration::from_millis(5250));
        assert_eq!(clock.playback_rate(), -2.0);
        assert!((clock.effective_elapsed(start + Duration::from_millis(5500)) - 2.0).abs() < 0.001);
    }

    #[test]
    fn runtime_finish_rejects_infinite_effects() {
        let start = Instant::now();
        let mut finite = CssAnimationClock::new(timing(), start);
        assert!(finite.finish(start));
        assert!(finite.is_paused());
        assert!(finite.sample(start).finished);

        let infinite_timing = CssAnimationTiming {
            iteration_count: AnimationIterationCount::Infinite,
            ..timing()
        };
        let mut infinite = CssAnimationClock::new(infinite_timing, start);
        assert!(!infinite.finish(start));
    }

''',
)

# Each property store applies a runtime command to the same CSS clock it samples.
for store in [
    "crates/vizia_core/src/storage/animatable_set.rs",
    "crates/vizia_core/src/storage/animatable_var_set.rs",
]:
    insert_before(
        store,
        "    pub(crate) fn set_css_timeline_progress(\n",
        '''    pub(crate) fn control_css_animation(
        &mut self,
        entity: Entity,
        instance_id: u64,
        control: crate::animation::CssAnimationControl,
        now: Instant,
    ) -> bool {
        let mut found = false;
        for state in self.active_animations.iter_mut() {
            if state.css_instance_id == Some(instance_id) && state.entities.contains(&entity) {
                if let Some(clock) = state.css_clock.as_mut() {
                    found |= clock.apply_control(control, now);
                }
            }
        }
        found
    }

''',
    )
    replace_once(
        store,
        '''                    clock.timing.sample_timeline_progress(state.css_timeline_progress)
''',
        '''                    clock
                        .timing
                        .sample_timeline_progress(clock.map_timeline_progress(state.css_timeline_progress))
''',
    )

# Runtime API and snapshots live next to the CSS-instance lifecycle, not in a parallel manager.
runtime = "crates/vizia_core/src/style/css_animation.rs"
replace_once(
    runtime,
    '''        Animation, AnimationEvent, AnimationEventKind, CssAnimationClock, CssAnimationPhase,
        CssAnimationTiming, TimingFunction,
''',
    '''        Animation, AnimationEvent, AnimationEventKind, CssAnimationClock, CssAnimationControl,
        CssAnimationId, CssAnimationPhase, CssAnimationPlaybackState, CssAnimationSnapshot,
        CssAnimationTiming, TimingFunction,
''',
)
replace_once(
    runtime,
    '''    context::Context,
''',
    '''    context::{Context, EventContext},
''',
)

# Freeze external timeline progress while CSS/runtime-paused.
replace_once(
    runtime,
    '''        if let Some(instances) = self.css_animation_instances.get_mut(&entity) {
            if let Some(instance) = instances.iter_mut().find(|item| item.instance_id == instance_id) {
                instance.timeline_driven = driven;
                instance.timeline_progress = progress;
                if driven {
                    instance.ended = false;
                }
            }
        }
        macro_rules! set_progress {
''',
    '''        let mut effective_progress = progress;
        if let Some(instances) = self.css_animation_instances.get_mut(&entity) {
            if let Some(instance) = instances.iter_mut().find(|item| item.instance_id == instance_id) {
                instance.timeline_driven = driven;
                if driven && instance.clock.is_paused() {
                    effective_progress = instance.timeline_progress;
                } else {
                    instance.timeline_progress = progress;
                }
                if driven {
                    instance.ended = false;
                }
            }
        }
        let progress = effective_progress;
        macro_rules! set_progress {
''',
)

insert_before(
    runtime,
    "    fn stop_css_on_stores(&mut self, entity: Entity, instance_id: u64) {\n",
    '''    fn control_css_on_stores(
        &mut self,
        entity: Entity,
        instance_id: u64,
        control: CssAnimationControl,
        now: Instant,
    ) {
        macro_rules! control {
            ($store:expr) => {
                let _ = $store.control_css_animation(entity, instance_id, control, now);
            };
        }
        control!(self.display);
        control!(self.opacity);
        control!(self.clip_path);
        control!(self.filter);
        control!(self.backdrop_filter);
        control!(self.transform);
        control!(self.transform_origin);
        control!(self.translate);
        control!(self.rotate);
        control!(self.scale);
        control!(self.border_top_width);
        control!(self.border_right_width);
        control!(self.border_bottom_width);
        control!(self.border_left_width);
        control!(self.border_top_color);
        control!(self.border_right_color);
        control!(self.border_bottom_color);
        control!(self.border_left_color);
        control!(self.corner_top_left_radius);
        control!(self.corner_top_right_radius);
        control!(self.corner_bottom_left_radius);
        control!(self.corner_bottom_right_radius);
        control!(self.corner_top_left_smoothing);
        control!(self.corner_top_right_smoothing);
        control!(self.corner_bottom_left_smoothing);
        control!(self.corner_bottom_right_smoothing);
        control!(self.outline_width);
        control!(self.outline_color);
        control!(self.outline_offset);
        control!(self.background_color);
        control!(self.background_image);
        control!(self.background_position);
        control!(self.background_repeat);
        control!(self.background_size);
        control!(self.shadow);
        control!(self.font_color);
        control!(self.font_size);
        control!(self.letter_spacing);
        control!(self.line_height);
        control!(self.caret_color);
        control!(self.selection_color);
        control!(self.text_decoration_color);
        control!(self.fill);
        control!(self.left);
        control!(self.right);
        control!(self.top);
        control!(self.bottom);
        control!(self.padding_left);
        control!(self.padding_right);
        control!(self.padding_top);
        control!(self.padding_bottom);
        control!(self.horizontal_gap);
        control!(self.vertical_gap);
        control!(self.width);
        control!(self.height);
        control!(self.min_width);
        control!(self.max_width);
        control!(self.min_height);
        control!(self.max_height);
        control!(self.min_horizontal_gap);
        control!(self.max_horizontal_gap);
        control!(self.min_vertical_gap);
        control!(self.max_vertical_gap);
        for store in self.custom_color_props.values_mut() { control!(store); }
        for store in self.custom_length_props.values_mut() { control!(store); }
        for store in self.custom_font_size_props.values_mut() { control!(store); }
        for store in self.custom_letter_spacing_props.values_mut() { control!(store); }
        for store in self.custom_line_height_props.values_mut() { control!(store); }
        for store in self.custom_units_props.values_mut() { control!(store); }
        for store in self.custom_opacity_props.values_mut() { control!(store); }
        for store in self.custom_shadow_props.values_mut() { control!(store); }
    }

    pub(crate) fn css_animation_snapshots(
        &self,
        entity: Entity,
        now: Instant,
    ) -> Vec<CssAnimationSnapshot> {
        self.css_animation_instances
            .get(&entity)
            .into_iter()
            .flatten()
            .map(|instance| {
                let sample = if instance.timeline_driven {
                    instance.clock.timing.sample_timeline_progress(
                        instance.clock.map_timeline_progress(instance.timeline_progress),
                    )
                } else {
                    instance.clock.sample(now)
                };
                let state = if instance.ended || (!instance.timeline_driven && sample.finished) {
                    CssAnimationPlaybackState::Finished
                } else if instance.clock.is_paused() {
                    CssAnimationPlaybackState::Paused
                } else if sample.phase == CssAnimationPhase::Before {
                    CssAnimationPlaybackState::Pending
                } else {
                    CssAnimationPlaybackState::Running
                };
                CssAnimationSnapshot {
                    id: CssAnimationId(instance.instance_id),
                    name: instance.name.clone(),
                    entity,
                    current_time: if instance.timeline_driven {
                        sample.elapsed_active + instance.clock.timing.delay
                    } else {
                        instance.clock.effective_elapsed(now)
                    },
                    progress: sample.progress,
                    playback_rate: instance.clock.playback_rate(),
                    state,
                    timeline_driven: instance.timeline_driven,
                }
            })
            .collect()
    }

    pub(crate) fn control_css_animation(
        &mut self,
        id: CssAnimationId,
        control: CssAnimationControl,
        now: Instant,
    ) -> bool {
        let Some((entity, index)) = self.css_animation_instances.iter().find_map(|(entity, items)| {
            items.iter().position(|item| item.instance_id == id.0).map(|index| (*entity, index))
        }) else {
            return false;
        };

        let success = {
            let instance = &mut self.css_animation_instances.get_mut(&entity).unwrap()[index];
            let success = instance.clock.apply_control(control, now);
            if matches!(control, CssAnimationControl::Resume | CssAnimationControl::Reverse) {
                instance.ended = false;
            }
            success
        };
        if success {
            self.control_css_on_stores(entity, id.0, control, now);
        }
        success
    }

    pub(crate) fn cancel_css_animation_id(&mut self, id: CssAnimationId, now: Instant) -> bool {
        let Some((entity, index)) = self.css_animation_instances.iter().find_map(|(entity, items)| {
            items.iter().position(|item| item.instance_id == id.0).map(|index| (*entity, index))
        }) else {
            return false;
        };
        let instance = self.css_animation_instances.get_mut(&entity).unwrap().remove(index);
        self.stop_css_on_stores(entity, id.0);
        if !instance.ended {
            self.pending_animation_events.push(Self::cancel_event(&instance, entity, now));
        }
        if self.css_animation_instances.get(&entity).is_some_and(|items| items.is_empty()) {
            self.css_animation_instances.remove(&entity);
        }
        true
    }

''',
)
replace_once(
    runtime,
    '''                    instance.clock.timing.sample_timeline_progress(instance.timeline_progress)
''',
    '''                    instance.clock.timing.sample_timeline_progress(
                        instance.clock.map_timeline_progress(instance.timeline_progress),
                    )
''',
)

# Public Context + EventContext API.
insert_before(
    runtime,
    "#[cfg(test)]\nmod tests {\n",
    '''impl Context {
    /// Snapshot all CSS animation occurrences currently associated with `entity`.
    pub fn css_animations(&self, entity: Entity) -> Vec<CssAnimationSnapshot> {
        self.style.css_animation_snapshots(entity, Instant::now())
    }

    pub fn pause_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Pause, Instant::now())
    }

    pub fn resume_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Resume, Instant::now())
    }

    pub fn seek_css_animation(&mut self, id: CssAnimationId, seconds: f32) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Seek(seconds), Instant::now())
    }

    pub fn set_css_animation_playback_rate(&mut self, id: CssAnimationId, rate: f32) -> bool {
        self.style.control_css_animation(
            id,
            CssAnimationControl::SetPlaybackRate(rate),
            Instant::now(),
        )
    }

    pub fn reverse_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Reverse, Instant::now())
    }

    pub fn finish_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Finish, Instant::now())
    }

    pub fn cancel_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.cancel_css_animation_id(id, Instant::now())
    }
}

impl EventContext<'_> {
    pub fn css_animations(&self, entity: Entity) -> Vec<CssAnimationSnapshot> {
        self.style.css_animation_snapshots(entity, Instant::now())
    }

    pub fn pause_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Pause, Instant::now())
    }

    pub fn resume_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Resume, Instant::now())
    }

    pub fn seek_css_animation(&mut self, id: CssAnimationId, seconds: f32) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Seek(seconds), Instant::now())
    }

    pub fn set_css_animation_playback_rate(&mut self, id: CssAnimationId, rate: f32) -> bool {
        self.style.control_css_animation(
            id,
            CssAnimationControl::SetPlaybackRate(rate),
            Instant::now(),
        )
    }

    pub fn reverse_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Reverse, Instant::now())
    }

    pub fn finish_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.control_css_animation(id, CssAnimationControl::Finish, Instant::now())
    }

    pub fn cancel_css_animation(&mut self, id: CssAnimationId) -> bool {
        self.style.cancel_css_animation_id(id, Instant::now())
    }
}

''',
)

# Focused runtime integration test.
insert_before(
    runtime,
    "    #[test]\n    fn list_values_repeat_to_match_animation_name_length()",
    '''    #[test]
    fn runtime_control_uses_stable_occurrence_id() {
        let mut style = Style::default();
        let entity = Entity::root();
        let animation = style.add_animation(
            AnimationBuilder::new()
                .keyframe(0.0, |key| key.opacity(0.0))
                .keyframe(1.0, |key| key.opacity(1.0)),
        );
        style.animations.insert("runtime".into(), animation);
        style.animation_name.insert(
            entity,
            AnimationNames(vec![AnimationName::Custom("runtime".into())]),
        );
        style.animation_duration.insert(
            entity,
            AnimationDurations(vec![AnimationDuration(AnimationTime(2.0))]),
        );
        style.opacity.insert(entity, Opacity(0.0));
        let start = Instant::now();
        style.sync_css_animations(entity, start);
        let id = style.css_animation_snapshots(entity, start)[0].id;

        assert!(style.control_css_animation(id, CssAnimationControl::Seek(1.0), start));
        assert!(style.control_css_animation(id, CssAnimationControl::Pause, start));
        let snapshot = style.css_animation_snapshots(entity, start + Duration::from_secs(10))[0].clone();
        assert_eq!(snapshot.id, id);
        assert_eq!(snapshot.state, CssAnimationPlaybackState::Paused);
        assert!((snapshot.current_time - 1.0).abs() < 0.001);

        assert!(style.control_css_animation(id, CssAnimationControl::Reverse, start));
        assert_eq!(style.css_animation_snapshots(entity, start)[0].playback_rate, -1.0);
        assert!(style.cancel_css_animation_id(id, start));
        assert!(style.css_animation_snapshots(entity, start).is_empty());
    }

''',
)
