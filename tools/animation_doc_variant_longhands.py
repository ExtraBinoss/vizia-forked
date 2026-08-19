from pathlib import Path
import re

rust = Path('examples/widget_gallery/src/views/animation.rs')
text = rust.read_text()
text = text.replace(
    'DocVariant { label: "All", css: "@keyframes demo {\\n  from { border-width: 2px; }\\n  to   { border-width: 18px; }\\n}\\n\\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthAll },',
    'DocVariant { label: "All", css: "@keyframes demo {\\n  from { border-top-width: 2px; border-right-width: 2px; border-bottom-width: 2px; border-left-width: 2px; }\\n  to   { border-top-width: 18px; border-right-width: 18px; border-bottom-width: 18px; border-left-width: 18px; }\\n}\\n\\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::BorderWidthAll },',
)
text = text.replace(
    'DocVariant { label: "All", css: "@keyframes demo {\\n  from { border-color: #3b82f6; }\\n  to   { border-color: #f43f5e; }\\n}\\n\\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorAll },',
    'DocVariant { label: "All", css: "@keyframes demo {\\n  from { border-top-color: #3b82f6; border-right-color: #3b82f6; border-bottom-color: #3b82f6; border-left-color: #3b82f6; }\\n  to   { border-top-color: #f43f5e; border-right-color: #f43f5e; border-bottom-color: #f43f5e; border-left-color: #f43f5e; }\\n}\\n\\n.target { animation: demo 1.3s ease-in-out infinite alternate; }", example: ExampleKind::BorderColorAll },',
)
text = text.replace(
    'DocVariant { label: "All", css: "@keyframes demo {\\n  from { corner-radius: 6px; }\\n  to   { corner-radius: 72px; }\\n}\\n\\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusAll },',
    'DocVariant { label: "All", css: "@keyframes demo {\\n  from { corner-top-left-radius: 6px; corner-top-right-radius: 6px; corner-bottom-left-radius: 6px; corner-bottom-right-radius: 6px; }\\n  to   { corner-top-left-radius: 72px; corner-top-right-radius: 72px; corner-bottom-left-radius: 72px; corner-bottom-right-radius: 72px; }\\n}\\n\\n.target { animation: demo 1.4s ease-in-out infinite alternate; }", example: ExampleKind::CornerRadiusAll },',
)
rust.write_text(text)

css = Path('examples/widget_gallery/resources/themes/animation.css')
c = css.read_text()
c = c.replace(
    '@keyframes doc-border-width-all { from { border-width: 2px; } to { border-width: 18px; } }',
    '@keyframes doc-border-width-all { from { border-top-width: 2px; border-right-width: 2px; border-bottom-width: 2px; border-left-width: 2px; } to { border-top-width: 18px; border-right-width: 18px; border-bottom-width: 18px; border-left-width: 18px; } }',
)
c = c.replace(
    '@keyframes doc-border-color-all { from { border-color: #3b82f6; } to { border-color: #f43f5e; } }',
    '@keyframes doc-border-color-all { from { border-top-color: #3b82f6; border-right-color: #3b82f6; border-bottom-color: #3b82f6; border-left-color: #3b82f6; } to { border-top-color: #f43f5e; border-right-color: #f43f5e; border-bottom-color: #f43f5e; border-left-color: #f43f5e; } }',
)
c = c.replace(
    '@keyframes doc-radius-all { from { corner-radius: 6px; } to { corner-radius: 72px; } }',
    '@keyframes doc-radius-all { from { corner-top-left-radius: 6px; corner-top-right-radius: 6px; corner-bottom-left-radius: 6px; corner-bottom-right-radius: 6px; } to { corner-top-left-radius: 72px; corner-top-right-radius: 72px; corner-bottom-left-radius: 72px; corner-bottom-right-radius: 72px; } }',
)

# The generic text target must already be comfortable even before a property-specific surface class.
c = re.sub(
    r'\.animation-doc-target \{.*?\n\}',
    '''.animation-doc-target {
    width: auto;
    height: auto;
    min-width: 190px;
    min-height: 92px;
    padding: 22px 30px;
    alignment: center;
    corner-radius: 10px;
    background-color: var(--primary);
    color: var(--primary-foreground);
    font-weight: bold;
    text-align: center;
    text-wrap: true;
}''',
    c,
    count=1,
    flags=re.S,
)
css.write_text(c)
