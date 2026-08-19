from pathlib import Path

for path in [
    Path("crates/vizia_core/src/storage/animatable_set.rs"),
    Path("crates/vizia_core/src/storage/animatable_var_set.rs"),
]:
    text = path.read_text()
    marker = "    pub(crate) fn update_css_animation(\n"
    replacement = (
        "    // Updating one CSS effect is an atomic store operation: identity, order, timing,\n"
        "    // easing, composition and the sampling timestamp must remain synchronized.\n"
        "    #[allow(clippy::too_many_arguments)]\n"
        "    pub(crate) fn update_css_animation(\n"
    )
    if replacement in text:
        continue
    if marker not in text:
        raise RuntimeError(f"update_css_animation marker not found in {path}")
    path.write_text(text.replace(marker, replacement, 1))
