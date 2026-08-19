from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


def insert_before(path: str, marker: str, text_to_insert: str) -> None:
    p = Path(path)
    text = p.read_text()
    if text_to_insert in text:
        return
    if marker not in text:
        raise RuntimeError(f"marker not found in {path}: {marker!r}")
    p.write_text(text.replace(marker, text_to_insert + marker, 1))


# ---------------------------------------------------------------------------
# vizia_style: animation-composition parsing/property storage
# ---------------------------------------------------------------------------
animation_values = "crates/vizia_style/src/values/animation.rs"
insert_before(
    animation_values,
    "#[derive(Debug, Clone, PartialEq)]\npub struct AnimationShorthandItem",
    '''#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AnimationComposition {
    #[default]
    Replace,
    Add,
    Accumulate,
}

impl<'i> Parse<'i> for AnimationComposition {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let ident = input.expect_ident_cloned()?;
        match_ignore_ascii_case! { &ident,
            "replace" => Ok(Self::Replace),
            "add" => Ok(Self::Add),
            "accumulate" => Ok(Self::Accumulate),
            _ => Err(location.new_unexpected_token_error(Token::Ident(ident))),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationCompositions(pub Vec<AnimationComposition>);

impl<'i> Parse<'i> for AnimationCompositions {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationComposition::parse).map(Self)
    }
}

''',
)

replace_once(
    animation_values,
    '''    #[test]
    fn parses_shorthand_time_ambiguity_and_all_level_one_fields() {
''',
    '''    #[test]
    fn parses_animation_composition_list() {
        let mut input = ParserInput::new("replace, add, accumulate");
        let mut parser = Parser::new(&mut input);
        let parsed = AnimationCompositions::parse(&mut parser).expect("composition list should parse");
        assert_eq!(
            parsed.0,
            vec![
                AnimationComposition::Replace,
                AnimationComposition::Add,
                AnimationComposition::Accumulate,
            ]
        );
    }

    #[test]
    fn parses_shorthand_time_ambiguity_and_all_level_one_fields() {
''',
)

property = "crates/vizia_style/src/property.rs"
replace_once(
    property,
    '''    Alignment, Angle, AnimationDelays, AnimationDirections, AnimationDurations, AnimationFillModes,
''',
    '''    Alignment, Angle, AnimationCompositions, AnimationDelays, AnimationDirections, AnimationDurations, AnimationFillModes,
''',
)
replace_once(
    property,
    '''        "animation-play-state": AnimationPlayState(AnimationPlayStates),
        "animation": Animation(AnimationShorthand),
''',
    '''        "animation-play-state": AnimationPlayState(AnimationPlayStates),
        "animation-composition": AnimationComposition(AnimationCompositions),
        "animation": Animation(AnimationShorthand),
''',
)

