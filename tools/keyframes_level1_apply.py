from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1))


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


# ---------------------------------------------------------------------------
# vizia_style: CSS animation values / shorthand / easing
# ---------------------------------------------------------------------------
write(
    "crates/vizia_style/src/values/animation.rs",
    r'''use crate::{CustomParseError, EasingFunction, Parse};
use cssparser::{ParseError, ParseErrorKind, Parser, Token};

#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
pub enum AnimationName {
    #[default]
    None,
    Custom(String),
}

impl<'i> Parse<'i> for AnimationName {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let ident = input.expect_ident_cloned()?;
        if ident.as_ref().eq_ignore_ascii_case("none") {
            Ok(Self::None)
        } else {
            Ok(Self::Custom(ident.to_string()))
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct AnimationNames(pub Vec<AnimationName>);

impl<'i> Parse<'i> for AnimationNames {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationName::parse).map(Self)
    }
}

/// A CSS animation time in seconds. Unlike `std::time::Duration`, this can represent
/// the negative values permitted by `animation-delay`.
#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct AnimationTime(pub f32);

impl AnimationTime {
    pub fn seconds(self) -> f32 {
        self.0
    }
}

impl<'i> Parse<'i> for AnimationTime {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        match input.next()? {
            Token::Dimension { value, unit, .. } if unit.as_ref().eq_ignore_ascii_case("s") => {
                Ok(Self(*value))
            }
            Token::Dimension { value, unit, .. } if unit.as_ref().eq_ignore_ascii_case("ms") => {
                Ok(Self(*value / 1000.0))
            }
            token => Err(location.new_unexpected_token_error(token.clone())),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct AnimationDuration(pub AnimationTime);

impl<'i> Parse<'i> for AnimationDuration {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let time = AnimationTime::parse(input)?;
        if time.0 < 0.0 {
            return Err(ParseError {
                kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),
                location,
            });
        }
        Ok(Self(time))
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationDurations(pub Vec<AnimationDuration>);

impl<'i> Parse<'i> for AnimationDurations {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationDuration::parse).map(Self)
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationDelays(pub Vec<AnimationTime>);

impl<'i> Parse<'i> for AnimationDelays {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationTime::parse).map(Self)
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationTimingFunctions(pub Vec<EasingFunction>);

impl<'i> Parse<'i> for AnimationTimingFunctions {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(EasingFunction::parse).map(Self)
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AnimationIterationCount {
    Number(f32),
    Infinite,
}

impl Default for AnimationIterationCount {
    fn default() -> Self {
        Self::Number(1.0)
    }
}

impl<'i> Parse<'i> for AnimationIterationCount {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        if input.try_parse(|i| i.expect_ident_matching("infinite")).is_ok() {
            return Ok(Self::Infinite);
        }
        let location = input.current_source_location();
        let count = input.expect_number()?;
        if count < 0.0 {
            return Err(ParseError {
                kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),
                location,
            });
        }
        Ok(Self::Number(count))
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationIterationCounts(pub Vec<AnimationIterationCount>);

impl<'i> Parse<'i> for AnimationIterationCounts {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationIterationCount::parse).map(Self)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AnimationDirection {
    #[default]
    Normal,
    Reverse,
    Alternate,
    AlternateReverse,
}

impl<'i> Parse<'i> for AnimationDirection {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let ident = input.expect_ident_cloned()?;
        match_ignore_ascii_case! { &ident,
            "normal" => Ok(Self::Normal),
            "reverse" => Ok(Self::Reverse),
            "alternate" => Ok(Self::Alternate),
            "alternate-reverse" => Ok(Self::AlternateReverse),
            _ => Err(location.new_unexpected_token_error(Token::Ident(ident))),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationDirections(pub Vec<AnimationDirection>);

impl<'i> Parse<'i> for AnimationDirections {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationDirection::parse).map(Self)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AnimationFillMode {
    #[default]
    None,
    Forwards,
    Backwards,
    Both,
}

impl<'i> Parse<'i> for AnimationFillMode {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let ident = input.expect_ident_cloned()?;
        match_ignore_ascii_case! { &ident,
            "none" => Ok(Self::None),
            "forwards" => Ok(Self::Forwards),
            "backwards" => Ok(Self::Backwards),
            "both" => Ok(Self::Both),
            _ => Err(location.new_unexpected_token_error(Token::Ident(ident))),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationFillModes(pub Vec<AnimationFillMode>);

impl<'i> Parse<'i> for AnimationFillModes {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationFillMode::parse).map(Self)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AnimationPlayState {
    #[default]
    Running,
    Paused,
}

impl<'i> Parse<'i> for AnimationPlayState {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let ident = input.expect_ident_cloned()?;
        match_ignore_ascii_case! { &ident,
            "running" => Ok(Self::Running),
            "paused" => Ok(Self::Paused),
            _ => Err(location.new_unexpected_token_error(Token::Ident(ident))),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationPlayStates(pub Vec<AnimationPlayState>);

impl<'i> Parse<'i> for AnimationPlayStates {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationPlayState::parse).map(Self)
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct AnimationShorthandItem {
    pub name: AnimationName,
    pub duration: AnimationDuration,
    pub timing_function: EasingFunction,
    pub delay: AnimationTime,
    pub iteration_count: AnimationIterationCount,
    pub direction: AnimationDirection,
    pub fill_mode: AnimationFillMode,
    pub play_state: AnimationPlayState,
}

impl Default for AnimationShorthandItem {
    fn default() -> Self {
        Self {
            name: AnimationName::None,
            duration: AnimationDuration::default(),
            timing_function: EasingFunction::Ease,
            delay: AnimationTime::default(),
            iteration_count: AnimationIterationCount::default(),
            direction: AnimationDirection::default(),
            fill_mode: AnimationFillMode::default(),
            play_state: AnimationPlayState::default(),
        }
    }
}

impl<'i> Parse<'i> for AnimationShorthandItem {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let mut result = Self::default();
        let mut duration = false;
        let mut delay = false;
        let mut timing = false;
        let mut iteration = false;
        let mut direction = false;
        let mut fill = false;
        let mut state = false;
        let mut name = false;

        while !input.is_exhausted() {
            if let Ok(time) = input.try_parse(AnimationTime::parse) {
                if !duration {
                    if time.0 < 0.0 {
                        return Err(ParseError {
                            kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),
                            location,
                        });
                    }
                    result.duration = AnimationDuration(time);
                    duration = true;
                    continue;
                }
                if !delay {
                    result.delay = time;
                    delay = true;
                    continue;
                }
                return Err(ParseError {
                    kind: ParseErrorKind::Custom(CustomParseError::InvalidDeclaration),
                    location,
                });
            }

            if !timing {
                if let Ok(value) = input.try_parse(EasingFunction::parse) {
                    result.timing_function = value;
                    timing = true;
                    continue;
                }
            }
            if !iteration {
                if let Ok(value) = input.try_parse(AnimationIterationCount::parse) {
                    result.iteration_count = value;
                    iteration = true;
                    continue;
                }
            }
            if !direction {
                if let Ok(value) = input.try_parse(AnimationDirection::parse) {
                    result.direction = value;
                    direction = true;
                    continue;
                }
            }
            if !fill {
                if let Ok(value) = input.try_parse(AnimationFillMode::parse) {
                    result.fill_mode = value;
                    fill = true;
                    continue;
                }
            }
            if !state {
                if let Ok(value) = input.try_parse(AnimationPlayState::parse) {
                    result.play_state = value;
                    state = true;
                    continue;
                }
            }
            if !name {
                if let Ok(value) = input.try_parse(AnimationName::parse) {
                    result.name = value;
                    name = true;
                    continue;
                }
            }

            let token = input.next()?.clone();
            return Err(location.new_unexpected_token_error(token));
        }

        Ok(result)
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct AnimationShorthand(pub Vec<AnimationShorthandItem>);

impl<'i> Parse<'i> for AnimationShorthand {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        input.parse_comma_separated(AnimationShorthandItem::parse).map(Self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use cssparser::ParserInput;

    fn parse_shorthand(text: &str) -> AnimationShorthand {
        let mut input = ParserInput::new(text);
        let mut parser = Parser::new(&mut input);
        AnimationShorthand::parse(&mut parser).expect("animation shorthand should parse")
    }

    #[test]
    fn parses_shorthand_time_ambiguity_and_all_level_one_fields() {
        let parsed = parse_shorthand(
            "slide 250ms ease-in -100ms 2.5 alternate-reverse both paused",
        );
        let item = &parsed.0[0];
        assert_eq!(item.name, AnimationName::Custom("slide".into()));
        assert_eq!(item.duration.0, AnimationTime(0.25));
        assert_eq!(item.delay, AnimationTime(-0.1));
        assert_eq!(item.iteration_count, AnimationIterationCount::Number(2.5));
        assert_eq!(item.direction, AnimationDirection::AlternateReverse);
        assert_eq!(item.fill_mode, AnimationFillMode::Both);
        assert_eq!(item.play_state, AnimationPlayState::Paused);
        assert_eq!(item.timing_function, EasingFunction::EaseIn);
    }

    #[test]
    fn parses_comma_separated_animations() {
        let parsed = parse_shorthand("fade 1s, spin 2s linear infinite reverse forwards");
        assert_eq!(parsed.0.len(), 2);
        assert_eq!(parsed.0[1].name, AnimationName::Custom("spin".into()));
        assert_eq!(parsed.0[1].iteration_count, AnimationIterationCount::Infinite);
    }

    #[test]
    fn rejects_negative_duration_but_accepts_negative_delay() {
        let mut input = ParserInput::new("fade -1s");
        let mut parser = Parser::new(&mut input);
        assert!(AnimationShorthand::parse(&mut parser).is_err());

        let parsed = parse_shorthand("fade 1s -250ms");
        assert_eq!(parsed.0[0].delay, AnimationTime(-0.25));
    }
}
''',
)

