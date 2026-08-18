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
        raise RuntimeError(f"anchor not found in {path}: {old[:160]!r}")
    p.write_text(text.replace(old, new, 1))


write(
    "crates/vizia_core/src/animation/css_timing.rs",
    r'''use std::time::{Duration, Instant};
use vizia_style::{
    AnimationDirection, AnimationFillMode, AnimationIterationCount, AnimationPlayState,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum CssAnimationPhase {
    Before,
    Active,
    After,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct CssAnimationTiming {
    pub duration: f32,
    pub delay: f32,
    pub iteration_count: AnimationIterationCount,
    pub direction: AnimationDirection,
    pub fill_mode: AnimationFillMode,
    pub play_state: AnimationPlayState,
}

impl Default for CssAnimationTiming {
    fn default() -> Self {
        Self {
            duration: 0.0,
            delay: 0.0,
            iteration_count: AnimationIterationCount::Number(1.0),
            direction: AnimationDirection::Normal,
            fill_mode: AnimationFillMode::None,
            play_state: AnimationPlayState::Running,
        }
    }
}

impl CssAnimationTiming {
    pub fn active_duration(self) -> f32 {
        if self.duration <= 0.0 {
            return 0.0;
        }
        match self.iteration_count {
            AnimationIterationCount::Infinite => f32::INFINITY,
            AnimationIterationCount::Number(count) => self.duration * count.max(0.0),
        }
    }

    fn reverse_for_iteration(self, iteration: u64) -> bool {
        match self.direction {
            AnimationDirection::Normal => false,
            AnimationDirection::Reverse => true,
            AnimationDirection::Alternate => iteration % 2 == 1,
            AnimationDirection::AlternateReverse => iteration % 2 == 0,
        }
    }

    fn directed_progress(self, iteration: u64, simple: f32) -> f32 {
        if self.reverse_for_iteration(iteration) { 1.0 - simple } else { simple }
    }

    fn initial_progress(self) -> f32 {
        self.directed_progress(0, 0.0)
    }

    fn final_iteration_and_progress(self) -> (u64, f32) {
        let count = match self.iteration_count {
            AnimationIterationCount::Infinite => return (0, self.initial_progress()),
            AnimationIterationCount::Number(count) => count.max(0.0),
        };

        if count == 0.0 {
            return (0, self.initial_progress());
        }

        let whole = count.floor();
        let fraction = count - whole;
        if fraction.abs() <= f32::EPSILON {
            let iteration = (whole as u64).saturating_sub(1);
            (iteration, self.directed_progress(iteration, 1.0))
        } else {
            let iteration = whole as u64;
            (iteration, self.directed_progress(iteration, fraction))
        }
    }

    fn final_progress(self) -> f32 {
        self.final_iteration_and_progress().1
    }

    pub fn sample(self, active_elapsed: f32) -> CssAnimationSample {
        let active_duration = self.active_duration();
        let local = active_elapsed - self.delay;

        if local < 0.0 {
            let progress = matches!(
                self.fill_mode,
                AnimationFillMode::Backwards | AnimationFillMode::Both
            )
            .then(|| self.initial_progress());
            return CssAnimationSample {
                phase: CssAnimationPhase::Before,
                progress,
                current_iteration: 0,
                elapsed_active: 0.0,
                before: self.reverse_for_iteration(0),
                finished: false,
            };
        }

        if active_duration == 0.0 || local >= active_duration {
            let (final_iteration, final_progress) = self.final_iteration_and_progress();
            let progress = matches!(
                self.fill_mode,
                AnimationFillMode::Forwards | AnimationFillMode::Both
            )
            .then_some(final_progress);
            return CssAnimationSample {
                phase: CssAnimationPhase::After,
                progress,
                current_iteration: final_iteration,
                elapsed_active: active_duration.min(local.max(0.0)),
                before: self.reverse_for_iteration(final_iteration),
                finished: true,
            };
        }

        let duration = self.duration.max(f32::MIN_POSITIVE);
        let position = local / duration;
        let iteration = position.floor() as u64;
        let simple = position - iteration as f32;
        CssAnimationSample {
            phase: CssAnimationPhase::Active,
            progress: Some(self.directed_progress(iteration, simple)),
            current_iteration: iteration,
            elapsed_active: local.max(0.0),
            before: self.reverse_for_iteration(iteration),
            finished: false,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct CssAnimationSample {
    pub phase: CssAnimationPhase,
    pub progress: Option<f32>,
    pub current_iteration: u64,
    pub elapsed_active: f32,
    /// CSS Easing's "before flag" is true while traversing a segment backwards. This matters at
    /// exact discontinuities for step timing functions.
    pub before: bool,
    pub finished: bool,
}

#[derive(Debug, Clone)]
pub(crate) struct CssAnimationClock {
    pub timing: CssAnimationTiming,
    pub start_time: Instant,
    paused_at: Option<Instant>,
    paused_duration: Duration,
}

impl CssAnimationClock {
    pub fn new(timing: CssAnimationTiming, start_time: Instant) -> Self {
        let paused_at = (timing.play_state == AnimationPlayState::Paused).then_some(start_time);
        Self { timing, start_time, paused_at, paused_duration: Duration::ZERO }
    }

    pub fn effective_elapsed(&self, now: Instant) -> f32 {
        let end = self.paused_at.unwrap_or(now);
        end.saturating_duration_since(self.start_time)
            .saturating_sub(self.paused_duration)
            .as_secs_f32()
    }

    pub fn sample(&self, now: Instant) -> CssAnimationSample {
        self.timing.sample(self.effective_elapsed(now))
    }

    pub fn update_timing(&mut self, timing: CssAnimationTiming, now: Instant) {
        let was_paused = self.paused_at.is_some();
        let should_pause = timing.play_state == AnimationPlayState::Paused;
        match (was_paused, should_pause) {
            (false, true) => self.paused_at = Some(now),
            (true, false) => {
                if let Some(paused_at) = self.paused_at.take() {
                    self.paused_duration += now.saturating_duration_since(paused_at);
                }
            }
            _ => {}
        }
        self.timing = timing;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn timing() -> CssAnimationTiming {
        CssAnimationTiming {
            duration: 2.0,
            delay: 1.0,
            iteration_count: AnimationIterationCount::Number(1.0),
            direction: AnimationDirection::Normal,
            fill_mode: AnimationFillMode::None,
            play_state: AnimationPlayState::Running,
        }
    }

    #[test]
    fn phases_positive_and_negative_delay() {
        let t = timing();
        assert_eq!(t.sample(0.5).phase, CssAnimationPhase::Before);
        assert_eq!(t.sample(1.5).progress, Some(0.25));
        assert_eq!(t.sample(3.0).phase, CssAnimationPhase::After);

        let t = CssAnimationTiming { delay: -0.5, ..t };
        assert_eq!(t.sample(0.0).progress, Some(0.25));
    }

    #[test]
    fn fractional_iteration_finishes_part_way_through() {
        let t = CssAnimationTiming {
            iteration_count: AnimationIterationCount::Number(2.5),
            fill_mode: AnimationFillMode::Forwards,
            ..timing()
        };
        assert_eq!(t.sample(6.0).progress, Some(0.5));
    }

    #[test]
    fn direction_modes_cover_odd_and_even_iterations() {
        let base = CssAnimationTiming { delay: 0.0, ..timing() };
        let reverse = CssAnimationTiming { direction: AnimationDirection::Reverse, ..base };
        let reversed_sample = reverse.sample(0.5);
        assert!((reversed_sample.progress.unwrap() - 0.75).abs() < 0.001);
        assert!(reversed_sample.before);

        let alternate = CssAnimationTiming {
            direction: AnimationDirection::Alternate,
            iteration_count: AnimationIterationCount::Number(3.0),
            ..base
        };
        assert!((alternate.sample(2.5).progress.unwrap() - 0.75).abs() < 0.001);
        assert!(alternate.sample(2.5).before);

        let alternate_reverse = CssAnimationTiming {
            direction: AnimationDirection::AlternateReverse,
            iteration_count: AnimationIterationCount::Number(3.0),
            ..base
        };
        assert!((alternate_reverse.sample(0.5).progress.unwrap() - 0.75).abs() < 0.001);
        assert!(alternate_reverse.sample(0.5).before);
    }

    #[test]
    fn fill_modes_choose_values_outside_active_interval() {
        let backwards = CssAnimationTiming { fill_mode: AnimationFillMode::Backwards, ..timing() };
        assert_eq!(backwards.sample(0.0).progress, Some(0.0));

        let both_reverse = CssAnimationTiming {
            fill_mode: AnimationFillMode::Both,
            direction: AnimationDirection::Reverse,
            ..timing()
        };
        assert_eq!(both_reverse.sample(0.0).progress, Some(1.0));
        assert_eq!(both_reverse.sample(4.0).progress, Some(0.0));
    }

    #[test]
    fn zero_duration_and_zero_iterations_are_instantaneous() {
        let zero_duration = CssAnimationTiming {
            duration: 0.0,
            delay: 0.0,
            iteration_count: AnimationIterationCount::Infinite,
            fill_mode: AnimationFillMode::Forwards,
            ..timing()
        };
        assert!(zero_duration.sample(0.0).finished);

        let zero_iterations = CssAnimationTiming {
            delay: 0.0,
            iteration_count: AnimationIterationCount::Number(0.0),
            fill_mode: AnimationFillMode::Forwards,
            ..timing()
        };
        assert_eq!(zero_iterations.sample(0.0).progress, Some(0.0));
    }

    #[test]
    fn pause_freezes_delay_and_active_time() {
        let start = Instant::now();
        let mut clock = CssAnimationClock::new(timing(), start);
        clock.update_timing(
            CssAnimationTiming { play_state: AnimationPlayState::Paused, ..timing() },
            start + Duration::from_millis(500),
        );
        assert_eq!(clock.effective_elapsed(start + Duration::from_secs(5)), 0.5);
        clock.update_timing(timing(), start + Duration::from_secs(5));
        assert!((clock.effective_elapsed(start + Duration::from_millis(5500)) - 1.0).abs() < 0.001);
    }
}
''',
)