# ---------------------------------------------------------------------------
# Core animation composition trait and property-specific operations.
# ---------------------------------------------------------------------------
interpolator = "crates/vizia_core/src/animation/interpolator.rs"
replace_once(
    interpolator,
    '''    Angle, BackgroundRepeat, BackgroundSize, ClipPath, Color, ColorStop, Display, Filter, FontSize,
''',
    '''    Angle, AnimationComposition, BackgroundRepeat, BackgroundSize, ClipPath, Color, ColorStop, Display, Filter, FontSize,
''',
)
replace_once(
    interpolator,
    '''pub(crate) trait Interpolator {
    fn interpolate(start: &Self, end: &Self, t: f32) -> Self;
}
''',
    '''pub(crate) trait Interpolator {
    fn interpolate(start: &Self, end: &Self, t: f32) -> Self;
}

/// Property-specific Level 2 effect composition.
///
/// Types without a meaningful additive/accumulative operation intentionally use replacement.
pub(crate) trait Compositor: Clone {
    fn compose(
        underlying: &Self,
        effect: &Self,
        composition: AnimationComposition,
    ) -> Self;
}

macro_rules! replace_compositor {
    ($($ty:ty),+ $(,)?) => {
        $(
            impl Compositor for $ty {
                fn compose(
                    _underlying: &Self,
                    effect: &Self,
                    _composition: AnimationComposition,
                ) -> Self {
                    effect.clone()
                }
            }
        )+
    };
}

fn add_length_or_percentage(
    underlying: &LengthOrPercentage,
    effect: &LengthOrPercentage,
) -> Option<LengthOrPercentage> {
    match (underlying, effect) {
        (LengthOrPercentage::Length(a), LengthOrPercentage::Length(b)) => {
            match (a, b) {
                (Length::Value(LengthValue::Px(a)), Length::Value(LengthValue::Px(b))) => {
                    Some(LengthOrPercentage::Length(Length::px(a + b)))
                }
                _ => None,
            }
        }
        (LengthOrPercentage::Percentage(a), LengthOrPercentage::Percentage(b)) => {
            Some(LengthOrPercentage::Percentage(a + b))
        }
        _ => None,
    }
}

fn add_units(underlying: &Units, effect: &Units) -> Option<Units> {
    match (underlying, effect) {
        (Units::Pixels(a), Units::Pixels(b)) => Some(Units::Pixels(a + b)),
        (Units::Percentage(a), Units::Percentage(b)) => Some(Units::Percentage(a + b)),
        (Units::Stretch(a), Units::Stretch(b)) => Some(Units::Stretch(a + b)),
        _ => None,
    }
}

fn multiply_scale_component(
    underlying: PercentageOrNumber,
    effect: PercentageOrNumber,
) -> PercentageOrNumber {
    PercentageOrNumber::Number(underlying.to_factor() * effect.to_factor())
}

fn accumulate_transform(underlying: &Transform, effect: &Transform) -> Option<Transform> {
    match (underlying, effect) {
        (Transform::Translate((ax, ay)), Transform::Translate((bx, by))) => Some(
            Transform::Translate((add_length_or_percentage(ax, bx)?, add_length_or_percentage(ay, by)?)),
        ),
        (Transform::TranslateX(a), Transform::TranslateX(b)) => {
            Some(Transform::TranslateX(add_length_or_percentage(a, b)?))
        }
        (Transform::TranslateY(a), Transform::TranslateY(b)) => {
            Some(Transform::TranslateY(add_length_or_percentage(a, b)?))
        }
        (Transform::Rotate(a), Transform::Rotate(b)) => {
            Some(Transform::Rotate(Angle::Rad(a.to_radians() + b.to_radians())))
        }
        (Transform::Scale((ax, ay)), Transform::Scale((bx, by))) => Some(Transform::Scale((
            multiply_scale_component(*ax, *bx),
            multiply_scale_component(*ay, *by),
        ))),
        (Transform::ScaleX(a), Transform::ScaleX(b)) => {
            Some(Transform::ScaleX(multiply_scale_component(*a, *b)))
        }
        (Transform::ScaleY(a), Transform::ScaleY(b)) => {
            Some(Transform::ScaleY(multiply_scale_component(*a, *b)))
        }
        (Transform::Skew(ax, ay), Transform::Skew(bx, by)) => Some(Transform::Skew(
            Angle::Rad(ax.to_radians() + bx.to_radians()),
            Angle::Rad(ay.to_radians() + by.to_radians()),
        )),
        (Transform::SkewX(a), Transform::SkewX(b)) => {
            Some(Transform::SkewX(Angle::Rad(a.to_radians() + b.to_radians())))
        }
        (Transform::SkewY(a), Transform::SkewY(b)) => {
            Some(Transform::SkewY(Angle::Rad(a.to_radians() + b.to_radians())))
        }
        _ => None,
    }
}
''',
)