replace_once(
    "crates/vizia_style/src/values/mod.rs",
    "pub mod alignment;\n",
    "pub mod alignment;\npub mod animation;\n",
)
replace_once(
    "crates/vizia_style/src/values/mod.rs",
    "pub use alignment::*;\n",
    "pub use alignment::*;\npub use animation::*;\n",
)

write(
    "crates/vizia_style/src/values/easing.rs",
    r'''use crate::{CustomParseError, Parse};
use cssparser::{ParseError, ParseErrorKind, Parser, Token};

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub enum StepPosition {
    JumpStart,
    #[default]
    JumpEnd,
    JumpNone,
    JumpBoth,
    Start,
    End,
}

impl<'i> Parse<'i> for StepPosition {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        let ident = input.expect_ident_cloned()?;
        match_ignore_ascii_case! { &ident,
            "jump-start" => Ok(Self::JumpStart),
            "jump-end" => Ok(Self::JumpEnd),
            "jump-none" => Ok(Self::JumpNone),
            "jump-both" => Ok(Self::JumpBoth),
            "start" => Ok(Self::Start),
            "end" => Ok(Self::End),
            _ => Err(location.new_unexpected_token_error(Token::Ident(ident))),
        }
    }
}

#[derive(Debug, Default, Clone, Copy, PartialEq)]
pub enum EasingFunction {
    Linear,
    #[default]
    Ease,
    EaseIn,
    EaseOut,
    EaseInOut,
    CubicBezier(f32, f32, f32, f32),
    Steps(u32, StepPosition),
}

impl<'i> Parse<'i> for EasingFunction {
    fn parse<'t>(input: &mut Parser<'i, 't>) -> Result<Self, ParseError<'i, CustomParseError<'i>>> {
        let location = input.current_source_location();
        if let Ok(ident) = input.try_parse(|i| i.expect_ident_cloned()) {
            let keyword = match_ignore_ascii_case! { &ident,
                "linear" => EasingFunction::Linear,
                "ease" => EasingFunction::Ease,
                "ease-in" => EasingFunction::EaseIn,
                "ease-out" => EasingFunction::EaseOut,
                "ease-in-out" => EasingFunction::EaseInOut,
                "step-start" => EasingFunction::Steps(1, StepPosition::Start),
                "step-end" => EasingFunction::Steps(1, StepPosition::End),
                _ => return Err(location.new_unexpected_token_error(Token::Ident(ident.clone()))),
            };
            return Ok(keyword);
        }

        let function = input.expect_function()?.clone();
        input.parse_nested_block(|input| {
            match_ignore_ascii_case! { &function,
                "cubic-bezier" => {
                    let x1 = input.expect_number()?;
                    input.expect_comma()?;
                    let y1 = input.expect_number()?;
                    input.expect_comma()?;
                    let x2 = input.expect_number()?;
                    input.expect_comma()?;
                    let y2 = input.expect_number()?;
                    if !(0.0..=1.0).contains(&x1) || !(0.0..=1.0).contains(&x2) {
                        return Err(ParseError {
                            kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),
                            location,
                        });
                    }
                    Ok(EasingFunction::CubicBezier(x1, y1, x2, y2))
                },
                "steps" => {
                    let count = input.expect_integer()?;
                    if count <= 0 {
                        return Err(ParseError {
                            kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),
                            location,
                        });
                    }
                    let position = input.try_parse(|input| {
                        input.expect_comma()?;
                        StepPosition::parse(input)
                    }).unwrap_or_default();
                    if position == StepPosition::JumpNone && count == 1 {
                        return Err(ParseError {
                            kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),
                            location,
                        });
                    }
                    Ok(EasingFunction::Steps(count as u32, position))
                },
                _ => Err(location.new_unexpected_token_error(Token::Ident(function.clone())))
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use cssparser::ParserInput;

    fn parse(text: &str) -> Result<EasingFunction, ()> {
        let mut input = ParserInput::new(text);
        let mut parser = Parser::new(&mut input);
        EasingFunction::parse(&mut parser).map_err(|_| ())
    }

    #[test]
    fn parses_level_one_easing_functions() {
        assert_eq!(parse("linear"), Ok(EasingFunction::Linear));
        assert_eq!(parse("step-start"), Ok(EasingFunction::Steps(1, StepPosition::Start)));
        assert_eq!(parse("step-end"), Ok(EasingFunction::Steps(1, StepPosition::End)));
        assert_eq!(parse("steps(4, jump-start)"), Ok(EasingFunction::Steps(4, StepPosition::JumpStart)));
        assert_eq!(parse("steps(3)"), Ok(EasingFunction::Steps(3, StepPosition::JumpEnd)));
    }

    #[test]
    fn validates_cubic_bezier_x_coordinates_and_step_count() {
        assert!(parse("cubic-bezier(-0.1, 0, 1, 1)").is_err());
        assert!(parse("cubic-bezier(0, 0, 1.1, 1)").is_err());
        assert!(parse("steps(0)").is_err());
        assert!(parse("steps(1, jump-none)").is_err());
    }
}
''',
)

