from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"pattern not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


# Lifecycle sampling must use the same reversed progress as rendering/snapshots.
replace_once(
    "crates/vizia_core/src/style/css_animation.rs",
    '''                let sample = if instance.timeline_driven {
                    instance.clock.timing.sample_timeline_progress(instance.timeline_progress)
                } else {
                    instance.clock.sample(now)
                };
''',
    '''                let sample = if instance.timeline_driven {
                    instance.clock.timing.sample_timeline_progress(
                        instance.clock.map_timeline_progress(instance.timeline_progress),
                    )
                } else {
                    instance.clock.sample(now)
                };
''',
)

# Make the public snapshot wording correct for both document and progress timelines.
replace_once(
    "crates/vizia_core/src/animation/runtime.rs",
    '''    /// Current document-timeline time in seconds, including the CSS delay interval.
    pub current_time: f32,
''',
    '''    /// Current local effect time in seconds. For progress timelines this is the sampled
    /// progress mapped onto the effect's active duration rather than wall-clock time.
    pub current_time: f32,
''',
)

# Regression: a filled effect that reached t=1 must become sampleable again after seek/reverse.
path = Path("crates/vizia_core/src/style/css_animation.rs")
text = path.read_text()
anchor = '''    #[test]
    fn list_values_repeat_to_match_animation_name_length() {
'''
test = '''    #[test]
    fn runtime_seek_revives_a_filled_finished_effect() {
        let mut style = Style::default();
        let entity = Entity::root();
        let animation = style.add_animation(
            AnimationBuilder::new()
                .keyframe(0.0, |key| key.opacity(0.0))
                .keyframe(1.0, |key| key.opacity(1.0)),
        );
        style.animations.insert("revive".into(), animation);
        style
            .animation_name
            .insert(entity, AnimationNames(vec![AnimationName::Custom("revive".into())]));
        style
            .animation_duration
            .insert(entity, AnimationDurations(vec![AnimationDuration(AnimationTime(2.0))]));
        style.animation_fill_mode.insert(
            entity,
            AnimationFillModes(vec![AnimationFillMode::Forwards]),
        );
        style.opacity.insert(entity, Opacity(0.0));

        let start = Instant::now();
        style.sync_css_animations(entity, start);
        style.opacity.tick(start + Duration::from_secs(3));
        let id = style.css_animation_snapshots(entity, start + Duration::from_secs(3))[0].id;
        assert_eq!(
            style.css_animation_snapshots(entity, start + Duration::from_secs(3))[0].state,
            CssAnimationPlaybackState::Finished
        );

        let now = start + Duration::from_secs(3);
        assert!(style.control_css_animation(id, CssAnimationControl::Seek(0.5), now));
        style.opacity.tick(now);
        let opacity = style.opacity.get(entity).expect("revived opacity output").0;
        assert!((opacity - 0.25).abs() < 0.001, "seek should resample a filled effect");
        assert_ne!(
            style.css_animation_snapshots(entity, now)[0].state,
            CssAnimationPlaybackState::Finished
        );
    }

'''
if test not in text:
    if anchor not in text:
        raise RuntimeError("runtime regression test anchor not found")
    text = text.replace(anchor, test + anchor, 1)
    path.write_text(text)
