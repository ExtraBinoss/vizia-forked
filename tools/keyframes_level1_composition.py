from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:220]!r}")
    p.write_text(text.replace(old, new, 1))


# Each CSS list occurrence gets an identity distinct from the shared @keyframes animation id.
replace_once(
    "crates/vizia_core/src/animation/animation_state.rs",
    "    pub css_clock: Option<CssAnimationClock>,\n    pub css_default_timing: TimingFunction,\n",
    "    pub css_clock: Option<CssAnimationClock>,\n    pub css_default_timing: TimingFunction,\n    pub css_instance_id: Option<u64>,\n    pub css_order: usize,\n",
)
replace_once(
    "crates/vizia_core/src/animation/animation_state.rs",
    "            css_clock: None,\n            css_default_timing: TimingFunction::ease(),\n",
    "            css_clock: None,\n            css_default_timing: TimingFunction::ease(),\n            css_instance_id: None,\n            css_order: 0,\n",
)
# There are two constructors/default blocks with the same anchor.
p = ROOT / "crates/vizia_core/src/animation/animation_state.rs"
text = p.read_text()
needle = "            css_clock: None,\n            css_default_timing: TimingFunction::ease(),\n"
if needle in text:
    text = text.replace(
        needle,
        "            css_clock: None,\n            css_default_timing: TimingFunction::ease(),\n            css_instance_id: None,\n            css_order: 0,\n",
        1,
    )
p.write_text(text)

# Patch both generic animatable stores. The source Animation id still selects keyframes; the
# occurrence id selects the running instance and css_order controls cascade priority.
for path in [
    "crates/vizia_core/src/storage/animatable_set.rs",
    "crates/vizia_core/src/storage/animatable_var_set.rs",
]:
    replace_once(
        path,
        "        animation: Animation,\n        start_time: Instant,\n        timing: CssAnimationTiming,\n        default_timing: TimingFunction,\n        timeline: &[(f32, TimingFunction)],\n    ) {",
        "        animation: Animation,\n        instance_id: u64,\n        order: usize,\n        start_time: Instant,\n        timing: CssAnimationTiming,\n        default_timing: TimingFunction,\n        timeline: &[(f32, TimingFunction)],\n    ) {",
    )
    replace_once(
        path,
        "        for state in self.active_animations.iter_mut() {\n            if state.css_clock.is_some() && state.id == animation {\n                state.entities.remove(&entity);\n            }\n        }",
        "        for state in self.active_animations.iter_mut() {\n            if state.css_instance_id == Some(instance_id) {\n                state.entities.remove(&entity);\n            }\n        }",
    )
    replace_once(
        path,
        "        state.configure_css(timing, default_timing, start_time);\n        state.output = None;\n",
        "        state.configure_css(timing, default_timing, start_time);\n        state.css_instance_id = Some(instance_id);\n        state.css_order = order;\n        state.output = None;\n",
    )
    replace_once(
        path,
        "        animation: Animation,\n        timing: CssAnimationTiming,\n        default_timing: TimingFunction,\n        now: Instant,\n    ) {\n        for state in self.active_animations.iter_mut() {\n            if state.css_clock.is_some() && state.id == animation && state.entities.contains(&entity) {\n                state.update_css_timing(timing, default_timing, now);\n            }\n        }\n    }",
        "        instance_id: u64,\n        order: usize,\n        timing: CssAnimationTiming,\n        default_timing: TimingFunction,\n        now: Instant,\n    ) {\n        for state in self.active_animations.iter_mut() {\n            if state.css_instance_id == Some(instance_id) && state.entities.contains(&entity) {\n                state.css_order = order;\n                state.update_css_timing(timing, default_timing, now);\n            }\n        }\n    }",
    )
    # Dedicated stop by occurrence; keep legacy stop_animation(source-id) unchanged for the Rust API.
    replace_once(
        path,
        "    /// Stop an active animation for the given entity.\n    pub(crate) fn stop_animation(&mut self, entity: Entity, animation: Animation) {",
        "    pub(crate) fn stop_css_animation(&mut self, entity: Entity, instance_id: u64) {\n        for state in self.active_animations.iter_mut() {\n            if state.css_instance_id == Some(instance_id) {\n                state.entities.remove(&entity);\n            }\n        }\n        self.refresh_animation_index(entity);\n    }\n\n    /// Stop an active animation for the given entity.\n    pub(crate) fn stop_animation(&mut self, entity: Entity, animation: Animation) {",
    )
    # Sparse animation_index must remain the legacy animation/transition fallback, not a CSS state.
    replace_once(
        path,
        "            .find(|(_, state)| state.entities.contains(&entity))\n",
        "            .find(|(_, state)| state.css_instance_id.is_none() && state.entities.contains(&entity))\n",
    )
    # Later CSS list entries win even if the backing vector order did not change after a reorder.
    replace_once(
        path,
        "            // CSS animations override transitions and base style; later CSS animations win.\n            for state in self.active_animations.iter().rev() {\n                if state.css_clock.is_some() && state.entities.contains(&entity) {\n                    if let Some(output) = state.get_output() {\n                        return Some(output);\n                    }\n                }\n            }",
        "            // CSS animations override transitions/base style. The greatest current list order wins.\n            let mut css_output = None;\n            let mut css_order = 0usize;\n            for state in &self.active_animations {\n                if state.css_instance_id.is_some() && state.entities.contains(&entity) {\n                    if let Some(output) = state.get_output() {\n                        if css_output.is_none() || state.css_order >= css_order {\n                            css_order = state.css_order;\n                            css_output = Some(output);\n                        }\n                    }\n                }\n            }\n            if let Some(output) = css_output {\n                return Some(output);\n            }",
    )

