from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


# Duplicate keyframe offsets form one logical keyframe. A later block only replaces the easing
# declaration when it actually contains animation-timing-function; an omitted declaration must not
# erase an earlier declaration at the same offset.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    r'''                                let keyframe_timing = keyframes
                                    .declarations
                                    .declarations
                                    .iter()
                                    .rev()
                                    .find_map(|property| match property {
                                        Property::AnimationTimingFunction(functions) => {
                                            functions.0.first().copied()
                                        }
                                        _ => None,
                                    })
                                    .map(TimingFunction::from_easing)
                                    .unwrap_or(TimingFunction::AnimationDefault);
                                animation_timeline.push((time, keyframe_timing));
''',
    r'''                                let keyframe_timing = keyframes
                                    .declarations
                                    .declarations
                                    .iter()
                                    .rev()
                                    .find_map(|property| match property {
                                        Property::AnimationTimingFunction(functions) => {
                                            functions.0.first().copied()
                                        }
                                        _ => None,
                                    })
                                    .map(TimingFunction::from_easing);
                                if let Some((_, existing_timing)) = animation_timeline
                                    .iter_mut()
                                    .rev()
                                    .find(|(offset, _)| (*offset - time).abs() <= f32::EPSILON)
                                {
                                    if let Some(keyframe_timing) = keyframe_timing {
                                        *existing_timing = keyframe_timing;
                                    }
                                } else {
                                    animation_timeline.push((
                                        time,
                                        keyframe_timing
                                            .unwrap_or(TimingFunction::AnimationDefault),
                                    ));
                                }
''',
)

print("duplicate keyframe semantics applied")
