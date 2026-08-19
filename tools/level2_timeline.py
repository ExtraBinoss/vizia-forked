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


# ---------------------------------------------------------------------------
# CSS values: animation-timeline
# ---------------------------------------------------------------------------
values = "crates/vizia_style/src/values/animation.rs"
insert_before(
    values,
    "#[derive(Debug, Clone, PartialEq)]\npub struct AnimationShorthandItem",
    '''#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AnimationTimelineAxis {
    #[default]
    Block,
    Inline,
    X,
    Y,
}

impl AnimationTimelineAxis {
    fn from_ident(ident: &str) -> Option<Self> {
        if ident.eq_ignore_ascii_case("block") {
            Some(Self::Block)
        } else if ident.eq_ignore_ascii_case("inline") {
            Some(Self::Inline)
        } else if ident.eq_ignore_ascii_case("x") {
            Some(Self::X)
        } else if ident.eq_ignore_ascii_case("y") {
            Some(Self::Y)
        } else {
            None
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AnimationScroller {
    Root,
    #[default]
    Nearest,
    Self_,
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub enum AnimationTimeline {
    #[default]
    Auto,
    None,
    Named(String),
    Scroll {
        scroller: AnimationScroller,
        axis: AnimationTimelineAxis,
    },
    View {
        axis: AnimationTimelineAxis,
    },
}

impl<'i> Parse<'i> for AnimationTimeline {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        if let Ok(ident) = input.try_parse(|input| input.expect_ident_cloned()) {
            if ident.as_ref().eq_ignore_ascii_case("auto") {
                return Ok(Self::Auto);
            }
            if ident.as_ref().eq_ignore_ascii_case("none") {
                return Ok(Self::None);
            }
            if ident.as_ref().starts_with("--") {
                return Ok(Self::Named(ident.to_string()));
            }
            return Err(input.new_custom_error(CustomParseError::InvalidValue));
        }

        if input.try_parse(|input| input.expect_function_matching("scroll")).is_ok() {
            return input.parse_nested_block(|input| {
                let mut scroller = AnimationScroller::Nearest;
                let mut axis = AnimationTimelineAxis::Block;
                let mut seen_scroller = false;
                let mut seen_axis = false;
                while !input.is_exhausted() {
                    let location = input.current_source_location();
                    let ident = input.expect_ident_cloned()?;
                    if let Some(value) = AnimationTimelineAxis::from_ident(ident.as_ref()) {
                        if seen_axis {
                            return Err(location.new_unexpected_token_error(Token::Ident(ident)));
                        }
                        seen_axis = true;
                        axis = value;
                        continue;
                    }
                    let value = if ident.as_ref().eq_ignore_ascii_case("root") {
                        Some(AnimationScroller::Root)
                    } else if ident.as_ref().eq_ignore_ascii_case("nearest") {
                        Some(AnimationScroller::Nearest)
                    } else if ident.as_ref().eq_ignore_ascii_case("self") {
                        Some(AnimationScroller::Self_)
                    } else {
                        None
                    };
                    let Some(value) = value else {
                        return Err(location.new_unexpected_token_error(Token::Ident(ident)));
                    };
                    if seen_scroller {
                        return Err(location.new_unexpected_token_error(Token::Ident(ident)));
                    }
                    seen_scroller = true;
                    scroller = value;
                }
                Ok(Self::Scroll { scroller, axis })
            });
        }

        if input.try_parse(|input| input.expect_function_matching("view")).is_ok() {
            return input.parse_nested_block(|input| {
                let axis = if input.is_exhausted() {
                    AnimationTimelineAxis::Block
                } else {
                    let location = input.current_source_location();
                    let ident = input.expect_ident_cloned()?;
                    let Some(axis) = AnimationTimelineAxis::from_ident(ident.as_ref()) else {
                        return Err(location.new_unexpected_token_error(Token::Ident(ident)));
                    };
                    if !input.is_exhausted() {
                        let token = input.next()?.clone();
                        return Err(location.new_unexpected_token_error(token));
                    }
                    axis
                };
                Ok(Self::View { axis })
            });
        }

        let location = input.current_source_location();
        let token = input.next()?.clone();
        Err(location.new_unexpected_token_error(token))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct AnimationTimelines(pub Vec<AnimationTimeline>);

impl<'i> Parse<'i> for AnimationTimelines {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationTimeline::parse).map(Self)
    }
}

''',
)
insert_before(
    values,
    "    #[test]\n    fn parses_animation_composition_list()",
    '''    #[test]
    fn parses_animation_timeline_values() {
        let mut input = ParserInput::new("auto, --gallery, scroll(nearest y), scroll(x self), view(block)");
        let mut parser = Parser::new(&mut input);
        let parsed = AnimationTimelines::parse(&mut parser).expect("timeline list should parse");
        assert_eq!(parsed.0.len(), 5);
        assert_eq!(parsed.0[0], AnimationTimeline::Auto);
        assert_eq!(parsed.0[1], AnimationTimeline::Named("--gallery".into()));
        assert_eq!(
            parsed.0[2],
            AnimationTimeline::Scroll {
                scroller: AnimationScroller::Nearest,
                axis: AnimationTimelineAxis::Y,
            }
        );
        assert_eq!(
            parsed.0[3],
            AnimationTimeline::Scroll {
                scroller: AnimationScroller::Self_,
                axis: AnimationTimelineAxis::X,
            }
        );
        assert_eq!(
            parsed.0[4],
            AnimationTimeline::View { axis: AnimationTimelineAxis::Block }
        );
    }

''',
)

