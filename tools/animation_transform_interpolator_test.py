from pathlib import Path

path = Path('crates/vizia_core/src/animation/interpolator.rs')
text = path.read_text()
marker = '''    #[test]
    fn transform_add_concatenates_effect_lists_in_order() {
'''
if 'fn transform_interpolates_compatible_translate_functions()' not in text:
    insert = '''    #[test]
    fn transform_interpolates_compatible_translate_functions() {
        let start = Transform::TranslateX(LengthOrPercentage::Length(Length::px(-100.0)));
        let end = Transform::TranslateX(LengthOrPercentage::Length(Length::px(100.0)));
        let mid = Transform::interpolate(&start, &end, 0.5);

        let Transform::TranslateX(LengthOrPercentage::Length(Length::Value(
            LengthValue::Px(value),
        ))) = mid
        else {
            panic!("expected interpolated translateX");
        };
        assert!(value.abs() < 0.001);
    }

'''
    if marker not in text:
        raise SystemExit('composition test marker not found')
    text = text.replace(marker, insert + marker, 1)
path.write_text(text)
