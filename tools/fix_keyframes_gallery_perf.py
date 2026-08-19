from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1))


# Load the animation gallery stylesheet once at application startup instead of
# appending another copy every time the Animation page is revisited.
replace_once(
    "examples/widget_gallery/src/main.rs",
    '''        cx.add_stylesheet(include_style!("resources/themes/accents.css"))
            .expect("Failed to add stylesheet");
''',
    '''        cx.add_stylesheet(include_style!("resources/themes/accents.css"))
            .expect("Failed to add stylesheet");

        cx.add_stylesheet(include_style!("resources/themes/animation.css"))
            .expect("Failed to add animation gallery stylesheet");
''',
)

# Add a change-aware tick for expensive layout properties. The normal tick is
# intentionally left untouched because it also acts as the animation frame
# driver for paint/transform animations.
replace_once(
    "crates/vizia_core/src/storage/animatable_var_set.rs",
    "use hashbrown::HashMap;",
    "use hashbrown::{HashMap, HashSet};",
)

replace_once(
    "crates/vizia_core/src/storage/animatable_var_set.rs",
    '''        self.active_animations
            .iter()
            .filter(|state| state.t < 1.0)
            .flat_map(|state| state.entities.iter().copied())
            .collect()
    }

    // Returns true if the given entity is linked to an active animation    // Returns true if the given entity is linked to an active animation
''',
    '''        self.active_animations
            .iter()
            .filter(|state| state.t < 1.0)
            .flat_map(|state| state.entities.iter().copied())
            .collect()
    }

    /// Tick animations but only return entities whose visible computed value changed.
    ///
    /// Layout/reflow callers use this to avoid invalidating an expensive subsystem on
    /// every frame of paused or stepped CSS animations. The regular `tick()` remains
    /// available for paint/transform paths that also drive the animation frame loop.
    pub fn tick_changed(&mut self, time: Instant) -> Vec<Entity> {
        let entities: HashSet<Entity> = self
            .active_animations
            .iter()
            .filter(|state| state.t < 1.0)
            .flat_map(|state| state.entities.iter().copied())
            .collect();

        if entities.is_empty() {
            return Vec::new();
        }

        let before = entities
            .iter()
            .map(|entity| (*entity, self.get(*entity).cloned()))
            .collect::<Vec<_>>();

        let _ = self.tick(time);

        before
            .into_iter()
            .filter_map(|(entity, before)| {
                (self.get(entity).cloned() != before).then_some(entity)
            })
            .collect()
    }

    // Returns true if the given entity is linked to an active animation    // Returns true if the given entity is linked to an active animation
''',
)

# Layout animations must keep the frame clock alive, but they should only ask
# morphorm to relayout when the sampled value actually changed.
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    '''    let mut retransform_entities = Vec::new();
    let mut reclip_entities = Vec::new();
''',
    '''    let mut retransform_entities = Vec::new();
    let mut reclip_entities = Vec::new();
    let mut has_active_layout_animations = false;
''',
)

replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    '''    // Properties which affect layout
    relayout_entities.extend(cx.style.display.tick(time));
''',
    '''    // Properties which affect layout. Keep the animation frame loop alive while
    // avoiding a relayout when a stepped/paused animation sampled the same value.
    macro_rules! tick_layout {
        ($store:expr) => {{
            has_active_layout_animations |= $store.has_animations();
            relayout_entities.extend($store.tick_changed(time));
        }};
    }

    relayout_entities.extend(cx.style.display.tick(time));
''',
)

for name in [
    "border_top_width",
    "border_right_width",
    "border_bottom_width",
    "border_left_width",
    "left",
    "right",
    "top",
    "bottom",
    "width",
    "height",
    "max_width",
    "max_height",
    "min_width",
    "min_height",
    "max_horizontal_gap",
    "max_vertical_gap",
    "min_horizontal_gap",
    "min_vertical_gap",
    "vertical_gap",
    "horizontal_gap",
    "padding_left",
    "padding_right",
    "padding_top",
    "padding_bottom",
]:
    replace_once(
        "crates/vizia_core/src/systems/animation.rs",
        f"    relayout_entities.extend(cx.style.{name}.tick(time));",
        f"    tick_layout!(cx.style.{name});",
    )

replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    '''    for store in cx.style.custom_units_props.values_mut() {
        relayout_entities.extend(store.tick(time));
    }
''',
    '''    for store in cx.style.custom_units_props.values_mut() {
        has_active_layout_animations |= store.has_animations();
        relayout_entities.extend(store.tick_changed(time));
    }
''',
)

replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    '''    !redraw_entities.is_empty()
        | !relayout_entities.is_empty()
''',
    '''    has_active_layout_animations
        | !redraw_entities.is_empty()
        | !relayout_entities.is_empty()
''',
)