# Property parser.
property = "crates/vizia_style/src/property.rs"
replace_once(
    property,
    '''        "animation-composition": AnimationComposition(AnimationCompositions),
        "animation": Animation(AnimationShorthand),
''',
    '''        "animation-composition": AnimationComposition(AnimationCompositions),
        "animation-timeline": AnimationTimeline(AnimationTimelines),
        "animation": Animation(AnimationShorthand),
''',
)

# ---------------------------------------------------------------------------
# Core module exports and timing sampling.
# ---------------------------------------------------------------------------
mod = "crates/vizia_core/src/animation/mod.rs"
replace_once(mod, "mod timing_function;\n", "mod timing_function;\nmod timeline;\n")
replace_once(
    mod,
    "pub(crate) use timing_function::TimingFunction;\n",
    "pub(crate) use timeline::{ScrollTimelineSource, view_progress};\npub(crate) use timing_function::TimingFunction;\n",
)

timing = "crates/vizia_core/src/animation/css_timing.rs"
insert_before(
    timing,
    "}\n\n#[derive(Debug, Clone, Copy, PartialEq)]\npub(crate) struct CssAnimationSample",
    '''
    /// Sample a progress-based timeline. Delays are intentionally not wall-clock delays here: the
    /// external timeline owns progress and maps its full 0..=1 range across the effect iterations.
    /// Infinite iteration counts map to one reversible timeline iteration.
    pub fn sample_timeline_progress(self, progress: Option<f32>) -> CssAnimationSample {
        let Some(progress) = progress else {
            return CssAnimationSample {
                phase: CssAnimationPhase::Before,
                progress: None,
                current_iteration: 0,
                elapsed_active: 0.0,
                before: self.reverse_for_iteration(0),
                finished: false,
            };
        };
        let timeline_progress = progress.clamp(0.0, 1.0);
        let count = match self.iteration_count {
            AnimationIterationCount::Infinite => 1.0,
            AnimationIterationCount::Number(count) => count.max(0.0),
        };
        if count == 0.0 {
            return CssAnimationSample {
                phase: CssAnimationPhase::Active,
                progress: Some(self.initial_progress()),
                current_iteration: 0,
                elapsed_active: 0.0,
                before: self.reverse_for_iteration(0),
                finished: false,
            };
        }
        if timeline_progress >= 1.0 {
            let (iteration, value) = match self.iteration_count {
                AnimationIterationCount::Infinite => (0, self.directed_progress(0, 1.0)),
                AnimationIterationCount::Number(_) => self.final_iteration_and_progress(),
            };
            return CssAnimationSample {
                phase: CssAnimationPhase::Active,
                progress: Some(value),
                current_iteration: iteration,
                elapsed_active: self.duration.max(0.0) * count,
                before: self.reverse_for_iteration(iteration),
                finished: false,
            };
        }
        let position = timeline_progress * count;
        let iteration = position.floor() as u64;
        let simple = position - iteration as f32;
        CssAnimationSample {
            phase: CssAnimationPhase::Active,
            progress: Some(self.directed_progress(iteration, simple)),
            current_iteration: iteration,
            elapsed_active: timeline_progress * self.duration.max(0.0) * count,
            before: self.reverse_for_iteration(iteration),
            finished: false,
        }
    }
''',
)
insert_before(
    timing,
    "    #[test]\n    fn phases_positive_and_negative_delay()",
    '''    #[test]
    fn progress_timeline_is_reversible_and_ignores_wall_clock() {
        let t = CssAnimationTiming {
            delay: 99.0,
            iteration_count: AnimationIterationCount::Number(2.0),
            direction: AnimationDirection::Alternate,
            ..timing()
        };
        assert_eq!(t.sample_timeline_progress(Some(0.25)).progress, Some(0.5));
        assert_eq!(t.sample_timeline_progress(Some(0.75)).progress, Some(0.5));
        assert!(!t.sample_timeline_progress(Some(1.0)).finished);
        assert_eq!(t.sample_timeline_progress(None).progress, None);
    }

''',
)

