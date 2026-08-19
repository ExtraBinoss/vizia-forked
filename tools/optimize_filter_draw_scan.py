from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:160]!r}")
    p.write_text(text.replace(old, new, 1))


# Track only entities which can require filter/backdrop dirty-bound handling.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    '''    // Filters
    pub(crate) filter: AnimatableSet<Filter>,
    pub(crate) backdrop_filter: AnimatableSet<Filter>,

    pub(crate) blend_mode: StyleSet<BlendMode>,
''',
    '''    // Filters
    pub(crate) filter: AnimatableSet<Filter>,
    pub(crate) backdrop_filter: AnimatableSet<Filter>,
    /// Entities which currently have, or are actively animating, a filter/backdrop-filter.
    /// Draw uses this sparse set instead of scanning the entire layout tree every frame.
    pub(crate) filter_entities: HashSet<Entity>,

    pub(crate) blend_mode: StyleSet<BlendMode>,
''',
)

# Refresh static/computed membership whenever style matching is linked.
replace_once(
    "crates/vizia_core/src/systems/style.rs",
    '''    if style.backdrop_filter.link(entity, matched_rules) {
        should_redraw = true;
    }

    if style.blend_mode.link(entity, matched_rules) {
''',
    '''    if style.backdrop_filter.link(entity, matched_rules) {
        should_redraw = true;
    }

    if style.filter.get(entity).is_some() || style.backdrop_filter.get(entity).is_some() {
        style.filter_entities.insert(entity);
    } else {
        style.filter_entities.remove(&entity);
    }

    if style.blend_mode.link(entity, matched_rules) {
''',
)

# Animated filters may exist without a static base declaration, so register them from tick output.
replace_once(
    "crates/vizia_core/src/systems/animation.rs",
    '''    // Filters
    redraw_entities.extend(cx.style.filter.tick(time));
    redraw_entities.extend(cx.style.backdrop_filter.tick(time));
''',
    '''    // Filters. Track only the entities which can require filter-aware dirty-bound work.
    let filter_entities = cx.style.filter.tick(time);
    cx.style.filter_entities.extend(filter_entities.iter().copied());
    redraw_entities.extend(filter_entities);
    let backdrop_filter_entities = cx.style.backdrop_filter.tick(time);
    cx.style.filter_entities.extend(backdrop_filter_entities.iter().copied());
    redraw_entities.extend(backdrop_filter_entities);
''',
)

# Replace the O(total-tree-size) draw scan with O(number-of-filtered-entities).
replace_once(
    "crates/vizia_core/src/systems/draw.rs",
    "use vizia_storage::{DrawChildIterator, LayoutTreeIterator};",
    "use vizia_storage::DrawChildIterator;",
)

old = '''    let iter = LayoutTreeIterator::full(&cx.tree);
    for entity in iter {
        if cx.tree.is_ignored(entity) {
            continue;
        }

        if cx.tree.is_window(entity) && entity != window_entity {
            continue;
        }

        // Check if the entity has a filter style.
        if cx.style.filter.get(entity).is_some() || cx.style.backdrop_filter.get(entity).is_some() {
            if entity.visible(&cx.style) {
                // Entity is VISIBLE and has a filter.
                // Skip recomputation if already processed in redraw_list.
                if !redraw_list.contains(&entity) {
                    let filter_current_bounds = draw_bounds(&cx.style, &cx.cache, &cx.tree, entity);

                    // Update cache for visible entity
                    cx.cache.draw_bounds.insert(entity, filter_current_bounds);

                    if filter_current_bounds.w > 0.0 && filter_current_bounds.h > 0.0 {
                        // Ensure bounds are valid
                        // Condition to update dirty_rect:
                        // 1. dirty_rect is None (then set it to filter_current_bounds).
                        // 2. dirty_rect is Some, and filter_current_bounds intersects with it (then union).
                        if dirty_rect.is_none_or(|current_dr_val| {
                            filter_current_bounds.intersects(&current_dr_val)
                        }) {
                            dirty_rect =
                                Some(dirty_rect.map_or(filter_current_bounds, |current_dr_val| {
                                    current_dr_val.union(&filter_current_bounds)
                                }));
                        }
                    }
                }
            } else {
                // Entity is INVISIBLE but has (or had) a filter style.
                // Its *previous* bounds need to be added to dirty_rect.
                if let Some(previous_draw_bounds) = cx.cache.draw_bounds.get(entity).copied() {
                    union_dirty_rect(&mut dirty_rect, previous_draw_bounds);
                }

                // Remove from cache as it's no longer visible with these bounds.
                cx.cache.draw_bounds.remove(entity);
            }
        }
    }
'''
new = '''    // Filter/backdrop dirty handling is proportional to the number of filtered entities,
    // not to the total number of widgets in the window.
    let filter_entities = cx.style.filter_entities.iter().copied().collect::<Vec<_>>();
    let mut stale_filter_entities = Vec::new();
    for entity in filter_entities {
        if !cx.entity_manager.is_alive(entity) {
            stale_filter_entities.push(entity);
            continue;
        }

        if cx.tree.is_ignored(entity) {
            continue;
        }

        if cx.tree.is_window(entity) && entity != window_entity {
            continue;
        }

        if cx.style.filter.get(entity).is_none() && cx.style.backdrop_filter.get(entity).is_none() {
            stale_filter_entities.push(entity);
            continue;
        }

        if entity.visible(&cx.style) {
            // Skip recomputation if already processed in redraw_list.
            if !redraw_list.contains(&entity) {
                let filter_current_bounds = draw_bounds(&cx.style, &cx.cache, &cx.tree, entity);
                cx.cache.draw_bounds.insert(entity, filter_current_bounds);

                if filter_current_bounds.w > 0.0
                    && filter_current_bounds.h > 0.0
                    && dirty_rect
                        .is_none_or(|current_dr_val| filter_current_bounds.intersects(&current_dr_val))
                {
                    dirty_rect = Some(dirty_rect.map_or(filter_current_bounds, |current_dr_val| {
                        current_dr_val.union(&filter_current_bounds)
                    }));
                }
            }
        } else {
            if let Some(previous_draw_bounds) = cx.cache.draw_bounds.get(entity).copied() {
                union_dirty_rect(&mut dirty_rect, previous_draw_bounds);
            }
            cx.cache.draw_bounds.remove(entity);
        }
    }

    for entity in stale_filter_entities {
        cx.style.filter_entities.remove(&entity);
    }
'''
replace_once("crates/vizia_core/src/systems/draw.rs", old, new)
