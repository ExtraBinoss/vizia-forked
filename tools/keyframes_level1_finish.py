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


replace_once(
    "crates/vizia_style/src/rules/keyframes.rs",
    "        if let Ok(val) = input.try_parse(Percentage::parse) {\n            return Ok(KeyframeSelector::Percentage(val));\n        }\n",
    "        let location = input.current_source_location();\n        if let Ok(val) = input.try_parse(Percentage::parse) {\n            if (0.0..=100.0).contains(&val.0) {\n                return Ok(KeyframeSelector::Percentage(val));\n            }\n            return Err(ParseError {\n                kind: ParseErrorKind::Custom(CustomParseError::InvalidValue),\n                location,\n            });\n        }\n",
)

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

print("keyframes level 1 finish patch applied")