# Add concrete compositor implementations before the first Interpolator impl.
insert_before(
    interpolator,
    "// Implementations of `Interpolator` for various properties.\n",
    '''impl Compositor for f32 {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => underlying + effect,
        }
    }
}

impl Compositor for i32 {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => underlying + effect,
        }
    }
}

impl Compositor for Opacity {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => {
                Opacity((underlying.0 + effect.0).clamp(0.0, 1.0))
            }
        }
    }
}

impl Compositor for Color {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => Color::rgba(
                underlying.r().saturating_add(effect.r()),
                underlying.g().saturating_add(effect.g()),
                underlying.b().saturating_add(effect.b()),
                underlying.a().saturating_add(effect.a()),
            ),
        }
    }
}

impl Compositor for RGBA {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => RGBA::rgba(
                underlying.r().saturating_add(effect.r()),
                underlying.g().saturating_add(effect.g()),
                underlying.b().saturating_add(effect.b()),
                underlying.a().saturating_add(effect.a()),
            ),
        }
    }
}

impl Compositor for Units {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => {
                add_units(underlying, effect).unwrap_or(*effect)
            }
        }
    }
}

impl Compositor for LengthOrPercentage {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => effect.clone(),
            AnimationComposition::Add | AnimationComposition::Accumulate => {
                add_length_or_percentage(underlying, effect).unwrap_or_else(|| effect.clone())
            }
        }
    }
}

impl Compositor for Translate {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => effect.clone(),
            AnimationComposition::Add | AnimationComposition::Accumulate => Translate {
                x: add_length_or_percentage(&underlying.x, &effect.x)
                    .unwrap_or_else(|| effect.x.clone()),
                y: add_length_or_percentage(&underlying.y, &effect.y)
                    .unwrap_or_else(|| effect.y.clone()),
            },
        }
    }
}

impl Compositor for Scale {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => Scale {
                x: multiply_scale_component(underlying.x, effect.x),
                y: multiply_scale_component(underlying.y, effect.y),
            },
        }
    }
}

impl Compositor for Angle {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => *effect,
            AnimationComposition::Add | AnimationComposition::Accumulate => {
                Angle::Rad(underlying.to_radians() + effect.to_radians())
            }
        }
    }
}

impl Compositor for Vec<Transform> {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => effect.clone(),
            AnimationComposition::Add => {
                let mut result = underlying.clone();
                result.extend(effect.iter().cloned());
                result
            }
            AnimationComposition::Accumulate => {
                if underlying.len() == effect.len() {
                    let mut result = Vec::with_capacity(effect.len());
                    for (a, b) in underlying.iter().zip(effect) {
                        let Some(value) = accumulate_transform(a, b) else {
                            let mut fallback = underlying.clone();
                            fallback.extend(effect.iter().cloned());
                            return fallback;
                        };
                        result.push(value);
                    }
                    result
                } else {
                    let mut result = underlying.clone();
                    result.extend(effect.iter().cloned());
                    result
                }
            }
        }
    }
}

impl Compositor for Filter {
    fn compose(underlying: &Self, effect: &Self, composition: AnimationComposition) -> Self {
        match composition {
            AnimationComposition::Replace => effect.clone(),
            AnimationComposition::Add => {
                fn append(filter: &Filter, out: &mut Vec<Filter>) {
                    match filter {
                        Filter::None => {}
                        Filter::List(values) => out.extend(values.iter().cloned()),
                        value => out.push(value.clone()),
                    }
                }
                let mut values = Vec::new();
                append(underlying, &mut values);
                append(effect, &mut values);
                match values.len() {
                    0 => Filter::None,
                    1 => values.remove(0),
                    _ => Filter::List(values),
                }
            }
            AnimationComposition::Accumulate => match (underlying, effect) {
                (Filter::Blur(a), Filter::Blur(b)) => {
                    let a = LengthOrPercentage::Length(a.clone());
                    let b = LengthOrPercentage::Length(b.clone());
                    match add_length_or_percentage(&a, &b) {
                        Some(LengthOrPercentage::Length(value)) => Filter::Blur(value),
                        _ => effect.clone(),
                    }
                }
                (Filter::List(a), Filter::List(b)) if a.len() == b.len() => Filter::List(
                    a.iter()
                        .zip(b)
                        .map(|(a, b)| Filter::compose(a, b, AnimationComposition::Accumulate))
                        .collect(),
                ),
                _ => Filter::compose(underlying, effect, AnimationComposition::Add),
            },
        }
    }
}

replace_compositor!(
    (f32, f32),
    Display,
    ClipPath,
    LengthValue,
    Length,
    LengthPercentageOrAuto,
    PercentageOrNumber,
    ImageOrGradient,
    BackgroundSize,
    BackgroundRepeat,
    Position,
    FontSize,
    LetterSpacing,
    LineHeight,
    Shadow,
    Gradient,
    LinearGradient,
    ColorStop,
    Matrix,
);

impl<T> Compositor for Vec<T>
where
    T: Interpolator + Compositor + Clone,
{
    fn compose(_underlying: &Self, effect: &Self, _composition: AnimationComposition) -> Self {
        effect.clone()
    }
}

''',
)

