use morphorm::Node;

use crate::{layout::node::SubLayout, prelude::*};

macro_rules! process_auto_animations {
    ($cx:expr, $property:expr, $height:expr) => {
        if let Some(animations) = $property.get_active_animations() {
            let mut entities = vec![];

            for animation in animations {
                if animation.keyframes.iter().any(|keyframe| keyframe.value == Units::Auto) {
                    for entity in animation.entities.iter() {
                        let current_bounds = $cx.cache.get_bounds(*entity);
                        let current_measured =
                            if $height { current_bounds.h } else { current_bounds.w };
                        entities.push((*entity, animation.clone(), current_measured));
                    }
                }
            }

            if entities.is_empty() {
                // No auto keyframes for this property in the current frame.
            } else {
                // Resolve auto values against a root layout pass so wrapped text is measured using
                // real parent constraints (especially width) rather than isolated node layout.
                for (entity, animation, _) in entities.iter() {
                    $property.stop_animation(*entity, animation.id);
                    $property.insert(*entity, Units::Auto);
                }

                Entity::root().layout(
                    &mut $cx.cache,
                    &$cx.tree,
                    &$cx.style,
                    &mut SubLayout {
                        text_context: &mut $cx.text_context,
                        resource_manager: &$cx.resource_manager,
                    },
                );

                for (entity, mut animation, current_measured) in entities {
                    $property.remove(entity);

                    let measured_target =
                        if let Some(bounds) = $cx.cache.relative_bounds.get(entity) {
                            if $height { bounds.h } else { bounds.w }
                        } else {
                            let bounds = $cx.cache.get_bounds(entity);
                            if $height { bounds.h } else { bounds.w }
                        };

                    animation.keyframes.iter_mut().for_each(|keyframe| {
                        if keyframe.value == Units::Auto {
                            // Preserve transition direction: start keyframes resolve from current
                            // geometry, later keyframes resolve from target auto geometry.
                            let measured = if keyframe.time <= 0.0 {
                                current_measured
                            } else {
                                measured_target
                            };
                            keyframe.value = Units::Pixels(measured);
                        }
                    });

                    let id = $cx.style.animation_manager.create();
                    $property.insert_animation(id, animation.clone());
                    $property.play_animation(
                        entity,
                        id,
                        animation.start_time,
                        animation.duration,
                        animation.delay,
                    );
                }
            }
        }
    };
}

