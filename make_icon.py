#!/usr/bin/env python3
"""Build icon/Stache.icns and icon/Stache_glyph.png from Tim's artwork - v2.1.0

    ./venv/bin/python make_icon.py

v2.0.0 replaced the drawn placeholder with Tim's own artwork: three
moustaches on yellow behind a translucent S, drawn in Pixelmator Pro.
`icon/stache.pxd` is the master and `icon/StacheIcon_source.png` is its
512-point export, which is what this script reads.  Don't invent icon art
for this app - the artwork exists.

v2.1.0 also renders the menu bar mark: the same Old English S that is in
the artwork, in "Olde English" — the face Tim drew it with.  (A first pass
picked "Old English Five", whose S is much wider and squatter; the two names
are one letter apart and a substring search for "old english" does not even
find "Olde English".)  It
is rendered here rather than at runtime so the app carries a PNG and does not
depend on the font being installed, and it is cropped to the glyph's own ink
because AppKit centres text on its line box, which would otherwise hang the S
low in the menu bar.

macOS puts app icon artwork on an 824-point square centred in a 1024-point
canvas, with a corner radius of 185.4 - the "squircle" every stock icon
sits on.  Getting that grid wrong is what makes a third-party icon look
subtly too big or too square beside Apple's in the Dock, which is exactly
what the full-bleed alternative did.

The source is 512 points and the largest slice an icns needs is 1024, so the
artwork is enlarged 2x on the way in.  Re-exporting the .pxd at 1024 would
be sharper; nothing else here would have to change.
"""

import os
import shutil
import subprocess

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(HERE, "icon")
SOURCE = os.path.join(ICON_DIR, "StacheIcon_source.png")

CANVAS = 1024
CONTENT = 824
RADIUS = 185.4
INSET = (CANVAS - CONTENT) // 2


def squircle_mask(size, radius):
    """A rounded-rectangle mask, drawn 4x and downsampled so the corners are
    smooth rather than stair-stepped."""
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size * 4 - 1, size * 4 - 1), radius=radius * 4, fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def build_png():
    if not os.path.exists(SOURCE):
        raise SystemExit("make_icon.py: %s is missing — it is the artwork, "
                         "exported from icon/stache.pxd" % SOURCE)
    art = Image.open(SOURCE).convert("RGBA")
    plate = art.resize((CONTENT, CONTENT), Image.LANCZOS)
    plate.putalpha(squircle_mask(CONTENT, RADIUS))
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(plate, (INSET, INSET), plate)
    return canvas


def build_icns(png):
    iconset = os.path.join(ICON_DIR, "Stache.iconset")
    shutil.rmtree(iconset, ignore_errors=True)
    os.makedirs(iconset)
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px = size * scale
            name = "icon_%dx%d%s.png" % (size, size, "@2x" if scale == 2 else "")
            png.resize((px, px), Image.LANCZOS).save(
                os.path.join(iconset, name))
    out = os.path.join(ICON_DIR, "Stache.icns")
    subprocess.run(["/usr/bin/iconutil", "-c", "icns", iconset, "-o", out],
                   check=True)
    shutil.rmtree(iconset, ignore_errors=True)
    return out


GLYPH_FONT = "Olde English"
GLYPH_PX = 36                     # 18pt in the menu bar, at 2x


def build_glyph():
    """The Old English S, cropped to its ink, as a menu bar template image."""
    from AppKit import (NSFont, NSColor, NSBitmapImageRep, NSGraphicsContext,
                        NSAttributedString, NSFontAttributeName,
                        NSForegroundColorAttributeName, NSDeviceRGBColorSpace,
                        NSBitmapImageFileTypePNG, NSMakePoint, NSApplication)
    NSApplication.sharedApplication()
    font = NSFont.fontWithName_size_(GLYPH_FONT, 300)
    if font is None:
        raise SystemExit("make_icon.py: the font %r is not installed"
                         % GLYPH_FONT)
    side = 500
    rep = NSBitmapImageRep.alloc().\
        initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, side, side, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0)
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(ctx)
    NSAttributedString.alloc().initWithString_attributes_("S", {
        NSFontAttributeName: font,
        NSForegroundColorAttributeName: NSColor.blackColor(),
    }).drawAtPoint_(NSMakePoint(90, 90))
    NSGraphicsContext.restoreGraphicsState()

    import io
    data = rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, {})
    glyph = Image.open(io.BytesIO(bytes(data))).convert("RGBA")
    box = glyph.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("make_icon.py: the glyph rendered empty")
    glyph = glyph.crop(box)
    width = max(1, round(glyph.width * GLYPH_PX / glyph.height))
    glyph = glyph.resize((width, GLYPH_PX), Image.LANCZOS)
    out = os.path.join(ICON_DIR, "Stache_glyph.png")
    glyph.save(out)
    return out, glyph.size


if __name__ == "__main__":
    os.makedirs(ICON_DIR, exist_ok=True)
    png = build_png()
    png.save(os.path.join(ICON_DIR, "Stache_1024.png"))
    icns = build_icns(png)
    print("wrote %s (%d bytes)" % (icns, os.path.getsize(icns)))
    glyph, size = build_glyph()
    print("wrote %s (%dx%d)" % (glyph, size[0], size[1]))