write(
    "crates/vizia_core/src/animation/timing_function.rs",
    r'''use vizia_style::{EasingFunction, StepPosition};

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum TimingFunction {
    CubicBezier { x1: f32, x2: f32, y1: f32, y2: f32 },
    Steps { steps: u32, position: StepPosition },
    /// Resolve to the animation-level timing function when sampling CSS keyframes.
    AnimationDefault,
}

impl Default for TimingFunction {
    fn default() -> Self {
        Self::ease_in_out()
    }
}

impl TimingFunction {
    pub fn linear() -> Self {
        Self::new(0., 0., 1., 1.)
    }
    pub fn ease() -> Self {
        Self::new(0.25, 0.1, 0.25, 1.)
    }
    pub fn ease_in() -> Self {
        Self::new(0.42, 0., 1., 1.)
    }
    pub fn ease_out() -> Self {
        Self::new(0., 0., 0.58, 1.)
    }
    pub fn ease_in_out() -> Self {
        Self::new(0.42, 0., 0.58, 1.)
    }

    pub fn from_easing(value: EasingFunction) -> Self {
        match value {
            EasingFunction::Linear => Self::linear(),
            EasingFunction::Ease => Self::ease(),
            EasingFunction::EaseIn => Self::ease_in(),
            EasingFunction::EaseOut => Self::ease_out(),
            EasingFunction::EaseInOut => Self::ease_in_out(),
            EasingFunction::CubicBezier(x1, y1, x2, y2) => Self::new(x1, y1, x2, y2),
            EasingFunction::Steps(steps, position) => Self::Steps { steps, position },
        }
    }

    pub fn new(x1: f32, y1: f32, x2: f32, y2: f32) -> Self {
        Self::CubicBezier { x1, x2, y1, y2 }
    }

    pub fn value(&self, x: f32) -> f32 {
        self.value_with_before(x, false)
    }

    pub fn value_with_before(&self, x: f32, before: bool) -> f32 {
        match *self {
            Self::AnimationDefault => Self::ease().value_with_before(x, before),
            Self::Steps { steps, position } => {
                let steps = steps.max(1) as f32;
                let mut current = (x * steps).floor();
                if matches!(position, StepPosition::JumpStart | StepPosition::JumpBoth | StepPosition::Start) {
                    current += 1.0;
                }
                if before && (x * steps).fract().abs() <= f32::EPSILON {
                    current -= 1.0;
                }
                if x >= 0.0 && current < 0.0 {
                    current = 0.0;
                }
                let jumps = match position {
                    StepPosition::JumpNone => steps - 1.0,
                    StepPosition::JumpBoth => steps + 1.0,
                    _ => steps,
                };
                if x <= 1.0 && current > jumps {
                    current = jumps;
                }
                current / jumps.max(1.0)
            }
            Self::CubicBezier { x1, x2, y1, y2 } => {
                if x1 == y1 && x2 == y2 {
                    return x;
                }
                Self::calc_bezier(Self::find_t_for_x(x, x1, x2), y1, y2)
            }
        }
    }

    fn calc_bezier(t: f32, a1: f32, a2: f32) -> f32 {
        let a = |a1: f32, a2: f32| 1.0 - 3.0 * a2 + 3.0 * a1;
        let b = |a1: f32, a2: f32| 3.0 * a2 - 6.0 * a1;
        let c = |a1: f32| 3.0 * a1;
        ((a(a1, a2) * t + b(a1, a2)) * t + c(a1)) * t
    }

    fn calc_bezier_slope(t: f32, a1: f32, a2: f32) -> f32 {
        let a = |a1: f32, a2: f32| 1.0 - 3.0 * a2 + 3.0 * a1;
        let b = |a1: f32, a2: f32| 3.0 * a2 - 6.0 * a1;
        let c = |a1: f32| 3.0 * a1;
        3.0 * a(a1, a2) * t * t + 2.0 * b(a1, a2) * t + c(a1)
    }

    fn find_t_for_x(x: f32, x1: f32, x2: f32) -> f32 {
        let mut guess = x.clamp(0.0, 1.0);
        for _ in 0..8 {
            let error = Self::calc_bezier(guess, x1, x2) - x;
            if error.abs() <= 0.0000001 {
                return guess;
            }
            let slope = Self::calc_bezier_slope(guess, x1, x2);
            if slope.abs() <= f32::EPSILON {
                break;
            }
            guess = (guess - error / slope).clamp(0.0, 1.0);
        }
        guess
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn linear_and_bezier_presets() {
        assert_eq!(TimingFunction::linear().value(0.5), 0.5);
        assert!((TimingFunction::ease().value(0.25) - 0.4085106).abs() < 0.00001);
    }

    #[test]
    fn steps_follow_css_easing_boundaries() {
        let start = TimingFunction::Steps { steps: 4, position: StepPosition::JumpStart };
        let end = TimingFunction::Steps { steps: 4, position: StepPosition::JumpEnd };
        assert_eq!(start.value(0.0), 0.25);
        assert_eq!(start.value_with_before(0.0, true), 0.0);
        assert_eq!(end.value(0.0), 0.0);
        assert_eq!(end.value(1.0), 1.0);
        assert_eq!(end.value_with_before(0.5, true), 0.25);
    }
}
''',
)