pub(crate) fn animation_system(cx: &mut Context) -> bool {
    cx.style.play_pending_animations();

    process_auto_animations!(cx, cx.style.max_height, true);
    process_auto_animations!(cx, cx.style.max_width, false);
    process_auto_animations!(cx, cx.style.height, true);
    process_auto_animations!(cx, cx.style.width, false);

    // Tick all animations

    let time = Instant::now();

    let mut redraw_entities = Vec::new();
    let mut reflow_entities = Vec::new();
    let mut relayout_entities = Vec::new();
    let mut retransform_entities = Vec::new();
    let mut reclip_entities = Vec::new();
    let mut has_active_layout_animations = false;

    // Properties which affect rendering
    // Opacity
    redraw_entities.extend(cx.style.opacity.tick(time));
    // Filters
    redraw_entities.extend(cx.style.filter.tick(time));
    redraw_entities.extend(cx.style.backdrop_filter.tick(time));
    // Corner Colour
    redraw_entities.extend(cx.style.border_top_color.tick(time));
    redraw_entities.extend(cx.style.border_right_color.tick(time));
    redraw_entities.extend(cx.style.border_bottom_color.tick(time));
    redraw_entities.extend(cx.style.border_left_color.tick(time));
    // Corner Radius and smoothing. Radius changes also affect rounded clipping.
    let corner_top_left = cx.style.corner_top_left_radius.tick(time);
    let corner_top_right = cx.style.corner_top_right_radius.tick(time);
    let corner_bottom_left = cx.style.corner_bottom_left_radius.tick(time);
    let corner_bottom_right = cx.style.corner_bottom_right_radius.tick(time);
    redraw_entities.extend(corner_top_left.iter().copied());
    redraw_entities.extend(corner_top_right.iter().copied());
    redraw_entities.extend(corner_bottom_left.iter().copied());
    redraw_entities.extend(corner_bottom_right.iter().copied());
    reclip_entities.extend(corner_top_left);
    reclip_entities.extend(corner_top_right);
    reclip_entities.extend(corner_bottom_left);
    reclip_entities.extend(corner_bottom_right);
    redraw_entities.extend(cx.style.corner_top_left_smoothing.tick(time));
    redraw_entities.extend(cx.style.corner_top_right_smoothing.tick(time));
    redraw_entities.extend(cx.style.corner_bottom_left_smoothing.tick(time));
    redraw_entities.extend(cx.style.corner_bottom_right_smoothing.tick(time));
    // Background
    redraw_entities.extend(cx.style.background_color.tick(time));
    redraw_entities.extend(cx.style.background_image.tick(time));
    redraw_entities.extend(cx.style.background_position.tick(time));
    redraw_entities.extend(cx.style.background_repeat.tick(time));
    redraw_entities.extend(cx.style.background_size.tick(time));
    // Box Shadow
    redraw_entities.extend(cx.style.shadow.tick(time));
    // Transform
    retransform_entities.extend(cx.style.transform.tick(time));
    retransform_entities.extend(cx.style.transform_origin.tick(time));
    retransform_entities.extend(cx.style.translate.tick(time));
    retransform_entities.extend(cx.style.rotate.tick(time));
    retransform_entities.extend(cx.style.scale.tick(time));
    // Outline
    redraw_entities.extend(cx.style.outline_color.tick(time));
    redraw_entities.extend(cx.style.outline_offset.tick(time));
    redraw_entities.extend(cx.style.outline_width.tick(time));
    // Clip Path
    reclip_entities.extend(cx.style.clip_path.tick(time));

    redraw_entities.extend(cx.style.fill.tick(time));

    // Pure paint text properties do not require text reconstruction.
    redraw_entities.extend(cx.style.font_color.tick(time));
    redraw_entities.extend(cx.style.caret_color.tick(time));
    redraw_entities.extend(cx.style.selection_color.tick(time));
    redraw_entities.extend(cx.style.text_decoration_color.tick(time));
    // Font Size
    reflow_entities.extend(cx.style.font_size.tick(time));
    // Letter Spacing
    reflow_entities.extend(cx.style.letter_spacing.tick(time));
    // Line Height
    reflow_entities.extend(cx.style.line_height.tick(time));

    // Properties which affect layout. Keep the animation frame loop alive while
    // avoiding a relayout when a stepped/paused animation sampled the same value.
    macro_rules! tick_layout {
        ($store:expr) => {{
            has_active_layout_animations |= $store.has_animations();
            relayout_entities.extend($store.tick_changed(time));
        }};
    }

    relayout_entities.extend(cx.style.display.tick(time));
    // Border Width
    tick_layout!(cx.style.border_top_width);
    tick_layout!(cx.style.border_right_width);
    tick_layout!(cx.style.border_bottom_width);
    tick_layout!(cx.style.border_left_width);
    // Space
    tick_layout!(cx.style.left);
    tick_layout!(cx.style.right);
    tick_layout!(cx.style.top);
    tick_layout!(cx.style.bottom);
    // Size
    tick_layout!(cx.style.width);
    tick_layout!(cx.style.height);
    // Min/Max Size
    tick_layout!(cx.style.max_width);
    tick_layout!(cx.style.max_height);
    tick_layout!(cx.style.min_width);
    tick_layout!(cx.style.min_height);
    // Min/Max Gap
    tick_layout!(cx.style.max_horizontal_gap);
    tick_layout!(cx.style.max_vertical_gap);
    tick_layout!(cx.style.min_horizontal_gap);
    tick_layout!(cx.style.min_vertical_gap);
    // Row/Col Between
    tick_layout!(cx.style.vertical_gap);
    tick_layout!(cx.style.horizontal_gap);
    // Child Space
    tick_layout!(cx.style.padding_left);
    tick_layout!(cx.style.padding_right);
    tick_layout!(cx.style.padding_top);
    tick_layout!(cx.style.padding_bottom);

    // Tick animations on custom color properties
    for store in cx.style.custom_color_props.values_mut() {
        redraw_entities.extend(store.tick(time));
    }
    // Tick animations on custom length properties
    for store in cx.style.custom_length_props.values_mut() {
        redraw_entities.extend(store.tick(time));
    }
    // Tick animations on custom font-size properties
    for store in cx.style.custom_font_size_props.values_mut() {
        reflow_entities.extend(store.tick(time));
    }
    // Tick animations on custom letter-spacing properties
    for store in cx.style.custom_letter_spacing_props.values_mut() {
        reflow_entities.extend(store.tick(time));
    }
    // Tick animations on custom line-height properties
    for store in cx.style.custom_line_height_props.values_mut() {
        reflow_entities.extend(store.tick(time));
    }
    // Tick animations on custom units properties
    for store in cx.style.custom_units_props.values_mut() {
        has_active_layout_animations |= store.has_animations();
        relayout_entities.extend(store.tick_changed(time));
    }
    // Tick animations on custom opacity properties
    for store in cx.style.custom_opacity_props.values_mut() {
        redraw_entities.extend(store.tick(time));
    }
    // Tick animations on custom shadow properties.
    for store in cx.style.custom_shadow_props.values_mut() {
        redraw_entities.extend(store.tick(time));
    }

    // CSS animation lifecycle events are emitted once per named animation.
    let lifecycle_events = cx.style.tick_css_animation_events(time);
    for lifecycle_event in lifecycle_events {
        let entity = lifecycle_event.entity;
        cx.event_queue.push_back(
            Event::new(lifecycle_event).target(entity).origin(entity).propagate(Propagation::Up),
        );
    }

    for entity in relayout_entities.iter() {
        cx.style.needs_relayout(*entity);
    }

    for entity in redraw_entities.iter() {
        cx.needs_redraw(*entity);
    }

    for entity in reflow_entities.iter() {
        cx.style.text_construction.insert(*entity);
    }

    for entity in retransform_entities.iter() {
        cx.needs_retransform(*entity);
        cx.needs_redraw(*entity);
    }

    for entity in reclip_entities.iter() {
        cx.needs_reclip(*entity);
        cx.needs_redraw(*entity);
    }

    has_active_layout_animations
        | !redraw_entities.is_empty()
        | !relayout_entities.is_empty()
        | !reflow_entities.is_empty()
        | !retransform_entities.is_empty()
        | !reclip_entities.is_empty()
}