# ---------------------------------------------------------------------------
# AnimationState external timeline sampling state.
# ---------------------------------------------------------------------------
state = "crates/vizia_core/src/animation/animation_state.rs"
replace_once(
    state,
    '''    pub css_composition: AnimationComposition,
''',
    '''    pub css_composition: AnimationComposition,
    pub css_timeline_driven: bool,
    pub css_timeline_progress: Option<f32>,
''',
)
replace_once(
    state,
    '''            css_composition: AnimationComposition::Replace,
        }
''',
    '''            css_composition: AnimationComposition::Replace,
            css_timeline_driven: false,
            css_timeline_progress: None,
        }
''',
)
# second constructor
p = Path(state)
text = p.read_text()
old = '''            css_composition: AnimationComposition::Replace,
        }
'''
if old in text:
    text = text.replace(old, '''            css_composition: AnimationComposition::Replace,
            css_timeline_driven: false,
            css_timeline_progress: None,
        }
''', 1)
    p.write_text(text)

# ---------------------------------------------------------------------------
# Property stores can be switched between document and progress-based sampling.
# ---------------------------------------------------------------------------
for store in [
    "crates/vizia_core/src/storage/animatable_set.rs",
    "crates/vizia_core/src/storage/animatable_var_set.rs",
]:
    insert_before(
        store,
        "    fn refresh_css_composed_outputs(&mut self) {\n",
        '''    pub(crate) fn set_css_timeline_progress(
        &mut self,
        entity: Entity,
        instance_id: u64,
        driven: bool,
        progress: Option<f32>,
    ) {
        for state in self.active_animations.iter_mut() {
            if state.css_instance_id == Some(instance_id) && state.entities.contains(&entity) {
                state.css_timeline_driven = driven;
                state.css_timeline_progress = progress;
                if driven {
                    // Progress timelines are reversible, so reaching 100% must not remove the effect.
                    state.t = 0.0;
                }
            }
        }
    }

''',
    )
    replace_once(
        store,
        '''            if let Some(clock) = &state.css_clock {
                let sample = clock.sample(time);
                state.t = if sample.finished { 1.0 } else { 0.0 };
''',
        '''            if let Some(clock) = &state.css_clock {
                let sample = if state.css_timeline_driven {
                    clock.timing.sample_timeline_progress(state.css_timeline_progress)
                } else {
                    clock.sample(time)
                };
                state.t = if state.css_timeline_driven {
                    0.0
                } else if sample.finished {
                    1.0
                } else {
                    0.0
                };
''',
    )

