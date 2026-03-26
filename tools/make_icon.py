# Shuraksha - Icon Generator


import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

# Output path
OUTPUT_DIR  = Path(__file__).parent.parent / 'assets' / 'icons'
OUTPUT_ICO  = OUTPUT_DIR / 'icon.ico'
OUTPUT_PNG  = OUTPUT_DIR / 'icon_256.png'

# Shuraksha brand colours
C_BG_DARK  = (6,   9,  18, 255)    # Deep navy background
C_CYAN     = (56, 200, 255, 255)    # Bright cyan accent
C_RED      = (204,  34,   0, 255)   # Deep red for svastika
C_GOLD     = (255, 143,   0, 255)   # Saffron gold
C_WHITE    = (224, 244, 255, 255)   # Bright white text


def draw_svastika(draw, cx, cy, arm, thick, color):
    """
    Draw a traditional Hindu svastika (right-facing, auspicious).
    cx, cy  = centre point
    arm     = length of each arm from centre
    thick   = line thickness
    color   = RGBA tuple
    """
    h = thick // 2

    # Centre square
    draw.rectangle(
        [cx - h, cy - h, cx + h, cy + h],
        fill=color
    )

    # Four arms and their end caps (clockwise from top)

    # Top arm going up, then right cap
    draw.rectangle(
        [cx - h, cy - arm, cx + h, cy],
        fill=color
    )
    draw.rectangle(
        [cx + h, cy - arm, cx + arm, cy - arm + thick],
        fill=color
    )

    # Right arm going right, then down cap
    draw.rectangle(
        [cx, cy - h, cx + arm, cy + h],
        fill=color
    )
    draw.rectangle(
        [cx + arm - thick, cy + h, cx + arm, cy + arm],
        fill=color
    )

    # Bottom arm going down, then left cap
    draw.rectangle(
        [cx - h, cy, cx + h, cy + arm],
        fill=color
    )
    draw.rectangle(
        [cx - arm, cy + arm - thick, cx - h, cy + arm],
        fill=color
    )

    # Left arm going left, then up cap
    draw.rectangle(
        [cx - arm, cy - h, cx, cy + h],
        fill=color
    )
    draw.rectangle(
        [cx - arm, cy - arm, cx - arm + thick, cy - h],
        fill=color
    )


def draw_shield_outline(draw, w, h, color, width=3):
    """
    Draw a simple shield outline.
    The shield is taller than it is wide with a pointed bottom.
    """
    pad   = int(w * 0.08)
    top   = pad
    left  = pad
    right = w - pad
    mid_y = int(h * 0.65)
    bot_x = w // 2
    bot_y = h - pad

    points = [
        (left,  top),
        (right, top),
        (right, mid_y),
        (bot_x, bot_y),
        (left,  mid_y),
    ]

    # Draw outline by drawing multiple offset rectangles
    for i in range(width):
        offset_pts = [
            (left + i,  top + i),
            (right - i, top + i),
            (right - i, mid_y - i),
            (bot_x,     bot_y - i * 2),
            (left + i,  mid_y - i),
        ]
        draw.polygon(offset_pts, outline=color)


def draw_shield_fill(draw, w, h, color):
    """Fill the shield interior with a solid colour."""
    pad   = int(w * 0.08) + 3
    top   = pad
    left  = pad
    right = w - pad
    mid_y = int(h * 0.65)
    bot_x = w // 2
    bot_y = h - pad - 2

    points = [
        (left,  top),
        (right, top),
        (right, mid_y),
        (bot_x, bot_y),
        (left,  mid_y),
    ]
    draw.polygon(points, fill=color)


def create_icon_image(size: int) -> Image.Image:
    """
    Create the Shuraksha icon at the given pixel size.
    Uses RGBA mode for transparency support.
    """
    img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    w, h = size, size
    cx   = w // 2
    cy   = h // 2

    # Fill shield background
    draw_shield_fill(draw, w, h, C_BG_DARK)

    # Draw shield border in cyan
    border_width = max(1, size // 32)
    draw_shield_outline(draw, w, h, C_CYAN, border_width)

    # Draw the svastika in the centre
    # Scale the svastika proportionally to the icon size
    arm   = int(size * 0.22)
    thick = max(2, int(size * 0.07))

    # Shift svastika up slightly from centre
    svast_cy = int(cy * 0.95)
    draw_svastika(draw, cx, svast_cy, arm, thick, C_RED)

    # For larger sizes add the four gold corner dots
    if size >= 48:
        dot_r  = max(1, size // 20)
        offset = int(size * 0.28)
        for dx, dy in [
            (-offset, -offset),
            ( offset, -offset),
            (-offset,  offset),
            ( offset,  offset),
        ]:
            dot_cx = cx + dx
            dot_cy = svast_cy + dy
            draw.ellipse(
                [dot_cx - dot_r, dot_cy - dot_r,
                 dot_cx + dot_r, dot_cy + dot_r],
                fill=C_GOLD
            )

    # For the largest size add a thin gold ring
    if size >= 128:
        ring_r = int(size * 0.42)
        ring_w = max(1, size // 64)
        draw.ellipse(
            [cx - ring_r, cy - ring_r,
             cx + ring_r, cy + ring_r],
            outline=(*C_GOLD[:3], 120),
            width=ring_w
        )

    return img


def main():
    print("Shuraksha Icon Generator")
    print("------------------------")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate all required sizes
    sizes  = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = create_icon_image(size)
        images.append(img)
        print(f"  Generated {size}x{size}")

    # Save the 256x256 as a standalone PNG
    images[-1].save(str(OUTPUT_PNG))
    print(f"  Saved PNG:  {OUTPUT_PNG}")

    # Save all sizes packed into one .ico file
    # The first image in the list is the primary icon
    # Windows will pick the most appropriate size automatically
    images[0].save(
        str(OUTPUT_ICO),
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"  Saved ICO:  {OUTPUT_ICO}")
    print("")
    print("Icon generation complete.")


if __name__ == '__main__':
    main()
