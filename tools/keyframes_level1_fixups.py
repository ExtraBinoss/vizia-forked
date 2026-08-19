from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for relative in [
    "crates/vizia_core/src/storage/animatable_set.rs",
    "crates/vizia_core/src/storage/animatable_var_set.rs",
]:
    path = ROOT / relative
    text = path.read_text()
    old = "    pub(crate) fn play_css_animation(\n"
    new = (
        "    // CSS playback is installed as one cohesive operation across both store variants.\n"
        "    #[allow(clippy::too_many_arguments)]\n"
        "    pub(crate) fn play_css_animation(\n"
    )
    if new not in text:
        if old not in text:
            raise RuntimeError(f"play_css_animation anchor not found in {relative}")
        path.write_text(text.replace(old, new, 1))

print("annotated CSS animation store entry points for clippy")
