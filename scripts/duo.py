"""Shared, explicit SVG color roles for the two duo styles."""

DUO_STYLES = ("duocolor", "duotone")
DEFAULTS = {
    "light": {"primary": "#245B9E", "secondary": "#5B87B7"},
    "dark": {"primary": "#93C5FD", "secondary": "#60A5FA"},
}
SECONDARY = "var(--fedora-secondary, #5B87B7)"


def apply_colors(svg, theme="light", primary="currentColor", secondary=None):
    svg.set("color", (
        f"var(--fedora-primary, {DEFAULTS[theme]['primary']})"
        if primary == "currentColor" else primary
    ))
    for node in svg.iter():
        for attr in ("fill", "stroke"):
            if node.get(attr, "").startswith("var(--fedora-secondary, "):
                node.set(attr, (
                    secondary if secondary is not None
                    else f"var(--fedora-secondary, {DEFAULTS[theme]['secondary']})"
                ))
