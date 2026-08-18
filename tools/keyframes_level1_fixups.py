from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"anchor not found in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1))


# cssparser exports match_ignore_ascii_case as a macro; import it explicitly in generated modules.
replace_once(
    "crates/vizia_style/src/values/animation.rs",
    "use cssparser::{ParseError, ParseErrorKind, Parser, Token};",
    "use cssparser::{match_ignore_ascii_case, ParseError, ParseErrorKind, Parser, Token};",
)
replace_once(
    "crates/vizia_style/src/values/easing.rs",
    "use cssparser::{ParseError, ParseErrorKind, Parser, Token};",
    "use cssparser::{match_ignore_ascii_case, ParseError, ParseErrorKind, Parser, Token};",
)

# Keep filter-list fallback inside vizia_core without violating Rust's orphan rules.
p = ROOT / "crates/vizia_core/src/animation/interpolator.rs"
text = p.read_text()
text = text.replace("                    start.clone().into()\n", "                    Filter::List(start.clone())\n")
text = text.replace("                    end.clone().into()\n", "                    Filter::List(end.clone())\n")
start = text.find("\nimpl From<Vec<Filter>> for Filter {\n")
if start >= 0:
    end = text.find("\n}\n", start + 1)
    if end < 0:
        raise RuntimeError("could not remove orphan Filter From impl")
    text = text[:start] + text[end + 3 :]
p.write_text(text)

# Track names originating from stylesheets separately so a stylesheet reload can cancel removed
# @keyframes without destroying animations registered through the explicit Rust API.
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "    pub(crate) animations: HashMap<String, Animation>,\n    // List of animations to be started on the next frame\n",
    "    pub(crate) animations: HashMap<String, Animation>,\n    pub(crate) css_animation_names: HashSet<String>,\n    // List of animations to be started on the next frame\n",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "                        self.animation_timelines.insert(animation_id, animation_timeline);\n                        self.animations.insert(name, animation_id);\n",
    "                        self.animation_timelines.insert(animation_id, animation_timeline);\n                        self.css_animation_names.insert(name.clone());\n                        self.animations.insert(name, animation_id);\n",
)
replace_once(
    "crates/vizia_core/src/style/mod.rs",
    "        self.animation_timelines.clear();\n        self.animations.clear();\n        self.disabled.clear_rules();\n",
    r'''        self.animation_timelines.clear();
        for name in std::mem::take(&mut self.css_animation_names) {
            self.animations.remove(&name);
        }
        self.disabled.clear_rules();
''',
)

print("generated CSS animation fixups applied")