replace_once(
    "crates/vizia_style/src/property.rs",
    "    Alignment, Angle, AspectRatio, BackgroundImage, BackgroundRepeat, BackgroundSize, BlendMode,\n",
    "    Alignment, Angle, AnimationDelays, AnimationDirections, AnimationDurations, AnimationFillModes,\n    AnimationIterationCounts, AnimationNames, AnimationPlayStates, AnimationShorthand,\n    AnimationTimingFunctions, AspectRatio, BackgroundImage, BackgroundRepeat, BackgroundSize, BlendMode,\n",
)
replace_once(
    "crates/vizia_style/src/property.rs",
    "        // Animations\n        \"transition\": Transition(Vec<Transition>),\n",
    "        // Animations\n        \"animation-name\": AnimationName(AnimationNames),\n        \"animation-duration\": AnimationDuration(AnimationDurations),\n        \"animation-delay\": AnimationDelay(AnimationDelays),\n        \"animation-timing-function\": AnimationTimingFunction(AnimationTimingFunctions),\n        \"animation-iteration-count\": AnimationIterationCount(AnimationIterationCounts),\n        \"animation-direction\": AnimationDirection(AnimationDirections),\n        \"animation-fill-mode\": AnimationFillMode(AnimationFillModes),\n        \"animation-play-state\": AnimationPlayState(AnimationPlayStates),\n        \"animation\": Animation(AnimationShorthand),\n        \"transition\": Transition(Vec<Transition>),\n",
)

