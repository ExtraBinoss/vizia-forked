from pathlib import Path

rust = Path('examples/widget_gallery/src/views/animation.rs')
text = rust.read_text()

if '    TransformTranslateOnly,\n' not in text:
    text = text.replace(
        '    Transform,\n    TransformOrigin,',
        '    Transform,\n    TransformTranslateOnly,\n    TransformRotateOnly,\n    TransformCombined,\n    TransformOrigin,',
        1,
    )

start = text.index('const TRANSFORM_VARIANTS: &[DocVariant] = &[')
end = text.index('\n];', start) + 3
block = text[start:end]
block = block.replace('example: ExampleKind::Transform,', 'example: ExampleKind::TransformTranslateOnly,', 1)
block = block.replace('example: ExampleKind::Transform,', 'example: ExampleKind::TransformRotateOnly,', 1)
block = block.replace('example: ExampleKind::Transform,', 'example: ExampleKind::TransformCombined,', 1)
text = text[:start] + block + text[end:]

arm = '        ExampleKind::Transform => simple_stage(cx, "transform", "animation-doc-transform"),\n'
if 'ExampleKind::TransformTranslateOnly =>' not in text:
    replacement = arm + '''        ExampleKind::TransformTranslateOnly => surface_stage(cx, "translateX", "animation-doc-transform-translate-only"),
        ExampleKind::TransformRotateOnly => surface_stage(cx, "rotate", "animation-doc-transform-rotate-only"),
        ExampleKind::TransformCombined => surface_stage(cx, "combined", "animation-doc-transform-combined"),
'''
    if arm not in text:
        raise SystemExit('transform preview arm not found')
    text = text.replace(arm, replacement, 1)

rust.write_text(text)

css = Path('examples/widget_gallery/resources/themes/animation.css')
c = css.read_text()
if '@keyframes doc-transform-translate-only' not in c:
    c += r'''

@keyframes doc-transform-translate-only {
    from { transform: translateX(-120px); }
    to { transform: translateX(120px); }
}
@keyframes doc-transform-rotate-only {
    from { transform: rotate(-35deg); }
    to { transform: rotate(325deg); }
}
@keyframes doc-transform-combined {
    from { transform: translate(-100px, 0px) rotate(-25deg) scale(0.78, 0.78); }
    to { transform: translate(100px, 0px) rotate(335deg) scale(1.12, 1.12); }
}
.animation-doc-transform-translate-only {
    background-color: #2563eb;
    color: white;
    animation: doc-transform-translate-only 1500ms ease-in-out infinite alternate;
}
.animation-doc-transform-rotate-only {
    background-color: #7c3aed;
    color: white;
    animation: doc-transform-rotate-only 1800ms linear infinite;
}
.animation-doc-transform-combined {
    background-color: #0f9d58;
    color: white;
    animation: doc-transform-combined 1800ms ease-in-out infinite alternate;
}
'''
css.write_text(c)

exec(Path('tools/animation_doc_variant_longhands.py').read_text())