# Add composition-focused tests near the end of interpolator.rs.
insert_before(
    interpolator,
    "impl Interpolator for BackgroundSize",
    '''#[cfg(test)]
mod composition_tests {
    use super::*;

    #[test]
    fn translate_add_composes_with_underlying_value() {
        let base = Translate {
            x: LengthOrPercentage::Length(Length::px(10.0)),
            y: LengthOrPercentage::Length(Length::px(5.0)),
        };
        let effect = Translate {
            x: LengthOrPercentage::Length(Length::px(20.0)),
            y: LengthOrPercentage::Length(Length::px(7.0)),
        };
        let result = Translate::compose(&base, &effect, AnimationComposition::Add);
        assert_eq!(result.x, LengthOrPercentage::Length(Length::px(30.0)));
        assert_eq!(result.y, LengthOrPercentage::Length(Length::px(12.0)));
    }

    #[test]
    fn transform_add_concatenates_effect_lists_in_order() {
        let base = vec![Transform::TranslateX(LengthOrPercentage::Length(Length::px(10.0)))];
        let effect = vec![Transform::Rotate(Angle::Deg(45.0))];
        let result = Vec::<Transform>::compose(&base, &effect, AnimationComposition::Add);
        assert_eq!(result.len(), 2);
        assert!(matches!(result[0], Transform::TranslateX(_)));
        assert!(matches!(result[1], Transform::Rotate(_)));
    }

    #[test]
    fn scale_accumulate_uses_property_specific_multiplication() {
        let base = Scale::new(2.0, 3.0);
        let effect = Scale::new(1.5, 0.5);
        let result = Scale::compose(&base, &effect, AnimationComposition::Accumulate);
        assert!((result.x.to_factor() - 3.0).abs() < 0.001);
        assert!((result.y.to_factor() - 1.5).abs() < 0.001);
    }
}

''',
)

# ---------------------------------------------------------------------------
# Animation state carries composition metadata.
# ---------------------------------------------------------------------------
state = "crates/vizia_core/src/animation/animation_state.rs"
replace_once(
    state,
    "use hashbrown::HashSet;\n",
    "use hashbrown::HashSet;\nuse vizia_style::AnimationComposition;\n",
)
replace_once(
    state,
    '''    pub css_instance_id: Option<u64>,
    pub css_order: usize,
''',
    '''    pub css_instance_id: Option<u64>,
    pub css_order: usize,
    pub css_composition: AnimationComposition,
''',
)
replace_once(
    state,
    '''            css_instance_id: None,
            css_order: 0,
''',
    '''            css_instance_id: None,
            css_order: 0,
            css_composition: AnimationComposition::Replace,
''',
)
# There are two initializers with the same tail; replace the second one too if still present.
p = Path(state)
text = p.read_text()
old_tail = '''            css_instance_id: None,
            css_order: 0,
'''
if old_tail in text:
    text = text.replace(
        old_tail,
        '''            css_instance_id: None,
            css_order: 0,
            css_composition: AnimationComposition::Replace,
''',
        1,
    )
    p.write_text(text)