replace_once(
    "crates/vizia_style/src/rules/keyframes.rs",
    "        if let Ok(percentage) = input.try_parse(Percentage::parse) {\n            return Ok(KeyframeSelector::Percentage(percentage));\n        }\n",
    "        if let Ok(percentage) = input.try_parse(Percentage::parse) {\n            if (0.0..=100.0).contains(&percentage.0) {\n                return Ok(KeyframeSelector::Percentage(percentage));\n            }\n            return Err(ParseError {\n                kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),\n                location,\n            });\n        }\n",
)
replace_once(
    "crates/vizia_style/src/rules/keyframes.rs",
    "use cssparser::*;\n",
    "use cssparser::*;\n",
)

# Parser coverage at stylesheet level, including multiple keyframe selectors and invalid percentages.
replace_once(
    "crates/vizia_style/src/stylesheet.rs",
    "    #[test]\n    fn parses_filter_and_backdrop_filter_keyframes() {",
    r'''    #[test]
    fn parses_css_animation_level_one_declarations() {
        let stylesheet = StyleSheet::parse(
            r#"
                .animated {
                    animation-name: fade, slide;
                    animation-duration: 200ms, 1s;
                    animation-delay: -50ms, 0s;
                    animation-timing-function: steps(4, end), ease-in-out;
                    animation-iteration-count: 2.5, infinite;
                    animation-direction: alternate, reverse;
                    animation-fill-mode: both, forwards;
                    animation-play-state: running, paused;
                    animation: fade 1s ease-in -200ms 2 alternate both running;
                }
                @keyframes fade {
                    from, 25% { opacity: 0; }
                    25%, 75% { opacity: 0.5; }
                    to { opacity: 1; }
                }
            "#,
            ParserOptions::default(),
        )
        .expect("CSS Animations Level 1 declarations should parse");

        assert_eq!(stylesheet.rules.0.len(), 2);
    }

    #[test]
    fn rejects_out_of_range_keyframe_percentages() {
        assert!(StyleSheet::parse(
            "@keyframes bad { 101% { opacity: 1; } }",
            ParserOptions::default(),
        )
        .is_err());
    }

    #[test]
    fn parses_filter_and_backdrop_filter_keyframes() {''',
)

print("keyframes level 1 patch applied")