write(
    "crates/vizia_core/src/animation/animation_state.rs",
    r'''use crate::animation::Interpolator;
use hashbrown::HashSet;

use crate::prelude::*;

use super::{CssAnimationClock, CssAnimationTiming, TimingFunction};

/// A keyframe in an animation state.
#[derive(Debug, Clone)]
pub(crate) struct Keyframe<T: Interpolator> {
    pub time: f32,
    pub value: T,
    pub timing_function: TimingFunction,
}

/// Represents an animation of a property with type `T`.
#[derive(Clone, Debug)]
pub(crate) struct AnimationState<T: Interpolator> {
    pub id: Animation,
    pub start_time: Instant,
    pub duration: Duration,
    pub delay: Duration,
    pub keyframes: Vec<Keyframe<T>>,
    pub output: Option<T>,
    pub persistent: bool,
    pub t: f32,
    pub dt: f32,
    pub active: bool,
    pub from_rule: usize,
    pub to_rule: usize,
    pub entities: HashSet<Entity>,
    pub css_clock: Option<CssAnimationClock>,
    pub css_default_timing: TimingFunction,
}

impl<T> AnimationState<T>
where
    T: Interpolator,
{
    pub(crate) fn new(id: Animation) -> Self {
        AnimationState {
            id,
            start_time: Instant::now(),
            duration: Duration::ZERO,
            delay: Duration::ZERO,
            keyframes: Vec::new(),
            output: None,
            persistent: false,
            t: 0.0,
            dt: 0.0,
            active: false,
            entities: HashSet::new(),
            from_rule: usize::MAX,
            to_rule: usize::MAX,
            css_clock: None,
            css_default_timing: TimingFunction::ease(),
        }
    }

    pub(crate) fn with_duration(mut self, duration: Duration) -> Self {
        self.duration = duration;
        self
    }

    pub(crate) fn with_delay(mut self, delay: Duration) -> Self {
        self.delay = delay;
        self
    }

    pub(crate) fn with_keyframe(mut self, key: Keyframe<T>) -> Self {
        self.keyframes.push(key);
        self
    }

    pub(crate) fn get_output(&self) -> Option<&T> {
        self.output.as_ref()
    }

    pub(crate) fn play(&mut self, entity: Entity) {
        self.active = true;
        self.t = 0.0;
        self.start_time = Instant::now();
        self.entities.insert(entity);
    }

    pub(crate) fn configure_css(
        &mut self,
        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        start_time: Instant,
    ) {
        self.start_time = start_time;
        self.duration = Duration::from_secs_f32(timing.duration.max(0.0));
        self.delay = Duration::ZERO;
        self.dt = 0.0;
        self.css_clock = Some(CssAnimationClock::new(timing, start_time));
        self.css_default_timing = default_timing;
        self.persistent = matches!(
            timing.fill_mode,
            vizia_style::AnimationFillMode::Forwards | vizia_style::AnimationFillMode::Both
        );
        self.active = true;
        self.t = 0.0;
    }

    pub(crate) fn update_css_timing(
        &mut self,
        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        now: Instant,
    ) {
        if let Some(clock) = &mut self.css_clock {
            clock.update_timing(timing, now);
        }
        self.css_default_timing = default_timing;
        self.persistent = matches!(
            timing.fill_mode,
            vizia_style::AnimationFillMode::Forwards | vizia_style::AnimationFillMode::Both
        );
    }

    pub(crate) fn is_transition(&self) -> bool {
        !(self.from_rule == usize::MAX && self.to_rule == usize::MAX)
    }
}

impl<Prop> Default for AnimationState<Prop>
where
    Prop: Interpolator,
{
    fn default() -> Self {
        Self {
            id: Animation::null(),
            start_time: Instant::now(),
            duration: Duration::ZERO,
            delay: Duration::ZERO,
            keyframes: Vec::new(),
            output: None,
            persistent: true,
            t: 0.0,
            dt: 0.0,
            active: false,
            entities: HashSet::new(),
            from_rule: usize::MAX,
            to_rule: usize::MAX,
            css_clock: None,
            css_default_timing: TimingFunction::ease(),
        }
    }
}
''',
)

replace_once(
    "crates/vizia_core/src/animation/mod.rs",
    "mod animation_state;\npub(crate) use animation_state::{AnimationState, Keyframe};\n",
    "mod css_timing;\npub(crate) use css_timing::{CssAnimationClock, CssAnimationPhase, CssAnimationSample, CssAnimationTiming};\n\nmod animation_state;\npub(crate) use animation_state::{AnimationState, Keyframe};\n",
)

print("CSS timing runtime foundation applied")