# ---------------------------------------------------------------------------
# Export Compositor inside core animation module.
# ---------------------------------------------------------------------------
mod = "crates/vizia_core/src/animation/mod.rs"
replace_once(
    mod,
    "pub(crate) use interpolator::Interpolator;",
    "pub(crate) use interpolator::{Compositor, Interpolator};",
)

# ---------------------------------------------------------------------------
# Style computed property + shorthand reset to replace.
# ---------------------------------------------------------------------------
style_mod = "crates/vizia_core/src/style/mod.rs"
replace_once(
    style_mod,
    '''    AnimationDelays, AnimationDirections, AnimationDurations, AnimationFillModes,
    AnimationIterationCounts, AnimationNames, AnimationPlayStates, AnimationTimingFunctions,
''',
    '''    AnimationComposition, AnimationCompositions, AnimationDelays, AnimationDirections,
    AnimationDurations, AnimationFillModes, AnimationIterationCounts, AnimationNames,
    AnimationPlayStates, AnimationTimingFunctions,
''',
)
replace_once(
    style_mod,
    '''    pub(crate) animation_fill_mode: StyleSet<AnimationFillModes>,
    pub(crate) animation_play_state: StyleSet<AnimationPlayStates>,
''',
    '''    pub(crate) animation_fill_mode: StyleSet<AnimationFillModes>,
    pub(crate) animation_play_state: StyleSet<AnimationPlayStates>,
    pub(crate) animation_composition: StyleSet<AnimationCompositions>,
''',
)
replace_once(
    style_mod,
    '''            Property::AnimationPlayState(value) => {
                self.animation_play_state.insert_rule(rule_id, value.clone());
                return;
            }
            Property::Animation(value) => {
''',
    '''            Property::AnimationPlayState(value) => {
                self.animation_play_state.insert_rule(rule_id, value.clone());
                return;
            }
            Property::AnimationComposition(value) => {
                self.animation_composition.insert_rule(rule_id, value.clone());
                return;
            }
            Property::Animation(value) => {
''',
)
replace_once(
    style_mod,
    '''                self.animation_play_state.insert_rule(
                    rule_id,
                    AnimationPlayStates(value.0.iter().map(|item| item.play_state).collect()),
                );
                return;
''',
    '''                self.animation_play_state.insert_rule(
                    rule_id,
                    AnimationPlayStates(value.0.iter().map(|item| item.play_state).collect()),
                );
                self.animation_composition.insert_rule(
                    rule_id,
                    AnimationCompositions(
                        value.0.iter().map(|_| AnimationComposition::Replace).collect(),
                    ),
                );
                return;
''',
)

style_system = "crates/vizia_core/src/systems/style.rs"
replace_once(
    style_system,
    '''        cx.style.animation_fill_mode.link(entity, rules);
        cx.style.animation_play_state.link(entity, rules);
''',
    '''        cx.style.animation_fill_mode.link(entity, rules);
        cx.style.animation_play_state.link(entity, rules);
        cx.style.animation_composition.link(entity, rules);
''',
)

