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

text = text.replace(
    '"use hashbrown::{HashMap, HashSet};\\nuse vizia_storage::{SparseSet, SparseSetGeneric, SparseSetIndex};\\nuse vizia_style::AnimationComposition;\\n",',
    '"use hashbrown::HashMap;\\nuse vizia_storage::{SparseSet, SparseSetGeneric, SparseSetIndex};\\nuse vizia_style::AnimationComposition;\\n",',
    1,
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
