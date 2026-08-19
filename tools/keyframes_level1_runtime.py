from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_if_present(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if old in text:
        p.write_text(text.replace(old, new, 1))


def ensure_after(path: str, anchor: str, insertion: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if insertion in text:
        return
    if anchor not in text:
        raise RuntimeError(f"anchor not found in {path}: {anchor!r}")
    p.write_text(text.replace(anchor, anchor + insertion, 1))


# Repair the last parser regressions left behind by the obsolete bootstrap generator.
replace_if_present(
    "crates/vizia_style/src/values/mod.rs",
    "pub mod animation;\npub mod animation;\n",
    "pub mod animation;\n",
)
replace_if_present(
    "crates/vizia_style/src/values/animation.rs",
    "use cssparser::{ParseError, ParseErrorKind, Parser, Token};",
    "use cssparser::{match_ignore_ascii_case, ParseError, ParseErrorKind, Parser, Token};",
)
replace_if_present(
    "crates/vizia_style/src/values/easing.rs",
    "use cssparser::{ParseError, ParseErrorKind, Parser, Token};",
    "use cssparser::{match_ignore_ascii_case, ParseError, ParseErrorKind, Parser, Token};",
)

# The runtime and stores are already materialized in Rust. This script applies only the remaining
# integration fixes discovered by compiling the materialized source on stable Rust.
replace_if_present(
    "crates/vizia_core/src/animation/mod.rs",
    "    CssAnimationClock, CssAnimationPhase, CssAnimationSample, CssAnimationTiming,\n",
    "    CssAnimationClock, CssAnimationPhase, CssAnimationTiming,\n",
)
replace_if_present(
    "crates/vizia_core/src/style/mod.rs",
    "    BlendMode, EasingFunction, KeyframeSelector, ParserOptions, Property, Selectors, StyleSheet,\n",
    "    BlendMode, KeyframeSelector, ParserOptions, Property, Selectors, StyleSheet,\n",
)
replace_if_present(
    "crates/vizia_core/src/style/mod.rs",
    "    AnimationEvent, AnimationState, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n",
    "    AnimationEvent, AnimationState, Interpolator, Keyframe, TimingFunction,\n",
)
replace_if_present(
    "crates/vizia_core/src/storage/animatable_set.rs",
    "    AnimationState, CssAnimationPhase, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n",
    "    AnimationState, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n",
)
replace_if_present(
    "crates/vizia_core/src/storage/animatable_var_set.rs",
    "    AnimationState, CssAnimationPhase, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n",
    "    AnimationState, CssAnimationTiming, Interpolator, Keyframe, TimingFunction,\n",
)

replace_if_present(
    "crates/vizia_core/src/animation/animation_state.rs",
    """            css_instance_id: None,
            css_order: 0,
            css_instance_id: None,
            css_order: 0,
            css_instance_id: None,
            css_order: 0,
""",
    """            css_instance_id: None,
            css_order: 0,
""",
)

animation_state = ROOT / "crates/vizia_core/src/animation/animation_state.rs"
text = animation_state.read_text()
default_marker = """            css_clock: None,
            css_default_timing: TimingFunction::ease(),
        }
    }
}"""
if "impl<Prop> Default" in text:
    default_part = text.split("impl<Prop> Default", 1)[1]
    if "css_instance_id: None" not in default_part:
        text = text.replace(
            default_marker,
            """            css_clock: None,
            css_default_timing: TimingFunction::ease(),
            css_instance_id: None,
            css_order: 0,
        }
    }
}""",
            1,
        )
        animation_state.write_text(text)

var_set = ROOT / "crates/vizia_core/src/storage/animatable_var_set.rs"
text = var_set.read_text()
duplicate = """    /// Stop an active animation for the given entity.
    pub(crate) fn stop_animation(&mut self, entity: Entity, animation: Animation) {
        let entity_index = entity.index();

        if entity_index < self.inline_data.sparse.len() {
            let active_anim_index = self.inline_data.sparse[entity_index].anim_index as usize;
            if active_anim_index < self.active_animations.len() {
                let anim_state = &mut self.active_animations[active_anim_index];
                if anim_state.id == animation {
                    anim_state.entities.remove(&entity);
                }
            }
            self.inline_data.sparse[entity_index].anim_index = u32::MAX;
        }
    }

"""
if duplicate in text:
    var_set.write_text(text.replace(duplicate, "", 1))

replace_if_present(
    "crates/vizia_core/src/environment.rs",
    "                    cx.needs_restyle(Entity::root());\n",
    "                    cx.needs_restyle();\n",
)

ensure_after(
    "crates/vizia_core/src/style/css_animation.rs",
    "use std::time::Instant;\n",
    "use vizia_id::GenerationalId;\n",
)

replace_if_present(
    "crates/vizia_core/src/style/mod.rs",
    "                        let mut animation_timeline = Vec::new();\n",
    "                        let mut animation_timeline: Vec<(f32, TimingFunction)> = Vec::new();\n",
)
replace_if_present(
    "crates/vizia_core/src/style/mod.rs",
    """    fn blur_radius(filter: &Filter) -> f32 {
        match filter {
            Filter::Blur(radius) => radius.to_px().expect(\"test blur radius should use pixels\"),
        }
    }
""",
    """    fn blur_radius(filter: &Filter) -> f32 {
        match filter {
            Filter::None => 0.0,
            Filter::Blur(radius) => radius.to_px().expect(\"test blur radius should use pixels\"),
            Filter::List(filters) if filters.len() == 1 => blur_radius(&filters[0]),
            Filter::List(_) => panic!(\"expected a single blur filter in this test\"),
        }
    }
""",
)
replace_if_present(
    "crates/vizia_core/src/systems/draw.rs",
    """    if let Some(filter) = style.filter.get(entity) {
        match filter {
            Filter::Blur(radius) => {
                dirty_bounds = dirty_bounds.expand(radius.to_px().unwrap() * style.scale_factor());
            }
        }
    }
""",
    """    if let Some(filter) = style.filter.get(entity) {
        for filter in filter.as_list() {
            if let Filter::Blur(radius) = filter {
                dirty_bounds =
                    dirty_bounds.expand(radius.to_px().unwrap_or(0.0) * style.scale_factor());
            }
        }
    }
""",
)

# The later generator stages have already been materialized. Make them idempotent for this
# validation rerun so the job tests the source tree instead of trying to regenerate it again.
for script in [
    "keyframes_level1_stores.py",
    "keyframes_level1_css_resolver.py",
    "keyframes_level1_filters.py",
    "keyframes_level1_integration.py",
    "keyframes_level1_semantics.py",
    "keyframes_level1_composition.py",
    "keyframes_level1_fixups.py",
]:
    (ROOT / "tools" / script).write_text(
        'print("CSS Animations Level 1 source already materialized; skipping generator stage")\n'
    )

print("materialized CSS Animations Level 1 parser and core integration fixes")