# ---------------------------------------------------------------------------
# CSS animation resolution passes composition into every property store.
# ---------------------------------------------------------------------------
css_animation = "crates/vizia_core/src/style/css_animation.rs"
replace_once(
    css_animation,
    '''    AnimationDirection, AnimationFillMode, AnimationIterationCount, AnimationName,
    AnimationPlayState, EasingFunction,
''',
    '''    AnimationComposition, AnimationDirection, AnimationFillMode, AnimationIterationCount,
    AnimationName, AnimationPlayState, EasingFunction,
''',
)
replace_once(
    css_animation,
    '''    pub default_timing: TimingFunction,
    pub started: bool,
''',
    '''    pub default_timing: TimingFunction,
    pub composition: AnimationComposition,
    pub started: bool,
''',
)
replace_once(
    css_animation,
    '''    timing: CssAnimationTiming,
    default_timing: TimingFunction,
''',
    '''    timing: CssAnimationTiming,
    default_timing: TimingFunction,
    composition: AnimationComposition,
''',
)
replace_once(
    css_animation,
    '''        let states = self.animation_play_state.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let reduce_motion = self.reduced_motion_override.unwrap_or(self.system_reduced_motion);
''',
    '''        let states = self.animation_play_state.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let compositions =
            self.animation_composition.get(entity).map(|v| v.0.as_slice()).unwrap_or(&[]);
        let reduce_motion = self.reduced_motion_override.unwrap_or(self.system_reduced_motion);
''',
)
replace_once(
    css_animation,
    '''                    default_timing: TimingFunction::from_easing(easing),
                })
''',
    '''                    default_timing: TimingFunction::from_easing(easing),
                    composition: repeated(
                        compositions,
                        index,
                        AnimationComposition::Replace,
                    ),
                })
''',
)
replace_once(
    css_animation,
    '''                    spec.default_timing,
                    &timeline,
''',
    '''                    spec.default_timing,
                    spec.composition,
                    &timeline,
''',
)
replace_once(
    css_animation,
    '''                    spec.timing,
                    spec.default_timing,
                    now,
''',
    '''                    spec.timing,
                    spec.default_timing,
                    spec.composition,
                    now,
''',
)
replace_once(
    css_animation,
    '''                    instance.default_timing = spec.default_timing;
                    self.update_css_on_stores(entity, spec, instance.instance_id, order, now);
''',
    '''                    instance.default_timing = spec.default_timing;
                    instance.composition = spec.composition;
                    self.update_css_on_stores(entity, spec, instance.instance_id, order, now);
''',
)
replace_once(
    css_animation,
    '''                default_timing: spec.default_timing,
                started: false,
''',
    '''                default_timing: spec.default_timing,
                composition: spec.composition,
                started: false,
''',
)