# ---------------------------------------------------------------------------
# Style computed timeline list and sparse source registry.
# ---------------------------------------------------------------------------
style = "crates/vizia_core/src/style/mod.rs"
replace_once(
    style,
    '''use crate::animation::{
    AnimationEvent, AnimationState, Compositor, Interpolator, Keyframe, TimingFunction,
};
''',
    '''use crate::animation::{
    AnimationEvent, AnimationState, Compositor, Interpolator, Keyframe, ScrollTimelineSource,
    TimingFunction,
};
''',
)
replace_once(
    style,
    '''    AnimationDurations, AnimationFillModes, AnimationIterationCounts, AnimationNames,
    AnimationPlayStates, AnimationTimingFunctions, BlendMode, KeyframeSelector, ParserOptions,
''',
    '''    AnimationDurations, AnimationFillModes, AnimationIterationCounts, AnimationNames,
    AnimationPlayStates, AnimationTimeline, AnimationTimelines, AnimationTimingFunctions, BlendMode,
    KeyframeSelector, ParserOptions,
''',
)
replace_once(
    style,
    '''    pub(crate) animation_composition: StyleSet<AnimationCompositions>,
    pub(crate) css_animation_instances: HashMap<Entity, Vec<CssAnimationInstance>>,
''',
    '''    pub(crate) animation_composition: StyleSet<AnimationCompositions>,
    pub(crate) animation_timeline: StyleSet<AnimationTimelines>,
    pub(crate) css_animation_instances: HashMap<Entity, Vec<CssAnimationInstance>>,
    pub(crate) scroll_timeline_sources: HashMap<Entity, ScrollTimelineSource>,
    pub(crate) named_scroll_timelines: HashMap<String, Entity>,
''',
)
replace_once(
    style,
    '''            Property::AnimationComposition(value) => {
                self.animation_composition.insert_rule(rule_id, value.clone());
                return;
            }
            Property::Animation(value) => {
''',
    '''            Property::AnimationComposition(value) => {
                self.animation_composition.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationTimeline(value) => {
                self.animation_timeline.insert_rule(rule_id, value.clone());
                return;
            }
            Property::Animation(value) => {
''',
)
replace_once(
    style,
    '''                self.animation_composition.insert_rule(
                    rule_id,
                    AnimationCompositions(
                        value.0.iter().map(|_| AnimationComposition::Replace).collect(),
                    ),
                );
                return;
''',
    '''                self.animation_composition.insert_rule(
                    rule_id,
                    AnimationCompositions(
                        value.0.iter().map(|_| AnimationComposition::Replace).collect(),
                    ),
                );
                self.animation_timeline.insert_rule(
                    rule_id,
                    AnimationTimelines(value.0.iter().map(|_| AnimationTimeline::Auto).collect()),
                );
                return;
''',
)

style_system = "crates/vizia_core/src/systems/style.rs"
replace_once(
    style_system,
    '''        cx.style.animation_play_state.link(entity, rules);
        cx.style.animation_composition.link(entity, rules);
''',
    '''        cx.style.animation_play_state.link(entity, rules);
        cx.style.animation_composition.link(entity, rules);
        cx.style.animation_timeline.link(entity, rules);
''',
)

