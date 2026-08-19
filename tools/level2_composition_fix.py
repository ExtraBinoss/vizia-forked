from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


# ColorStop is generic and does not need its own fallback compositor because
# Gradient/LinearGradient are composed as replacement values.
replace_once(
    "crates/vizia_core/src/animation/interpolator.rs",
    '''    Shadow,
    Gradient,
    LinearGradient,
    ColorStop,
    Matrix,
''',
    '''    Shadow,
    Gradient,
    LinearGradient,
    Matrix,
''',
)

# The first materialization accidentally duplicated the new field in `new()` and
# omitted it from `Default`.
replace_once(
    "crates/vizia_core/src/animation/animation_state.rs",
    '''            css_order: 0,
            css_composition: AnimationComposition::Replace,
            css_composition: AnimationComposition::Replace,
''',
    '''            css_order: 0,
            css_composition: AnimationComposition::Replace,
''',
)
replace_once(
    "crates/vizia_core/src/animation/animation_state.rs",
    '''            css_instance_id: None,
            css_order: 0,
        }
    }
}
''',
    '''            css_instance_id: None,
            css_order: 0,
            css_composition: AnimationComposition::Replace,
        }
    }
}
''',
)

# Every property registered in an animation has a Level 2 composition strategy.
# Keep this constraint local to the internal keyframe registration helpers.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    '''use crate::animation::{AnimationEvent, AnimationState, Interpolator, Keyframe, TimingFunction};
''',
    '''use crate::animation::{
    AnimationEvent, AnimationState, Compositor, Interpolator, Keyframe, TimingFunction,
};
''',
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    '''        fn insert_keyframe<T: 'static + Interpolator + Debug + Clone + PartialEq + Default>(
''',
    '''        fn insert_keyframe<
            T: 'static + Interpolator + Compositor + Debug + Clone + PartialEq + Default,
        >(
''',
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    '''        fn insert_keyframe2<T: 'static + Interpolator + Debug + Clone + PartialEq + Default>(
''',
    '''        fn insert_keyframe2<
            T: 'static + Interpolator + Compositor + Debug + Clone + PartialEq + Default,
        >(
''',
)
