"""py2app build for Stache.app

    ./venv/bin/python make_icon.py      (icon/ must be built first)
    ./venv/bin/python setup.py py2app

LSUIElement is what makes this a background app: no Dock icon and no menu
bar of its own, so the only things it ever puts on screen are its menu bar
item and the picker the hotkey raises.
"""

import re
from pathlib import Path

from setuptools import setup

APP = ["stache.py"]
# The menu bar mark ships as a PNG so the app does not depend on the
# "Old English Five" font being installed on the machine running it.
DATA_FILES = [("", ["icon/Stache_glyph.png"])]


def app_version():
    """The single source of truth: APP_VERSION in stache.py."""
    source = Path(__file__).with_name("stache.py").read_text()
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', source, re.MULTILINE)
    if not match:
        raise SystemExit("setup.py: APP_VERSION not found in stache.py")
    return match.group(1)


VERSION = app_version()

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "icon/Stache.icns",
    # Pillow is a build-time dependency of make_icon.py only; the app draws
    # its thumbnails with AppKit, so keeping PIL out halves the bundle.
    "excludes": ["PIL", "Pillow", "tkinter", "test", "unittest"],
    # Quartz as a PACKAGE, not an include. py2app compiles an include into
    # python314.zip, and codesign cannot reach inside a zip — which is how
    # PixProFitText shipped 18 unsigned dylibs and had the whole archive
    # rejected by Apple. A package is copied out as a real directory tree
    # where the Mach-O walk in build.sh signs everything it holds.
    "packages": ["Quartz"],
    "plist": {
        "CFBundleName": "Stache",
        "CFBundleDisplayName": "Stache",
        "CFBundleIdentifier": "com.timmccoy.stache",
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
        # Accessory app: no Dock icon, no menu bar.
        "LSUIElement": True,
        "NSHumanReadableCopyright":
            "Copyright © 2026 Tim McCoy. All rights reserved.",
        "CFBundleGetInfoString":
            "Stache — clipboard history for text and images, recalled by hotkey.",
    },
}

setup(
    name="Stache",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
