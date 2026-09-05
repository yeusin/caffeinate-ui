#!/usr/bin/env python3
"""Generate the macOS App icon (assets/app_icon.png and assets/app.icns).

Creates a macOS Big Sur+ style app icon:
- 1024x1024 canvas
- Rounded squircle with soft shadow
- Rich espresso brown background
- Crisp white caffeinate coffee cup emblem
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def generate_app_icon() -> None:
    root = Path(__file__).resolve().parent.parent
    logo_path = root / "assets" / "logo_on.png"
    out_png = root / "assets" / "app_icon.png"
    out_icns = root / "assets" / "app.icns"

    if not logo_path.exists():
        raise FileNotFoundError(f"Source logo not found at {logo_path}")

    size = 1024
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Squircle geometry
    sx, sy, sw, sh = 100, 96, 824, 824
    r = 185

    # 1. Drop shadow layer
    shadow_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_canvas)
    s_draw.rounded_rectangle(
        [sx - 2, sy + 16, sx + sw + 2, sy + sh + 20],
        radius=r + 4,
        fill=(0, 0, 0, 95),
    )
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(26))

    # 2. Squircle mask
    bg_mask = Image.new("L", (size, size), 0)
    bg_mask_draw = ImageDraw.Draw(bg_mask)
    bg_mask_draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=r, fill=255)

    # 3. Espresso brown vertical gradient
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    c_top = (78, 47, 22)    # #4E2F16
    c_mid = (61, 35, 20)    # #3D2314 (rich espresso)
    c_bot = (40, 21, 10)    # #28150A (dark roast base)

    grad_draw = ImageDraw.Draw(grad)
    for y in range(sy, sy + sh + 1):
        t = (y - sy) / sh
        if t < 0.5:
            sub_t = t / 0.5
            c = tuple(int(c_top[i] + (c_mid[i] - c_top[i]) * sub_t) for i in range(3))
        else:
            sub_t = (t - 0.5) / 0.5
            c = tuple(int(c_mid[i] + (c_bot[i] - c_mid[i]) * sub_t) for i in range(3))
        grad_draw.line([(sx, y), (sx + sw, y)], fill=c + (255,))

    # 4. Subtle inner border highlight
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(highlight)
    hl_draw.rounded_rectangle(
        [sx + 1, sy + 1, sx + sw - 1, sy + sh - 1],
        radius=r - 1,
        outline=(255, 255, 255, 36),
        width=2,
    )

    # 5. Cup emblem
    logo = Image.open(logo_path).convert("RGBA")
    cup_size = 490
    cup_resized = logo.resize((cup_size, cup_size), Image.Resampling.LANCZOS)

    # Optically centered: slight shift left (-8px) to balance handle on right
    cx = int((size - cup_size) / 2) - 8
    cy = int(sy + (sh - cup_size) / 2) + 2

    # Composite layers
    canvas = Image.alpha_composite(canvas, shadow_canvas)
    squircle_layer = Image.composite(
        grad, Image.new("RGBA", (size, size), (0, 0, 0, 0)), bg_mask
    )
    canvas = Image.alpha_composite(canvas, squircle_layer)
    canvas = Image.alpha_composite(canvas, highlight)
    canvas.paste(cup_resized, (cx, cy), cup_resized)

    # Save master PNG
    canvas.save(out_png, "PNG")
    print(f"Generated {out_png}")

    # Save multi-resolution ICNS
    canvas.save(out_icns, format="ICNS")
    print(f"Generated {out_icns}")


if __name__ == "__main__":
    generate_app_icon()