# ---------------------------------------------------------------------------
# CSS runtime stores the resolved timeline and propagates sampled progress.
# ---------------------------------------------------------------------------
css_runtime = "crates/vizia_core/src/style/css_animation.rs"
replace_once(
    css_runtime,
    '''    AnimationComposition, AnimationDirection, AnimationFillMode, AnimationIterationCount,
    AnimationName, AnimationPlayState, EasingFunction,
''',
    '''    AnimationComposition, AnimationDirection, AnimationFillMode, AnimationIterationCount,
    AnimationName, AnimationPlayState, AnimationTimeline, EasingFunction,
''',
)
replace_once(
    css_runtime,
    '''    pub composition: AnimationComposition,
    pub started: bool,
''',
    '''    pub composition: AnimationComposition,
    pub timeline: AnimationTimeline,
    pub timeline_driven: bool,
    pub timeline_progress: Option<f32>,
    pub started: bool,
''',
)
replace_once(
    css_runtime,
    '''    composition: AnimationComposition,
}
''',
    '''    composition: AnimationComposition,
    timeline: AnimationTimeline,
}
''',
)
replace_once(
    css_runtime,
    '''        let compositions =
            self.animation_composition.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let reduce_motion = self.reduced_motion_override.unwrap_or(self.system_reduced_motion);
''',
    '''        let compositions =
            self.animation_composition.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let timelines = self.animation_timeline.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let reduce_motion = self.reduced_motion_override.unwrap_or(self.system_reduced_motion);
''',
)
replace_once(
    css_runtime,
    '''                    composition: repeated(compositions, index, AnimationComposition::Replace),
                })
''',
    '''                    composition: repeated(compositions, index, AnimationComposition::Replace),
                    timeline: repeated(timelines, index, AnimationTimeline::Auto),
                })
''',
)
insert_before(
    css_runtime,
    "    fn stop_css_on_stores(&mut self, entity: Entity, instance_id: u64) {\n",
    '''    pub(crate) fn set_css_timeline_progress(
        &mut self,
        entity: Entity,
        instance_id: u64,
        driven: bool,
        progress: Option<f32>,
    ) {
        if let Some(instances) = self.css_animation_instances.get_mut(&entity) {
            if let Some(instance) = instances.iter_mut().find(|item| item.instance_id == instance_id) {
                instance.timeline_driven = driven;
                instance.timeline_progress = progress;
                if driven {
                    instance.ended = false;
                }
            }
        }
        macro_rules! set_progress {
            ($store:expr) => {
                $store.set_css_timeline_progress(entity, instance_id, driven, progress);
            };
        }
        set_progress!(self.display);
        set_progress!(self.opacity);
        set_progress!(self.clip_path);
        set_progress!(self.filter);
        set_progress!(self.backdrop_filter);
        set_progress!(self.transform);
        set_progress!(self.transform_origin);
        set_progress!(self.translate);
        set_progress!(self.rotate);
        set_progress!(self.scale);
        set_progress!(self.border_top_width);
        set_progress!(self.border_right_width);
        set_progress!(self.border_bottom_width);
        set_progress!(self.border_left_width);
        set_progress!(self.border_top_color);
        set_progress!(self.border_right_color);
        set_progress!(self.border_bottom_color);
        set_progress!(self.border_left_color);
        set_progress!(self.corner_top_left_radius);
        set_progress!(self.corner_top_right_radius);
        set_progress!(self.corner_bottom_left_radius);
        set_progress!(self.corner_bottom_right_radius);
        set_progress!(self.corner_top_left_smoothing);
        set_progress!(self.corner_top_right_smoothing);
        set_progress!(self.corner_bottom_left_smoothing);
        set_progress!(self.corner_bottom_right_smoothing);
        set_progress!(self.outline_width);
        set_progress!(self.outline_color);
        set_progress!(self.outline_offset);
        set_progress!(self.background_color);
        set_progress!(self.background_image);
        set_progress!(self.background_position);
        set_progress!(self.background_repeat);
        set_progress!(self.background_size);
        set_progress!(self.shadow);
        set_progress!(self.font_color);
        set_progress!(self.font_size);
        set_progress!(self.letter_spacing);
        set_progress!(self.line_height);
        set_progress!(self.caret_color);
        set_progress!(self.selection_color);
        set_progress!(self.text_decoration_color);
        set_progress!(self.fill);
        set_progress!(self.left);
        set_progress!(self.right);
        set_progress!(self.top);
        set_progress!(self.bottom);
        set_progress!(self.padding_left);
        set_progress!(self.padding_right);
        set_progress!(self.padding_top);
        set_progress!(self.padding_bottom);
        set_progress!(self.horizontal_gap);
        set_progress!(self.vertical_gap);
        set_progress!(self.width);
        set_progress!(self.height);
        set_progress!(self.min_width);
        set_progress!(self.max_width);
        set_progress!(self.min_height);
        set_progress!(self.max_height);
        set_progress!(self.min_horizontal_gap);
        set_progress!(self.max_horizontal_gap);
        set_progress!(self.min_vertical_gap);
        set_progress!(self.max_vertical_gap);
        for store in self.custom_color_props.values_mut() { set_progress!(store); }
        for store in self.custom_length_props.values_mut() { set_progress!(store); }
        for store in self.custom_font_size_props.values_mut() { set_progress!(store); }
        for store in self.custom_letter_spacing_props.values_mut() { set_progress!(store); }
        for store in self.custom_line_height_props.values_mut() { set_progress!(store); }
        for store in self.custom_units_props.values_mut() { set_progress!(store); }
        for store in self.custom_opacity_props.values_mut() { set_progress!(store); }
        for store in self.custom_shadow_props.values_mut() { set_progress!(store); }
    }

''',
)
replace_once(
    css_runtime,
    '''                    instance.composition = spec.composition;
                    self.update_css_on_stores(entity, spec, instance.instance_id, order, now);
''',
    '''                    instance.composition = spec.composition;
                    instance.timeline = spec.timeline.clone();
                    self.update_css_on_stores(entity, spec, instance.instance_id, order, now);
''',
)
replace_once(
    css_runtime,
    '''                composition: spec.composition,
                started: false,
''',
    '''                composition: spec.composition,
                timeline: spec.timeline.clone(),
                timeline_driven: false,
                timeline_progress: None,
                started: false,
''',
)
replace_once(
    css_runtime,
    '''                let sample = instance.clock.sample(now);
''',
    '''                let sample = if instance.timeline_driven {
                    instance.clock.timing.sample_timeline_progress(instance.timeline_progress)
                } else {
                    instance.clock.sample(now)
                };
''',
)
replace_once(
    css_runtime,
    '''                if sample.finished {
''',
    '''                if sample.finished && !instance.timeline_driven {
''',
)