# Resolver instance identity and monotonic allocator.
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "pub(crate) struct CssAnimationInstance {\n    pub name: String,\n    pub animation: Animation,\n",
    "pub(crate) struct CssAnimationInstance {\n    pub instance_id: u64,\n    pub name: String,\n    pub animation: Animation,\n",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    pub(crate) css_animation_instances: HashMap<Entity, Vec<CssAnimationInstance>>,\n",
    "    pub(crate) css_animation_instances: HashMap<Entity, Vec<CssAnimationInstance>>,\n    pub(crate) next_css_animation_instance_id: u64,\n",
)

# Store helpers now target one CSS occurrence and carry its current list order.
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "    fn play_css_on_stores(&mut self, entity: Entity, spec: &ResolvedCssAnimation, start_time: Instant) {",
    "    fn play_css_on_stores(\n        &mut self,\n        entity: Entity,\n        spec: &ResolvedCssAnimation,\n        instance_id: u64,\n        order: usize,\n        start_time: Instant,\n    ) {",
)
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "                    spec.animation,\n                    start_time,\n",
    "                    spec.animation,\n                    instance_id,\n                    order,\n                    start_time,\n",
)
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "    fn update_css_on_stores(&mut self, entity: Entity, spec: &ResolvedCssAnimation, now: Instant) {",
    "    fn update_css_on_stores(\n        &mut self,\n        entity: Entity,\n        spec: &ResolvedCssAnimation,\n        instance_id: u64,\n        order: usize,\n        now: Instant,\n    ) {",
)
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "                    entity,\n                    spec.animation,\n                    spec.timing,\n",
    "                    entity,\n                    instance_id,\n                    order,\n                    spec.timing,\n",
)
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "    fn stop_css_on_stores(&mut self, entity: Entity, animation: Animation) {\n        macro_rules! stop { ($store:expr) => { $store.stop_animation(entity, animation); }; }",
    "    fn stop_css_on_stores(&mut self, entity: Entity, instance_id: u64) {\n        macro_rules! stop { ($store:expr) => { $store.stop_css_animation(entity, instance_id); }; }",
)

# Replace sync wholesale between its signature and cancel_css_animations. Matched occurrences retain
# clocks across timing edits and reorder. A changed @keyframes definition (same name, new source id)
# cancels/recreates only that occurrence.
p = ROOT / "crates/vizia_core/src/style/css_animation.rs"
text = p.read_text()
start = text.index("    pub(crate) fn sync_css_animations(&mut self, entity: Entity, now: Instant) {")
end = text.index("    pub(crate) fn cancel_css_animations", start)
new_sync = r'''    pub(crate) fn sync_css_animations(&mut self, entity: Entity, now: Instant) {
        let specs = self.resolved_css_animations(entity);
        let old = self.css_animation_instances.remove(&entity).unwrap_or_default();
        let mut used = vec![false; old.len()];
        let mut next_reversed = Vec::with_capacity(specs.len());

        // CSS Animations matching is performed from the end so duplicate names retain the correct
        // occurrence identity when list lengths or ordering change.
        for (reverse_index, spec) in specs.iter().rev().enumerate() {
            let order = specs.len() - 1 - reverse_index;
            let matched = old
                .iter()
                .enumerate()
                .rev()
                .find(|(index, instance)| !used[*index] && instance.name == spec.name)
                .map(|(index, _)| index);

            if let Some(index) = matched {
                used[index] = true;
                let mut instance = old[index].clone();
                if instance.animation == spec.animation {
                    instance.clock.update_timing(spec.timing, now);
                    instance.default_timing = spec.default_timing;
                    self.update_css_on_stores(
                        entity,
                        spec,
                        instance.instance_id,
                        order,
                        now,
                    );
                    next_reversed.push(instance);
                    continue;
                }

                self.pending_animation_events.push(Self::cancel_event(&instance, entity, now));
                self.stop_css_on_stores(entity, instance.instance_id);
            }

            let instance_id = self.next_css_animation_instance_id;
            self.next_css_animation_instance_id = self.next_css_animation_instance_id.wrapping_add(1);
            let instance = CssAnimationInstance {
                instance_id,
                name: spec.name.clone(),
                animation: spec.animation,
                clock: CssAnimationClock::new(spec.timing, now),
                default_timing: spec.default_timing,
                started: false,
                last_iteration: 0,
                ended: false,
            };
            self.play_css_on_stores(entity, spec, instance_id, order, now);
            next_reversed.push(instance);
        }

        for (index, instance) in old.iter().enumerate() {
            if !used[index] {
                self.pending_animation_events.push(Self::cancel_event(instance, entity, now));
                self.stop_css_on_stores(entity, instance.instance_id);
            }
        }

        next_reversed.reverse();
        if !next_reversed.is_empty() {
            self.css_animation_instances.insert(entity, next_reversed);
        }
    }

'''
text = text[:start] + new_sync + text[end:]
p.write_text(text)

# Cancellation must stop each occurrence, not every animation sharing a source id.
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    "                self.stop_css_on_stores(entity, instance.animation);",
    "                self.stop_css_on_stores(entity, instance.instance_id);",
)

print("per-occurrence CSS animation composition applied")