# ---------------------------------------------------------------------------
# Both property-store variants keep a cached composed CSS result so get() can
# continue returning references without allocating on every draw/query.
# ---------------------------------------------------------------------------
for store_path in [
    "crates/vizia_core/src/storage/animatable_set.rs",
    "crates/vizia_core/src/storage/animatable_var_set.rs",
]:
    if store_path.endswith("animatable_set.rs"):
        replace_once(
            store_path,
            '''use crate::animation::{
    AnimationState, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,
};
''',
            '''use crate::animation::{
    AnimationState, Compositor, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,
};
''',
        )
        replace_once(
            store_path,
            "use vizia_storage::{SparseSet, SparseSetGeneric, SparseSetIndex};\n",
            "use hashbrown::{HashMap, HashSet};\nuse vizia_storage::{SparseSet, SparseSetGeneric, SparseSetIndex};\nuse vizia_style::AnimationComposition;\n",
        )
    else:
        replace_once(
            store_path,
            '''use crate::animation::{
    AnimationState, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,
};
''',
            '''use crate::animation::{
    AnimationState, Compositor, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,
};
''',
        )
        replace_once(
            store_path,
            "use hashbrown::{HashMap, HashSet};\n",
            "use hashbrown::{HashMap, HashSet};\nuse vizia_style::AnimationComposition;\n",
        )

    replace_once(
        store_path,
        '''    /// Animations which are currently playing
    active_animations: Vec<AnimationState<T>>,
''',
        '''    /// Animations which are currently playing
    active_animations: Vec<AnimationState<T>>,
    /// Final Level 2 CSS effect-stack result per entity.
    css_composed_outputs: HashMap<Entity, T>,
''',
    )

    # Extend generic bounds with Compositor.
    replace_once(
        store_path,
        "    T: 'static + Default + Clone + Interpolator + PartialEq + std::fmt::Debug,",
        "    T: 'static + Default + Clone + Interpolator + Compositor + PartialEq + std::fmt::Debug,",
    )

    # Remove cached result when entity data is removed.
    replace_once(
        store_path,
        '''    pub fn remove(&mut self, entity: Entity) -> Option<T> {
        let entity_index = entity.index();
''',
        '''    pub fn remove(&mut self, entity: Entity) -> Option<T> {
        self.css_composed_outputs.remove(&entity);
        let entity_index = entity.index();
''',
    )

    # Add composition argument to play_css_animation.
    replace_once(
        store_path,
        '''        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        timeline: &[(f32, TimingFunction)],
''',
        '''        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        composition: AnimationComposition,
        timeline: &[(f32, TimingFunction)],
''',
    )
    replace_once(
        store_path,
        '''        state.css_instance_id = Some(instance_id);
        state.css_order = order;
        state.output = None;
''',
        '''        state.css_instance_id = Some(instance_id);
        state.css_order = order;
        state.css_composition = composition;
        state.output = None;
''',
    )

    # Add composition argument to update_css_animation and update state.
    replace_once(
        store_path,
        '''        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        now: Instant,
''',
        '''        timing: CssAnimationTiming,
        default_timing: TimingFunction,
        composition: AnimationComposition,
        now: Instant,
''',
    )
    replace_once(
        store_path,
        '''                state.css_order = order;
                state.update_css_timing(timing, default_timing, now);
''',
        '''                state.css_order = order;
                state.css_composition = composition;
                state.update_css_timing(timing, default_timing, now);
''',
    )

    # Add effect-stack refresh helper before stop_css_animation.
    insert_before(
        store_path,
        "    pub(crate) fn stop_css_animation(&mut self, entity: Entity, instance_id: u64) {\n",
        '''    fn refresh_css_composed_outputs(&mut self) {
        let mut effects: HashMap<
            Entity,
            Vec<(usize, u64, AnimationComposition, T)>,
        > = HashMap::new();

        for state in &self.active_animations {
            let Some(instance_id) = state.css_instance_id else {
                continue;
            };
            let Some(output) = state.get_output() else {
                continue;
            };
            for entity in state.entities.iter().copied() {
                effects.entry(entity).or_default().push((
                    state.css_order,
                    instance_id,
                    state.css_composition,
                    output.clone(),
                ));
            }
        }

        let bases = effects
            .keys()
            .copied()
            .map(|entity| (entity, self.get_base(entity).cloned().unwrap_or_default()))
            .collect::<HashMap<_, _>>();

        self.css_composed_outputs.clear();
        for (entity, mut stack) in effects {
            stack.sort_by_key(|(order, instance_id, _, _)| (*order, *instance_id));
            let mut value = bases.get(&entity).cloned().unwrap_or_default();
            for (_, _, composition, effect) in stack {
                value = T::compose(&value, &effect, composition);
            }
            self.css_composed_outputs.insert(entity, value);
        }
    }

''',
    )

    replace_once(
        store_path,
        '''        }
        self.refresh_animation_index(entity);
    }

    /// Stop an active animation for the given entity.
''',
        '''        }
        self.refresh_animation_index(entity);
        self.refresh_css_composed_outputs();
    }

    /// Stop an active animation for the given entity.
''',
    )

    # If no animation needs ticking, still preserve/recompute forwards-filled composition output.
    replace_once(
        store_path,
        '''        if !self.has_animations() {
            return Vec::new();
        }
''',
        '''        if !self.has_animations() {
            self.refresh_css_composed_outputs();
            return Vec::new();
        }
''',
    )

    # Recompute stack after all state outputs are sampled.
    replace_once(
        store_path,
        '''        self.active_animations
            .iter()
            .filter(|state| state.t < 1.0)
            .flat_map(|state| state.entities.iter().copied())
            .collect()
    }
''',
        '''        self.refresh_css_composed_outputs();

        self.active_animations
            .iter()
            .filter(|state| state.t < 1.0)
            .flat_map(|state| state.entities.iter().copied())
            .collect()
    }
''',
    )

    # Replace winner-takes-all get() block with composed cache lookup.
    old_get = '''            // CSS animations override transitions/base style. The greatest current list order wins.
            let mut css_output = None;
            let mut css_order = 0usize;
            for state in &self.active_animations {
                if state.css_instance_id.is_some() && state.entities.contains(&entity) {
                    if let Some(output) = state.get_output() {
                        if css_output.is_none() || state.css_order >= css_order {
                            css_order = state.css_order;
                            css_output = Some(output);
                        }
                    }
                }
            }
            if let Some(output) = css_output {
                return Some(output);
            }
'''
    new_get = '''            // CSS Animations Level 2 effect stack, already sampled in stable composite order.
            if let Some(output) = self.css_composed_outputs.get(&entity) {
                return Some(output);
            }
'''
    replace_once(store_path, old_get, new_get)