# ---------------------------------------------------------------------------
# ScrollView publishes sparse timeline-source snapshots and optional names.
# ---------------------------------------------------------------------------
scrollview = "crates/vizia_core/src/views/scrollview.rs"
replace_once(
    scrollview,
    "use crate::prelude::*;\n",
    "use crate::{animation::ScrollTimelineSource, prelude::*};\n",
)
replace_once(
    scrollview,
    '''    /// Whether the vertical scrollbar should be visible.
    pub show_vertical_scrollbar: Signal<bool>,
}
''',
    '''    /// Whether the vertical scrollbar should be visible.
    pub show_vertical_scrollbar: Signal<bool>,
    /// Optional Vizia-native name used by CSS `animation-timeline: --name`.
    pub timeline_name: Option<String>,
}
''',
)
replace_once(
    scrollview,
    '''            show_horizontal_scrollbar,
            show_vertical_scrollbar,
        }
''',
    '''            show_horizontal_scrollbar,
            show_vertical_scrollbar,
            timeline_name: None,
        }
''',
)
replace_once(
    scrollview,
    '''            _ => {}
        });
    }
}

impl Handle<'_, ScrollView> {
''',
    '''            _ => {}
        });

        let source_entity = cx.current();
        cx.style.scroll_timeline_sources.insert(
            source_entity,
            ScrollTimelineSource {
                x: self.scroll_x.get(),
                y: self.scroll_y.get(),
                inner_width: self.inner_width.get(),
                inner_height: self.inner_height.get(),
                container_width: self.container_width.get(),
                container_height: self.container_height.get(),
            },
        );
        if let Some(name) = &self.timeline_name {
            cx.style.named_scroll_timelines.insert(name.clone(), source_entity);
        }
    }
}

impl Handle<'_, ScrollView> {
''',
)
insert_before(
    scrollview,
    "    /// Sets whether the horizontal scrollbar should be visible.\n",
    '''    /// Give this scroll container a named animation timeline source.
    /// Names conventionally use the CSS dashed-ident form (`--gallery-scroll`).
    pub fn timeline_name(self, name: impl Into<String>) -> Self {
        let name = name.into();
        self.modify(move |scrollview| scrollview.timeline_name = Some(name))
    }

''',
)

