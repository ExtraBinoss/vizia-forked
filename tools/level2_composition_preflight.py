from pathlib import Path

path = Path("tools/level2_composition.py")
text = path.read_text()

old = '''impl<T> Compositor for Vec<T>
where
    T: Interpolator + Compositor + Clone,
{
    fn compose(_underlying: &Self, effect: &Self, _composition: AnimationComposition) -> Self {
        effect.clone()
    }
}
'''
new = '''replace_compositor!(
    Vec<ImageOrGradient>,
    Vec<Position>,
    Vec<BackgroundRepeat>,
    Vec<BackgroundSize>,
    Vec<Shadow>,
);
'''
if old in text:
    text = text.replace(old, new, 1)

# AnimatableSet only needs HashMap for the composed-output cache. VarSet already
# imports HashSet for tick_changed(), so keep that one unchanged.
text = text.replace(
    '"use hashbrown::{HashMap, HashSet};\\nuse vizia_storage::{SparseSet, SparseSetGeneric, SparseSetIndex};\\nuse vizia_style::AnimationComposition;\\n",',
    '"use hashbrown::HashMap;\\nuse vizia_storage::{SparseSet, SparseSetGeneric, SparseSetIndex};\\nuse vizia_style::AnimationComposition;\\n",',
    1,
)

# The source documentation after stop_css_animation says Tick, not Stop. Keep the
# materializer anchored to the real Level 1 source so the source commit is atomic.
text = text.replace(
    '''        self.refresh_animation_index(entity);\n    }\n\n    /// Stop an active animation for the given entity.\n''',
    '''        self.refresh_animation_index(entity);\n    }\n\n    /// Tick the animation for the given time and return entities whose animated value may change.\n''',
)
text = text.replace(
    '''        self.refresh_animation_index(entity);\n        self.refresh_css_composed_outputs();\n    }\n\n    /// Stop an active animation for the given entity.\n''',
    '''        self.refresh_animation_index(entity);\n        self.refresh_css_composed_outputs();\n    }\n\n    /// Tick the animation for the given time and return entities whose animated value may change.\n''',
)

# Use explicit CSS length values in the focused store test so it does not rely on
# an incidental numeric conversion for Translate.
text = text.replace(
    'key.translate((10.0, 0.0))',
    'key.translate((Length::px(10.0), Length::px(0.0)))',
)
text = text.replace(
    'key.translate((20.0, 0.0))',
    'key.translate((Length::px(20.0), Length::px(0.0)))',
)

path.write_text(text)
