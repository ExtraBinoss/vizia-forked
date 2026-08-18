from pathlib import Path
import runpy

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

# Older relaunchable workflow runs predate the explicit composition step. When they check out the
# current branch, apply the per-occurrence composition patch here as well. The patch itself is
# idempotent, and current workflows skip this because the field already exists.
state = (ROOT / "crates/vizia_core/src/animation/animation_state.rs").read_text()
if "pub css_instance_id: Option<u64>" not in state:
    runpy.run_path(str(ROOT / "tools/keyframes_level1_composition.py"))

print("duplicate keyframe and occurrence semantics applied")