# VarSet's get_resolved() must also see the composed CSS output before legacy transitions/variables.
var_store = "crates/vizia_core/src/storage/animatable_var_set.rs"
replace_once(
    var_store,
    '''        if entity_index < self.inline_data.sparse.len() {
            // An active animation on this property itself takes priority.
            let animation_index = self.inline_data.sparse[entity_index].anim_index as usize;
''',
    '''        if entity_index < self.inline_data.sparse.len() {
            if let Some(output) = self.css_composed_outputs.get(&entity) {
                return Some(output.clone());
            }

            // An active legacy/transition animation on this property itself takes priority.
            let animation_index = self.inline_data.sparse[entity_index].anim_index as usize;
''',
)

# ---------------------------------------------------------------------------
# Focused core test: two CSS effects compose in stable order on Translate.
# ---------------------------------------------------------------------------
style_mod = "crates/vizia_core/src/style/mod.rs"
replace_once(
    style_mod,
    '''    #[test]
    fn backdrop_filter_keyframes_are_registered_played_and_interpolated() {
''',
    '''    #[test]
    fn level_two_translate_effect_stack_adds_in_stable_order() {
        let mut style = Style::default();
        let first = style.add_animation(
            AnimationBuilder::new()
                .keyframe(0.0, |key| key.translate((10.0, 0.0)))
                .keyframe(1.0, |key| key.translate((10.0, 0.0))),
        );
        let second = style.add_animation(
            AnimationBuilder::new()
                .keyframe(0.0, |key| key.translate((20.0, 0.0)))
                .keyframe(1.0, |key| key.translate((20.0, 0.0))),
        );
        let entity = Entity::root();
        style.translate.insert(entity, Translate::default());
        let now = Instant::now();
        let timing = CssAnimationTiming {
            duration: 1.0,
            fill_mode: AnimationFillMode::Both,
            ..Default::default()
        };

        style.translate.play_css_animation(
            entity,
            first,
            10,
            0,
            now,
            timing,
            TimingFunction::linear(),
            AnimationComposition::Add,
            &[],
        );
        style.translate.play_css_animation(
            entity,
            second,
            11,
            1,
            now,
            timing,
            TimingFunction::linear(),
            AnimationComposition::Add,
            &[],
        );
        style.translate.tick(now + Duration::from_millis(500));

        let value = style.translate.get(entity).expect("composed translate output");
        assert_eq!(
            value.x,
            LengthOrPercentage::Length(Length::px(30.0)),
            "two additive effects should compose instead of the later one replacing the first",
        );
    }

    #[test]
    fn backdrop_filter_keyframes_are_registered_played_and_interpolated() {
''',
)