# ---------------------------------------------------------------------------
# Sparse timeline resolution in the animation system.
# ---------------------------------------------------------------------------
system = "crates/vizia_core/src/systems/animation.rs"
replace_once(
    system,
    "use crate::{layout::node::SubLayout, prelude::*};\n",
    '''use crate::{animation::view_progress, layout::node::SubLayout, prelude::*};
use vizia_style::{AnimationScroller, AnimationTimeline, AnimationTimelineAxis};
''',
)
insert_before(
    system,
    "pub(crate) fn animation_system(cx: &mut Context) -> bool {\n",
    '''fn nearest_scroll_source(cx: &Context, entity: Entity) -> Option<Entity> {
    let mut current = cx.tree.get_layout_parent(entity);
    while let Some(entity) = current {
        if cx.style.scroll_timeline_sources.contains_key(&entity) {
            return Some(entity);
        }
        current = cx.tree.get_layout_parent(entity);
    }
    None
}

fn root_scroll_source(cx: &Context, entity: Entity) -> Option<Entity> {
    let mut current = Some(entity);
    let mut result = None;
    while let Some(entity) = current {
        if cx.style.scroll_timeline_sources.contains_key(&entity) {
            result = Some(entity);
        }
        current = cx.tree.get_layout_parent(entity);
    }
    result
}

fn source_progress(cx: &Context, source: Entity, axis: AnimationTimelineAxis) -> Option<f32> {
    cx.entity_manager
        .is_alive(source)
        .then(|| cx.style.scroll_timeline_sources.get(&source).copied())
        .flatten()
        .map(|source| source.progress(axis))
}

fn view_timeline_progress(
    cx: &Context,
    entity: Entity,
    axis: AnimationTimelineAxis,
) -> Option<f32> {
    let source_entity = nearest_scroll_source(cx, entity)?;
    let source = cx.style.scroll_timeline_sources.get(&source_entity).copied()?;
    let subject = cx.cache.get_bounds(entity);
    let viewport = cx.cache.get_bounds(source_entity);
    Some(match axis {
        AnimationTimelineAxis::Block | AnimationTimelineAxis::Y => {
            let offset = (source.inner_height - source.container_height).max(0.0) * source.y;
            view_progress(subject.y, subject.h, viewport.y, viewport.h, offset)
        }
        AnimationTimelineAxis::Inline | AnimationTimelineAxis::X => {
            let offset = (source.inner_width - source.container_width).max(0.0) * source.x;
            view_progress(subject.x, subject.w, viewport.x, viewport.w, offset)
        }
    })
}

fn refresh_progress_timelines(cx: &mut Context) {
    let requests = cx
        .style
        .css_animation_instances
        .iter()
        .flat_map(|(entity, instances)| {
            instances
                .iter()
                .map(move |instance| (*entity, instance.instance_id, instance.timeline.clone()))
        })
        .collect::<Vec<_>>();

    let mut samples = Vec::with_capacity(requests.len());
    for (entity, instance_id, timeline) in requests {
        let (driven, progress) = match timeline {
            AnimationTimeline::Auto => (false, None),
            AnimationTimeline::None => (true, None),
            AnimationTimeline::Named(name) => {
                let progress = cx
                    .style
                    .named_scroll_timelines
                    .get(&name)
                    .copied()
                    .and_then(|source| source_progress(cx, source, AnimationTimelineAxis::Block));
                (true, progress)
            }
            AnimationTimeline::Scroll { scroller, axis } => {
                let source = match scroller {
                    AnimationScroller::Self_ => cx
                        .style
                        .scroll_timeline_sources
                        .contains_key(&entity)
                        .then_some(entity),
                    AnimationScroller::Nearest => nearest_scroll_source(cx, entity),
                    AnimationScroller::Root => root_scroll_source(cx, entity),
                };
                (true, source.and_then(|source| source_progress(cx, source, axis)))
            }
            AnimationTimeline::View { axis } => (true, view_timeline_progress(cx, entity, axis)),
        };
        samples.push((entity, instance_id, driven, progress));
    }

    for (entity, instance_id, driven, progress) in samples {
        cx.style.set_css_timeline_progress(entity, instance_id, driven, progress);
    }
}

''',
)
replace_once(
    system,
    '''    // Tick all animations

    let time = Instant::now();
''',
    '''    // Tick all animations

    let time = Instant::now();
    refresh_progress_timelines(cx);
''',
)
