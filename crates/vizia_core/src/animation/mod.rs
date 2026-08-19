mod animation_id;
pub use animation_id::{AnimId, Animation};

mod animation_event;
pub use animation_event::{AnimationEvent, AnimationEventKind};

mod css_timing;
pub(crate) use css_timing::{CssAnimationClock, CssAnimationPhase, CssAnimationTiming};

mod animation_state;
pub(crate) use animation_state::{AnimationState, Keyframe};

mod interpolator;
pub(crate) use interpolator::{Compositor, Interpolator};

mod timeline;
mod timing_function;
pub(crate) use timeline::{ScrollTimelineSource, view_progress};
pub(crate) use timing_function::TimingFunction;

mod animation_builder;
pub use animation_builder::*;
