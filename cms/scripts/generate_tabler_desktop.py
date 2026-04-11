"""
generate_tabler_desktop.py
--------------------------
Generates static/tabler.desktop.css from the Starlette Admin bundled Tabler CSS.

Rules:
  - @media (min-width: Xpx) where X <= 1280 and no compound conditions
    → inlined (wrapper removed, inner rules promoted to top-level)
  - Everything else (@media max-width, print, prefers-*, min-width > 1280px,
    compound conditions) → stripped entirely

Re-run this script whenever starlette-admin is upgraded and ships a new Tabler CSS.

Usage (from cms/ directory):
    python3 scripts/generate_tabler_desktop.py
"""

import re
import pathlib

SRC = pathlib.Path(
    ".venv/lib/python3.9/site-packages/starlette_admin/statics/css/tabler.min-1.1.0.css"
)
DST = pathlib.Path("static/tabler.desktop.css")


def process(css: str) -> str:
    result, i, n = [], 0, len(css)

    while i < n:
        idx = css.find("@media", i)
        if idx == -1:
            result.append(css[i:])
            break

        # Append everything before this @media block
        result.append(css[i:idx])

        brace = css.find("{", idx)
        if brace == -1:
            result.append(css[idx:])
            break

        condition = css[idx + 6 : brace].strip()

        # Walk forward to find the matching closing brace
        depth, j = 0, brace
        while j < n:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1

        inner = css[brace + 1 : j - 1]

        # Only inline simple (min-width: Xpx) conditions where X <= 1280
        m = re.match(r"^\(min-width:(\d+)px\)$", condition)
        if m and int(m.group(1)) <= 1280:
            result.append(inner)
        # else: strip the block entirely

        i = j

    return "".join(result)


if __name__ == "__main__":
    if not SRC.exists():
        raise FileNotFoundError(f"Source not found: {SRC}")

    src_text = SRC.read_text(encoding="utf-8")
    output = process(src_text)

    header = (
        "/* Generated from tabler.min-1.1.0.css — see scripts/generate_tabler_desktop.py\n"
        "   @media breakpoints stripped; min-width <= 1280px rules inlined.\n"
        "   Re-run this script if starlette-admin is upgraded. */\n\n"
    )

    DST.write_text(header + output, encoding="utf-8")
    print(f"Written {DST.stat().st_size:,} bytes → {DST}")
