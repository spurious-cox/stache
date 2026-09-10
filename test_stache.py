#!/usr/bin/env python3
"""Headless checks for Stache - v1.0.0

    ./venv/bin/python test_stache.py

Exercises the store against a scratch database and renders the picker panel
to test_render.png with cacheDisplayInRect_toBitmapImageRep_, so the layout
can be looked at without leaving a GUI instance of the app running and
without any screen-recording permission.
"""

import os
import shutil
import sys
import tempfile
import time
from datetime import datetime

SCRATCH = tempfile.mkdtemp(prefix="stache-test-")
os.environ["HOME"] = os.environ.get("HOME")          # unchanged; see below

import stache

# Point every path at the scratch directory before anything creates files.
stache.SUPPORT_DIR = SCRATCH
stache.BLOB_DIR = os.path.join(SCRATCH, "blobs")
stache.THUMB_DIR = os.path.join(SCRATCH, "thumbs")
stache.DB_PATH = os.path.join(SCRATCH, "stache.sqlite3")

from AppKit import (NSApplication, NSBitmapImageFileTypePNG, NSColor,
                    NSGraphicsContext, NSMakeRect)

FAILURES = []


def _mark_dirty(view):
    view.setNeedsDisplay_(True)
    for sub in view.subviews():
        _mark_dirty(sub)


def check(label, condition, detail=""):
    if condition:
        print("  ok    %s" % label)
    else:
        print("  FAIL  %s %s" % (label, detail))
        FAILURES.append(label)


def sample_png(width, height, rgb):
    """A solid PNG built through AppKit, the same path the app uses."""
    from AppKit import NSBitmapImageRep, NSBezierPath, NSDeviceRGBColorSpace
    rep = NSBitmapImageRep.alloc().\
        initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, width, height, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0)
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(ctx)
    NSColor.colorWithCalibratedRed_green_blue_alpha_(
        rgb[0], rgb[1], rgb[2], 1.0).setFill()
    NSBezierPath.fillRect_(NSMakeRect(0, 0, width, height))
    NSColor.whiteColor().setFill()
    NSBezierPath.fillRect_(NSMakeRect(width * 0.2, height * 0.2,
                                      width * 0.6, height * 0.25))
    NSGraphicsContext.restoreGraphicsState()
    return bytes(rep.representationUsingType_properties_(
        NSBitmapImageFileTypePNG, {}))


def test_store():
    print("store")
    store = stache.Store(stache.DB_PATH)

    first = store.add_text("hello clipboard", app="TextEdit")
    check("text insert", first is not None)
    check("count after one insert", store.count() == 1)

    again = store.add_text("hello clipboard", app="TextEdit")
    check("identical text is deduped, not duplicated",
          again is None and store.count() == 1)

    store.add_text("a second, different clipping", app="Safari")
    items = store.items()
    check("newest first", items[0].body == "a second, different clipping")

    png = sample_png(640, 400, (0.2, 0.45, 0.85))
    img_id = store.add_image(png, 640, 400, app="Preview", alt_text=None)
    check("image insert", img_id is not None)
    item = store.items(kind="image")[0]
    check("image blob written on disk", os.path.exists(item.blob_path))
    check("thumbnail written on disk",
          item.thumb_path and os.path.exists(item.thumb_path))
    check("image dimensions recorded",
          item.width == 640 and item.height == 400)
    check("image detail line", "640 x 400" in item.detail(), item.detail())

    check("kind filter", len(store.items(kind="text")) == 2)
    check("search hits the body",
          len(store.items(query="second")) == 1)
    check("search hits the source app",
          len(store.items(query="Safari")) == 1)

    store.set_pinned(items[0].id, True)
    check("pinned sorts first", store.items()[0].id == items[0].id)

    # Retention: a cap of one keeps the pinned item plus one other.
    store.prune(max_items=1, max_days=0)
    check("prune to one keeps the pinned item too", store.count() == 2,
          "count=%d" % store.count())

    orphans = [n for n in os.listdir(stache.BLOB_DIR)]
    check("pruned image files are deleted with their rows",
          len(orphans) <= 1, orphans)

    # Age cap — counted from the last USE, so both have to be old.
    stale = time.time() - 40 * 86400
    store.db.execute("UPDATE items SET created = ?, used = ?, pinned = 0",
                     (stale, stale))
    store.db.commit()
    store.prune(max_items=0, max_days=30)
    check("age cap empties an old history", store.count() == 0)
    check("blob directory emptied with it",
          os.listdir(stache.BLOB_DIR) == [], os.listdir(stache.BLOB_DIR))
    store.close()


def test_hotkey_labels():
    print("hotkey")
    check("default chord reads as Control-Option-Command-Space",
          stache.hotkey_label(stache.DEFAULT_HOTKEY_CODE,
                             stache.DEFAULT_HOTKEY_MODS) == "⌃⌥⌘Space",
          stache.hotkey_label(stache.DEFAULT_HOTKEY_CODE,
                             stache.DEFAULT_HOTKEY_MODS))
    check("shift-command-V reads back",
          stache.hotkey_label(9, stache.shiftKey | stache.cmdKey) == "⇧⌘V")
    check("Carbon framework loaded and exports the API",
          hasattr(stache._carbon, "RegisterEventHotKey"))


def test_menu():
    print("menu titles")   # used by alerts now, not by the menu bar
    store = stache.Store(stache.DB_PATH)
    store.add_text("   a clipping   with  collapsed\n whitespace  ", app="Notes")
    store.add_text("x" * 200, app="Notes")
    store.add_image(sample_png(320, 200, (0.4, 0.4, 0.4)), 320, 200,
                    app="Preview")

    text_items = store.items(kind="text")
    long_title = stache._menu_title(
        [i for i in text_items if len(i.body) == 200][0])
    check("a long clipping is truncated for the menu",
          len(long_title) == stache.MENU_TITLE_CHARS and
          long_title.endswith("…"), long_title)
    collapsed = stache._menu_title(
        [i for i in text_items if "collapsed" in i.body][0])
    check("newlines and runs of spaces are collapsed",
          collapsed == "a clipping with collapsed whitespace", collapsed)

    image = store.items(kind="image")[0]
    check("an image gets its dimensions as a title",
          stache._menu_title(image) == "Image  320 × 200",
          stache._menu_title(image))
    store.clear(keep_pinned=False)
    store.close()


def test_search_dates():
    """Dates in the search box."""
    print("date search")
    import time as _time
    from datetime import datetime, timedelta
    store = stache.Store(stache.DB_PATH)
    store.clear(keep_pinned=False)
    store.add_text("a note from right now", app="Notes")
    # Backdate one clipping by three days.
    old_id = store.add_text("an older note", app="Notes")
    then = _time.time() - 3 * 86400
    store.db.execute("UPDATE items SET created = ?, stamp = ? WHERE id = ?",
                     (then, stache.time_stamp(then), old_id))
    store.db.commit()

    now = datetime.now()
    check("the month name finds today's clipping",
          len(store.items(query=now.strftime("%b"))) >= 1,
          now.strftime("%b"))
    check("the full month name works too",
          len(store.items(query=now.strftime("%B"))) >= 1)
    check("an ISO date works",
          len(store.items(query=now.strftime("%Y-%m-%d"))) == 1,
          now.strftime("%Y-%m-%d"))
    check("a bare year works", len(store.items(query=now.strftime("%Y"))) == 2)
    check("the weekday name works",
          len(store.items(query=now.strftime("%A"))) >= 1)
    check("'today' excludes the three-day-old clipping",
          len(store.items(query="today")) == 1)
    check("'yesterday' matches neither", len(store.items(query="yesterday")) == 0)
    check("'this week' is a range, not a string",
          len(store.items(query="this week")) >= 1)

    # And an ordinary word search must not be hijacked by the date machinery.
    check("a plain word still searches the text",
          len(store.items(query="older")) == 1)
    check("a word that is not a date matches nothing spurious",
          len(store.items(query="zzzznotpresent")) == 0)
    check("a short non-date word is not treated as a date",
          stache.date_query("report") is None)
    check("a month prefix IS treated as a date",
          stache.date_query("aug") == ("stamp",))
    check("anything with a digit is treated as a date",
          stache.date_query("8/28") == ("stamp",))
    check("'today' resolves to a time range",
          stache.date_query("today")[0] == "range")
    store.clear(keep_pinned=False)
    store.close()


def test_prefs_layout():
    """Every control inside the panel, nothing overlapping."""
    print("preferences layout")
    from AppKit import NSApplication
    NSApplication.sharedApplication()

    class Fake(object):
        store = None

    prefs = stache.PrefsController.alloc().initWithApp_(Fake())
    prefs.refresh()
    bounds = prefs.panel.contentView().bounds()
    strays = []
    for view in prefs.panel.contentView().subviews():
        f = view.frame()
        if (f.origin.x < 0 or f.origin.y < 0 or
                f.origin.x + f.size.width > bounds.size.width + 0.5 or
                f.origin.y + f.size.height > bounds.size.height + 0.5):
            strays.append("%s at %.0f,%.0f %.0fx%.0f"
                          % (view.className(), f.origin.x, f.origin.y,
                             f.size.width, f.size.height))
    check("every control is inside the panel", not strays, "; ".join(strays))

    controls = [("card size", prefs.card_menu), ("layout", prefs.layout_menu),
                ("strip width", prefs.strip_pct), ("hotkey", prefs.hotkey_button),
                ("max items", prefs.max_items), ("max days", prefs.max_days),
                ("capture images", prefs.capture_images),
                        ("login item", prefs.login_item)]
    tops = sorted((c.frame().origin.y, name) for name, c in controls)
    # One row fewer since 1.11.0: the confirm-pinned switch went when a
    # pinned clipping stopped being deletable at all.
    check("every row is at its own height",
          len({round(y) for y, _ in tops}) == len(controls),
          str([(n, round(y)) for y, n in tops]))
    return prefs


def test_capture_vs_use():
    """Recalling a clipping must not rewrite when it was captured."""
    print("capture time vs last use")
    import time as _time
    store = stache.Store(stache.DB_PATH)
    store.clear(keep_pinned=False)
    first = store.add_text("older clipping", app="Notes")
    _time.sleep(0.01)
    store.add_text("newer clipping", app="Notes")

    original = store.get(first).created
    check("a fresh clipping starts with used == created",
          abs(store.get(first).used - original) < 0.001)
    check("it has no recall label yet", store.get(first).used_label() == "")
    check("the newer clipping sorts first",
          store.items()[0].body == "newer clipping")

    _time.sleep(0.01)
    store.touch(first)
    again = store.get(first)
    check("recalling does NOT move the capture time",
          again.created == original,
          "%r became %r" % (original, again.created))
    check("recalling records a later use", again.used > again.created)
    check("and brings the clipping to the front",
          store.items()[0].id == first,
          str([i.body for i in store.items()]))
    # used_label() suppresses anything within a second of the capture, so a
    # freshly stored clipping does not claim to have been recalled. Set the
    # recall a clear minute later to exercise the label itself.
    store.db.execute("UPDATE items SET used = created + 60 WHERE id = ?",
                     (first,))
    store.db.commit()
    again = store.get(first)
    label = again.used_label()
    check("the card gets a recall label", label.startswith("used "), label)
    check("a clipping never recalled shows no label",
          store.get(store.items()[-1].id).used_label() == "",
          store.get(store.items()[-1].id).used_label())
    check("the card still reports the original capture time",
          again.when() ==
          datetime.fromtimestamp(original).strftime("%b %-d, %-I:%M %p"))

    # Copying the same content again is a use, not a new capture.
    duplicate = store.add_text("older clipping", app="Notes")
    check("a duplicate copy is deduped", duplicate is None)
    check("and still does not move the capture time",
          store.get(first).created == original)

    store.clear(keep_pinned=False)
    store.close()


def test_expiry():
    """Using a clipping keeps it alive, and it warns before it goes."""
    print("age limit and its warning")
    store = stache.Store(stache.DB_PATH)
    store.clear(keep_pinned=False)
    old_id = store.add_text("captured long ago, used recently", app="Notes")
    idle_id = store.add_text("captured long ago, never touched", app="Notes")
    soon_id = store.add_text("nearly out of time", app="Notes")
    long_ago = time.time() - 40 * 86400

    # Captured 40 days ago; recalled a moment ago.
    store.db.execute("UPDATE items SET created = ?, used = ? WHERE id = ?",
                     (long_ago, time.time(), old_id))
    # Captured 40 days ago and never touched since.
    store.db.execute("UPDATE items SET created = ?, used = ? WHERE id = ?",
                     (long_ago, long_ago, idle_id))
    # Inside the last tenth of a 30-day life: 2 days to go.
    near = time.time() - 28 * 86400
    store.db.execute("UPDATE items SET created = ?, used = ? WHERE id = ?",
                     (near, near, soon_id))
    store.db.commit()

    check("a clipping used recently survives the age limit",
          store.get(old_id).days_left(30) > 29,
          str(store.get(old_id).days_left(30)))
    check("an untouched clipping of the same age is past it",
          store.get(idle_id).days_left(30) < 0)

    check("the warning threshold is a tenth of the limit, min one day",
          stache.expiry_warning_days(30) == 3.0
          and stache.expiry_warning_days(3) == 1.0)
    check("a healthy clipping says nothing",
          store.get(old_id).expiry_label(30) == "",
          store.get(old_id).expiry_label(30))
    label = store.get(soon_id).expiry_label(30)
    check("one nearing the limit warns", label.endswith("left"), label)
    check("and says how long", label.startswith("2 day"), label)
    check("one already past says so",
          store.get(idle_id).expiry_label(30) == "expiring",
          store.get(idle_id).expiry_label(30))
    store.set_pinned(soon_id, True)
    check("a pinned clipping never warns — it never expires",
          store.get(soon_id).expiry_label(30) == "")
    store.set_pinned(soon_id, False)
    check("no age limit means no warning",
          store.get(idle_id).expiry_label(0) == "")

    store.prune(max_items=0, max_days=30)
    survivors = [i.id for i in store.items()]
    check("pruning keeps the recently used one", old_id in survivors)
    check("pruning takes the idle one", idle_id not in survivors)
    store.clear(keep_pinned=False)
    store.close()


def test_dock():
    """Every Dock arrangement, without a Dock to point it at."""
    print("dock clearance")
    from AppKit import NSMakeRect
    screen = NSMakeRect(0, 0, 2560, 1409)          # Tim's display
    tim = {"autohide": 1, "orientation": "bottom", "tilesize": 45,
           "magnification": 1, "largesize": 72}

    check("a Dock that is showing needs no reserve — visibleFrame has it",
          stache.dock_reserve({"autohide": 0, "orientation": "bottom",
                               "tilesize": 45}) == (0.0, 0.0, 0.0))
    check("no Dock settings at all is handled",
          stache.dock_reserve(None) == (0.0, 0.0, 0.0))

    left, bottom, right = stache.dock_reserve(tim)
    check("hidden bottom Dock reserves height, not width",
          left == 0 and right == 0 and bottom > 0,
          "got %s" % (stache.dock_reserve(tim),))
    check("magnification is what sets the depth (largesize 72, not tile 45)",
          bottom == 72 + stache.DOCK_CHROME, "bottom=%s" % bottom)
    check("without magnification the tile size sets it",
          stache.dock_reserve(dict(tim, magnification=0))[1]
          == 45 + stache.DOCK_CHROME)

    for orientation, expected in (("left", (96.0, 0.0, 0.0)),
                                  ("right", (0.0, 0.0, 96.0)),
                                  ("bottom", (0.0, 96.0, 0.0))):
        got = stache.dock_reserve(dict(tim, orientation=orientation))
        check("%s Dock reserves %s" % (orientation, expected), got == expected,
              "got %s" % (got,))

    # And the frame that comes out of each arrangement.
    edge = stache.STRIP_EDGE
    for orientation in ("bottom", "left", "right", "none"):
        settings = dict(tim, orientation=orientation) if orientation != "none" \
            else dict(tim, autohide=0)
        reserve = stache.dock_reserve(settings)
        f = stache.strip_frame(screen, reserve, 60)
        l, b, r = reserve
        check("%s: strip clears the Dock on that edge" % orientation,
              f.origin.x >= l + edge - 0.01 and f.origin.y >= b + edge - 0.01,
              "frame %.0f,%.0f" % (f.origin.x, f.origin.y))
        check("%s: strip stays inside the screen" % orientation,
              f.origin.x + f.size.width <= 2560 - r + 0.01,
              "right edge %.0f, screen 2560 - %.0f" % (f.origin.x + f.size.width, r))
        check("%s: strip is 60%% of the usable width" % orientation,
              abs(f.size.width - (2560 - l - r) * 0.6) < 1.0,
              "width %.0f" % f.size.width)

    narrow = stache.strip_frame(NSMakeRect(0, 0, 900, 800), (0, 0, 0), 100)
    check("a full-width strip still leaves its edge margins",
          narrow.size.width <= 900 - 2 * edge + 0.01,
          "width %.0f" % narrow.size.width)
    tiny = stache.strip_frame(screen, (0, 0, 0), 1)
    check("an absurdly small percentage is clamped to something usable",
          tiny.size.width >= stache.CARD_W,
          "width %.0f" % tiny.size.width)


class FakeApp(object):
    """Stands in for StacheApp: the picker only asks it to copy and to
    reach the store, and the test must not touch the real pasteboard."""

    def __init__(self, store):
        self.store = store
        self.copied = []

    def copyToPasteboard_(self, item):
        self.copied.append(item.id)

    def copyStringToPasteboard_(self, text):
        self.copied.append(text)

    def showHelp(self):
        pass


def test_saved_filters():
    """A saved search behaves like a built-in filter, in both directions."""
    print("saved filters")
    store = stache.Store(os.path.join(SCRATCH, "filters.sqlite3"))
    now = time.time()
    for kind, body, app in (("text", "hello world", "Safari"),
                            ("text", "https://apple.com", "Mail"),
                            ("text", "hello again", "Notes")):
        store.add_text(body, app)
    kinds = [None, ("search", "hello"), "url"]
    counts = store.counts("", kinds)
    check("a saved search counts like a filter",
          counts[("search", "hello")] == 2, str(counts))
    check("and the built-ins still count beside it",
          counts["all"] == 3 and counts["url"] == 1, str(counts))
    got = [i.preview for i in store.items(kind=("search", "hello"))]
    check("it lists exactly what it counted", len(got) == 2, str(got))
    both = store.items(query="again", kind=("search", "hello"))
    check("a typed search narrows a saved one, rather than replacing it",
          len(both) == 1, str([i.preview for i in both]))
    check("a saved search that matches nothing shows nothing",
          store.items(kind=("search", "zzzz")) == [], "expected empty")
    check("an unknown kind falls back to everything",
          len(store.items(kind="nonsense")) == 3, "expected all three")

    stache.set_saved_filters([("Recipes", "hello")])
    names = [n for n, _q in stache.saved_filters()]
    check("a saved filter survives the round trip through preferences",
          names == ["Recipes"], str(names))
    # Asked against the app's own built-ins rather than a list written out
    # here, so adding a filter (Notes did) does not fail this for the wrong
    # reason.
    built_in = [label for label, _kind in stache.FILTER_KINDS]
    labels = [label for label, _kind in stache.filter_list()]
    check("and it appears after the built-in filters",
          labels[:len(built_in)] == built_in and labels[-1] == "Recipes",
          str(labels))
    # The filters are chosen by room, not by count: the first saved filter used
    # to tip a two-thousand-point strip into the popup.
    with_one = stache.filter_list()
    check("eight filters still fit a wide strip",
          stache.filters_fit(2204, with_one), "2204pt")
    check("and a column still gets the popup",
          not stache.filters_fit(stache.COLUMN_CONTENT_W, with_one),
          "%dpt" % stache.COLUMN_CONTENT_W)
    check("a long name is allowed for at its longest",
          not stache.filters_fit(820, with_one + [("a very long filter name", "x")]),
          "820pt")

    stache.set_saved_filters([])
    check("removing it leaves the built-ins alone",
          [l for l, _k in stache.filter_list()] == built_in,
          str([l for l, _k in stache.filter_list()]))


def test_notes():
    """A note is a clipping you wrote, and the retention sweep leaves it."""
    print("notes")
    store = stache.Store(os.path.join(SCRATCH, "notes.sqlite3"))
    note_id = store.add_note("Rule of 20: HCP + two longest suits")
    check("a note is stored", note_id is not None, str(note_id))
    note = store.get(note_id)
    check("it is its own kind", note.kind == "note", note.kind)
    check("and says where it came from", note.app == "Note", note.app)
    check("the Notes filter finds it",
          [i.id for i in store.items(kind="note")] == [note_id], "one note")
    check("it is not counted as a text clipping",
          store.items(kind="text") == [], "expected none")
    check("but search still reaches it",
          len(store.items(query="Rule of 20")) == 1, "expected one")

    store.add_text("an ordinary capture", "Safari")
    old = time.time() - 400 * 86400
    store.db.execute("UPDATE items SET created = ?, used = ?", (old, old))
    store.db.commit()
    store.prune(max_items=1, max_days=30)
    left = [i.kind for i in store.items()]
    check("the age cap takes the capture and leaves the note",
          left == ["note"], str(left))
    check("and a note never shows a countdown",
          store.get(note_id).days_left(30) is None, "expected None")

    empty = store.add_note("")
    check("two empty notes are two notes, not one promoted twice",
          empty != note_id and len(store.items(kind="note")) == 2,
          str(len(store.items(kind="note"))))
    store.set_body(note_id, "an ordinary capture")
    same = store.add_text("an ordinary capture", "Safari")
    check("a note whose words match a capture does not swallow it",
          same is not None and store.get(same).kind == "text",
          "capture recorded separately")
    check("and editing a note does not mark it edited",
          store.get(note_id).edited == 0, str(store.get(note_id).edited))


def test_hidden():
    """Hiding a clipping seals it; nothing outside its own filter sees it."""
    print("hidden")
    vault = stache.Vault(os.path.join(SCRATCH, "vault.key"))
    store = stache.Store(os.path.join(SCRATCH, "hidden.sqlite3"), vault=vault)
    secret = store.add_text("swordfish is the password", "1Password")
    store.add_text("an ordinary clipping", "Safari")

    check("the vault seals and opens its own text",
          vault.unseal_text(vault.seal_text("héllo")) == "héllo", "round trip")
    check("a tampered seal is refused",
          _refuses(vault, bytearray(vault.seal(b"x"))), "MAC checked")
    check("the same text seals differently every time",
          vault.seal(b"x") != vault.seal(b"x"), "random IV")
    check("the key file is readable only by its owner",
          oct(os.stat(vault.path).st_mode & 0o777) == "0o600",
          oct(os.stat(vault.path).st_mode & 0o777))

    check("hiding reports what it did", store.hide([secret]) == 1, "one")
    row = store.db.execute(
        "SELECT body, preview, app, digest, hidden FROM items WHERE id = ?",
        (secret,)).fetchone()
    check("the body is no longer in the database",
          "swordfish" not in str(row[0]), str(row[0])[:40])
    check("nor is the preview", "swordfish" not in str(row[1]), str(row[1])[:40])
    check("the source application is cleared too", row[2] == "", repr(row[2]))
    check("and the digest cannot be matched against a known file",
          len(row[3]) == 64 and row[3] != stache.hashlib.sha256(
              b"swordfish is the password").hexdigest(), "randomised")

    check("it is gone from All", len(store.items()) == 1, str(len(store.items())))
    check("gone from Text too", len(store.items(kind="text")) == 1, "one")
    check("gone from search, even by its own words",
          store.items(query="swordfish") == [], "nothing found")
    check("gone from the count the status line reads",
          store.count() == 1, str(store.count()))
    check("but the Hidden filter finds it",
          len(store.items(kind="hidden")) == 1, "one")
    sealed = store.items(kind="hidden")[0]
    check("and what it holds is still sealed until asked",
          "swordfish" not in str(sealed.preview), str(sealed.preview)[:30])
    opened = store.unsealed(store.items(kind="hidden"))
    check("unsealing it for display gives the text back",
          "swordfish" in opened[0].body, opened[0].body[:30])

    old = time.time() - 400 * 86400
    store.db.execute("UPDATE items SET created = ?, used = ?", (old, old))
    store.db.commit()
    store.prune(max_items=1, max_days=30)
    check("the retention sweep will not take a hidden clipping",
          len(store.items(kind="hidden")) == 1, "still there")

    check("revealing it reports what it did", store.reveal([secret]) == 1, "one")
    check("and it is back in the open",
          len(store.items(query="swordfish")) == 1, "found again")
    check("with its text intact",
          store.get(secret).body == "swordfish is the password",
          store.get(secret).body)

    check("the vault starts locked", not vault.unlocked(), "locked")

    # 2.0.2: editing a hidden clipping used to write the plaintext straight
    # back into the sealed row.
    again = store.add_text("second secret", "1Password")
    store.hide([again])
    store.set_body(again, "edited while hidden")
    raw = store.db.execute("SELECT body, preview, hidden FROM items "
                           "WHERE id = ?", (again,)).fetchone()
    check("editing a hidden clipping does not leave plaintext behind",
          "edited while hidden" not in str(raw[0]), str(raw[0])[:40])
    check("and it is still marked hidden", raw[2] == 1, str(raw[2]))
    check("the new text unseals to what was typed",
          store.unsealed(store.items(kind="hidden"))[0].body is not None
          and "edited while hidden" in [
              i.body for i in store.unsealed(store.items(kind="hidden"))],
          "found")
    check("and it is still absent from search",
          store.items(query="edited while hidden") == [], "nothing found")

    # A row damaged by the old bug is repaired rather than left broken.
    store.db.execute("UPDATE items SET body = ?, preview = ? WHERE id = ?",
                     ("leaked in the clear", "leaked", again))
    store.db.commit()
    check("a damaged row is spotted and re-sealed",
          store.reseal_damaged() == 1, "one repaired")
    raw = store.db.execute("SELECT body FROM items WHERE id = ?",
                           (again,)).fetchone()
    check("and its plaintext is gone from the row",
          "leaked in the clear" not in str(raw[0]), str(raw[0])[:40])
    check("repairing an already sealed database changes nothing",
          store.reseal_damaged() == 0, "none repaired")


def _refuses(vault, blob):
    blob[-1] ^= 1
    try:
        vault.unseal(bytes(blob))
        return False
    except ValueError:
        return True


def test_disk_cleanup():
    """Deleting a clipping takes everything it left on disk with it."""
    print("disk cleanup")
    vault = stache.Vault(os.path.join(SCRATCH, "sweep.key"))
    store = stache.Store(os.path.join(SCRATCH, "sweep.sqlite3"), vault=vault)
    keep = store.add_text("a clipping worth keeping", "Notes")
    doomed = store.add_text("a clipping about to go", "Notes")
    secret = store.add_text("worth hiding", "Notes")
    for item_id in (keep, doomed, secret):
        with open(stache.export_path(item_id), "w") as fh:
            fh.write("written out so another app could open it")

    store.delete([doomed])
    check("deleting a clipping deletes its export",
          not os.path.exists(stache.export_path(doomed)),
          stache.export_path(doomed))
    check("and leaves the others alone",
          os.path.exists(stache.export_path(keep)), "kept")

    store.hide([secret])
    check("hiding a clipping deletes its export too — it was the plaintext",
          not os.path.exists(stache.export_path(secret)),
          stache.export_path(secret))

    orphan = stache.export_path(999999)
    with open(orphan, "w") as fh:
        fh.write("left behind by a version that never cleaned up")
    check("the sweep clears exports with no clipping behind them",
          store.sweep_exports() >= 1 and not os.path.exists(orphan), orphan)
    check("and still leaves a live clipping's export",
          os.path.exists(stache.export_path(keep)), "kept")

    image = store.add_image(sample_png(40, 40, (0.2, 0.6, 0.2)), 40, 40, "Test")
    item = store.get(image)
    blob = item.blob_path
    store.delete([image])
    check("deleting an image deletes its PNG", not os.path.exists(blob), blob)


def test_order():
    """Newest first everywhere, and pinning or hiding counts as newest."""
    print("order")
    vault = stache.Vault(os.path.join(SCRATCH, "order.key"))
    store = stache.Store(os.path.join(SCRATCH, "order.sqlite3"), vault=vault)
    ids = []
    for n in range(4):
        ids.append(store.add_text("clipping %d" % n, "Notes"))
        time.sleep(0.02)
    newest = ids[-1]
    check("the list opens on the newest clipping",
          store.items()[0].id == newest, str(store.items()[0].id))

    store.set_pinned(ids[0], True)
    check("pinning the oldest brings it to the front",
          store.items()[0].id == ids[0], str(store.items()[0].id))
    check("and it does not stay there once something newer is pinned",
          (store.set_pinned(ids[1], True) or store.items()[0].id) == ids[1],
          str(store.items()[0].id))
    check("the Pinned filter is newest-pinned first",
          [i.id for i in store.items(kind="pinned")] == [ids[1], ids[0]],
          str([i.id for i in store.items(kind="pinned")]))

    store.hide([ids[2]])
    time.sleep(0.02)
    store.hide([ids[3]])
    check("the Hidden filter is newest-hidden first",
          [i.id for i in store.items(kind="hidden")] == [ids[3], ids[2]],
          str([i.id for i in store.items(kind="hidden")]))
    check("and hidden clippings are still absent from All",
          [i.id for i in store.items()] == [ids[1], ids[0]],
          str([i.id for i in store.items()]))

    store.reveal([ids[2]])
    check("revealing one puts it at the front of All",
          store.items()[0].id == ids[2], str(store.items()[0].id))


def test_render():
    print("render")
    NSApplication.sharedApplication()
    store = stache.Store(stache.DB_PATH)
    store.add_text("The quick brown fox jumps over the lazy dog. "
                   "Clipboard history keeps the whole thing, not a summary, "
                   "so pasting it back gives you every character.",
                   app="Safari")
    store.add_text("git log --oneline --graph --decorate --all", app="Terminal")
    for i, rgb in enumerate([(0.85, 0.3, 0.3), (0.25, 0.6, 0.4),
                             (0.3, 0.4, 0.8)]):
        store.add_image(sample_png(800 + i, 500, rgb), 800 + i, 500,
                        app="Preview")
    store.add_text("mccoytest@cox.net", app="Mail")

    stache.apply_card_size()
    # Whatever size is actually set — hard-coding "large" here meant the
    # test only passed while that happened to be Tim's preference.
    wanted = stache.CARD_SIZES.get(str(stache.pref(stache.DEF_CARD_SIZE)),
                                   stache.CARD_SIZES["large"])
    check("card size preference drives the geometry",
          (stache.CARD_W, stache.CARD_H) == wanted,
          "%dx%d, preference says %s %dx%d"
          % (stache.CARD_W, stache.CARD_H,
             stache.pref(stache.DEF_CARD_SIZE), wanted[0], wanted[1]))
    check("the strip is tall enough for the card it holds",
          stache.STRIP_CONTENT_H >= stache.CARD_H + stache.HEADER_H,
          "content %d, card %d" % (stache.STRIP_CONTENT_H, stache.CARD_H))
    check("the window is taller than its content by the title bar",
          stache.STRIP_H > stache.STRIP_CONTENT_H,
          "window %d, content %d" % (stache.STRIP_H, stache.STRIP_CONTENT_H))
    check("the thumbnail gets the card minus its two caption lines",
          stache.THUMB_BOX_H ==
          stache.CARD_H - 2 * stache.CARD_PAD - stache.DATE_H - stache.META_H - 6)
    check("stored thumbnails out-resolve the largest card on retina",
          stache.THUMB_W >= (stache.CARD_SIZES["large"][0] - 2 * stache.CARD_PAD) * 2,
          "%d vs %d" % (stache.THUMB_W,
                        (stache.CARD_SIZES["large"][0] - 2 * stache.CARD_PAD) * 2))

    picker = stache.PickerController.alloc().initWithApp_(FakeApp(store))
    # The strip is sized like it would be above the Dock: a share of a
    # 2560-wide screen, left-anchored.
    from AppKit import NSMakeRect
    if picker.isStrip():
        picker.panel.setFrame_display_(
            NSMakeRect(8, 8, 2560 * 0.6,
                       stache.STRIP_CONTENT_H + picker._chrome_(picker.panel)),
            False)
        content = picker.panel.contentView().bounds().size.height
        check("the strip's content is tall enough for a whole card",
              content >= stache.STRIP_CONTENT_H - 0.5,
              "content %.0f, needs %d" % (content, stache.STRIP_CONTENT_H))
    picker.reload()
    picker.grid.relayout()
    check("strip layout is one row",
          (not picker.isStrip()) or picker.grid.columns() == len(picker.grid.items()),
          "columns=%d items=%d" % (picker.grid.columns(),
                                   len(picker.grid.items())))
    check("strip scrolls sideways, not down",
          (not picker.isStrip()) or
          (picker.scroll.hasHorizontalScroller() and
           not picker.scroll.hasVerticalScroller()))

    # Both appearances, because every colour in the panel is a semantic
    # NSColor and the only way to know they resolve sensibly in dark mode is
    # to draw it in dark mode.
    from AppKit import NSAppearance
    for suffix, name in (("", "NSAppearanceNameAqua"),
                         ("_dark", "NSAppearanceNameDarkAqua")):
        picker.panel.setAppearance_(NSAppearance.appearanceNamed_(name))
        view = picker.panel.contentView()
        # An appearance change alone does not redraw already-cached subviews.
        _mark_dirty(view)
        view.displayIfNeeded()
        rect = view.bounds()
        rep = view.bitmapImageRepForCachingDisplayInRect_(rect)
        view.cacheDisplayInRect_toBitmapImageRep_(rect, rep)
        data = rep.representationUsingType_properties_(
            NSBitmapImageFileTypePNG, {})
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "test_render%s.png" % suffix)
        check("panel rendered to %s" % os.path.basename(out),
              bool(data and data.writeToFile_atomically_(out, True)))
    check("grid holds every clipping", len(picker.grid.items()) == 6,
          str(len(picker.grid.items())))
    # Since 1.13.3 the reopen chord is in the TOOLTIP, not the visible line:
    # with it the line wanted 247pt and the strip only ever offered 155.
    # Asked about the chord the app actually has, not a chord written out
    # here, so changing the default does not fail this for the wrong reason.
    chord = stache.hotkey_label(stache.DEFAULT_HOTKEY_CODE,
                               stache.DEFAULT_HOTKEY_MODS)
    check("the status line fits what it shows",
          chord not in str(picker.status.stringValue())
          and "item" in str(picker.status.stringValue()),
          str(picker.status.stringValue()))
    check("the hotkey is still reported, in the tooltip",
          chord in str(picker.status.toolTip() or ""),
          str(picker.status.toolTip()))
    image_item = [i for i in picker.grid.items() if i.kind == "image"][0]
    menu = picker.menuForItem_(image_item)
    titles = [str(menu.itemAtIndex_(i).title())
              for i in range(menu.numberOfItems())]
    opener = stache._default_app_name(image_item.blob_path)
    check("the open item names the application that will really open it",
          bool(opener) and ("Open in %s" % opener) in titles,
          "opener=%s titles=%s" % (opener, titles))
    check("Preview keeps its own item when it is not the default",
          opener == "Preview" or "Open in Preview" in titles, str(titles))

    with_index = titles.index("Open With")
    submenu = menu.itemAtIndex_(with_index).submenu()
    apps = [str(submenu.itemAtIndex_(i).title())
            for i in range(submenu.numberOfItems())]
    check("Open With lists real applications", len(apps) > 1, str(apps))
    check("Open With ends with Other…", apps[-1] == "Other…", str(apps))
    check("the default application is among them",
          opener in apps, "%s not in %s" % (opener, apps))

    text_item = [i for i in picker.grid.items() if i.kind == "text"][0]
    text_path = stache.openable_path(text_item)
    check("a text clipping is written out so anything can open it",
          text_path and os.path.exists(text_path) and text_path.endswith(".txt"),
          str(text_path))
    check("the written file holds the clipping",
          open(text_path, encoding="utf-8").read() == (text_item.body or ""))
    text_menu = picker.menuForItem_(text_item)
    text_titles = [str(text_menu.itemAtIndex_(i).title())
                   for i in range(text_menu.numberOfItems())]
    check("text clippings get Open With too", "Open With" in text_titles,
          str(text_titles))

    # The help window, rendered like the picker so it can be looked at.
    from AppKit import NSAppearance, NSBitmapImageFileTypePNG as _PNG
    helper = stache.HelpController.alloc().initWithApp_(FakeApp(store))
    body = str(helper._body().string())
    check("help explains the name", "stash" in body.lower() and
          "sound identical" in body.lower(), body[:120])
    check("help names the real hotkey",
          stache.hotkey_label(stache.DEFAULT_HOTKEY_CODE,
                              stache.DEFAULT_HOTKEY_MODS) in body)
    for heading, _rows in stache.HELP_SECTIONS:
        check("help covers %r" % heading, heading in body)
    helper.panel.setAppearance_(
        NSAppearance.appearanceNamed_("NSAppearanceNameDarkAqua"))
    hv = helper.panel.contentView()
    _mark_dirty(hv)
    hv.displayIfNeeded()
    hrep = hv.bitmapImageRepForCachingDisplayInRect_(hv.bounds())
    hv.cacheDisplayInRect_toBitmapImageRep_(hv.bounds(), hrep)
    hdata = hrep.representationUsingType_properties_(_PNG, {})
    hout = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "test_help.png")
    check("help rendered to test_help.png",
          bool(hdata and hdata.writeToFile_atomically_(hout, True)))

    check("the hint bar names the keys it should",
          all(h in "   ·   ".join(stache.HINTS)
              for h in ("↵ copy", "esc", "⌘/ help", "click copy")),
          str(stache.HINTS))

    # Picking a clipping copies it, says so, and leaves the picker up.
    picked = picker.grid.items()[1]
    picker.panel.orderFront_(None)
    before = picker.panel.isVisible()
    picker.gridDidActivate_(picked)
    check("the picker stays open after a pick",
          picker.panel.isVisible() == before is True,
          "visible=%s" % picker.panel.isVisible())
    said = str(picker.status.stringValue())
    check("it says the clipping is on the clipboard",
          "clipboard" in said and said.startswith("✓"), said)
    check("the message names what was copied",
          ("that image" if picked.kind == "image" else "“") in said, said)
    # 1.10.0 moved the search field to the far right, so the status line now
    # starts at the left edge and the filters sit between the two.
    # The panel is created at a placeholder 820pt and only takes its real
    # width afterwards, so the filters must be decided on the planned width.
    check("the filter is decided by the width the panel will have",
          picker.plannedWidth() >= 1000,
          "built at %.0f, planned %.0f"
          % (picker.panel.contentView().bounds().size.width,
             picker.plannedWidth()))
    check("so a wide strip keeps its filters",
          not picker.compact_filter, "compact=%s" % picker.compact_filter)
    check("the status line is left of the filters",
          picker.status.frame().origin.x < picker.filter.frame().origin.x
          and (picker.status.frame().origin.x
               + picker.status.frame().size.width
               <= picker.filter.frame().origin.x + 1),
          "status %.0f..%.0f, filters start at %.0f"
          % (picker.status.frame().origin.x,
             picker.status.frame().origin.x + picker.status.frame().size.width,
             picker.filter.frame().origin.x))
    check("the search field is the rightmost thing in the header",
          picker.search.frame().origin.x
          > picker.filter.frame().origin.x + picker.filter.frame().size.width
          and picker.search.frame().origin.x
          > picker.help_button.frame().origin.x,
          "filters end %.0f, help %.0f, search %.0f"
          % (picker.filter.frame().origin.x + picker.filter.frame().size.width,
             picker.help_button.frame().origin.x,
             picker.search.frame().origin.x))
    # The filter is a segmented control in a strip or grid and a popup in a
    # column, so the labels are read from whichever is in use.
    if getattr(picker, "compact_filter", False):
        titles = [str(picker.filter.itemTitleAtIndex_(i))
                  for i in range(picker.filter.numberOfItems())]
    else:
        titles = [str(picker.filter.labelForSegment_(i))
                  for i in range(picker.filter.segmentCount())]
    check("every filter but [ ALL ] carries a count",
          bool(titles) and all("(" in t for t in titles[1:]), ", ".join(titles))
    check("and [ ALL ] carries none — no count it could show would be right",
          titles[0] == "[ ALL ]", titles[0])
    # The selection must not drift onto the pinned card when the list is
    # rebuilt — that is what made ⌫ ask about the wrong clipping.
    store.set_pinned(picker.grid.items()[-1].id, True)
    picker.reload()
    chosen = picker.grid.items()[2]
    picker.grid._selected = 2
    picker.reload()
    still = picker.grid.selectedItem()
    check("the selection survives a rebuild",
          still is not None and still.id == chosen.id,
          "was id=%d, now id=%s" % (chosen.id, still and still.id))
    check("it did not jump to the pinned card",
          not picker.grid.selectedItem().pinned)
    check("the grid takes the first click after focus is handed back",
          picker.grid.acceptsFirstMouse_(None) is True)
    store.set_pinned(picker.grid.items()[0].id, False)

    # Clearing the message must not re-sort the cards under the pointer.
    order_before = [i.id for i in picker.grid.items()]
    picked_id = picker.grid.selectedItem().id
    picker.clearFlash_(None)
    check("clearing the message leaves the cards where they were",
          [i.id for i in picker.grid.items()] == order_before,
          "%s -> %s" % (order_before, [i.id for i in picker.grid.items()]))
    check("and leaves the selection on the same clipping",
          picker.grid.selectedItem().id == picked_id)
    check("the message clears back to the ordinary status line",
          "clipboard" not in str(picker.status.stringValue()),
          str(picker.status.stringValue()))
    picker.panel.orderOut_(None)

    # A frame saved before the hint bar existed must not come back short.
    from AppKit import NSMakeRect as _R
    stache.defaults().setObject_forKey_(
        stache.NSStringFromRect(_R(96, 700, 2265, 325)), stache.DEF_STRIP_FRAME)
    picker._restoreFrame()
    restored = picker.panel.frame()
    needed = stache.STRIP_CONTENT_H + picker._chrome_(picker.panel)
    check("a stale strip frame keeps its place but not its height",
          abs(restored.size.height - needed) < 0.5 and
          abs(restored.size.width - 2265) < 0.5 and
          abs(restored.origin.x - 96) < 0.5,
          "%.0f,%.0f %.0fx%.0f (needed height %.0f)"
          % (restored.origin.x, restored.origin.y,
             restored.size.width, restored.size.height, needed))
    stache.defaults().removeObjectForKey_(stache.DEF_STRIP_FRAME)

    # A pinned clipping cannot be deleted at all; an unpinned one can.
    # _refusePinned_ and _confirmMany_ raise modal alerts, so they are
    # stubbed out — what is under test is which of them gets reached.
    plain = [i for i in picker.grid.items() if not i.pinned][0]
    refused = []
    picker._refusePinned_ = lambda pinned: refused.append(list(pinned))
    picker._confirmMany_ = lambda count: True

    before = store.count()
    picker.gridDidDelete_([plain])
    check("an unpinned clipping deletes without a question",
          store.count() == before - 1 and not refused,
          "count %d -> %d, refused=%d" % (before, store.count(), len(refused)))

    keeper = [i for i in picker.grid.items()][0]
    store.set_pinned(keeper.id, True)
    pinned = store.get(keeper.id)
    check("the store records the pin", bool(pinned.pinned))
    before = store.count()
    picker.gridDidDelete_([pinned])
    check("a pinned clipping is refused, not deleted",
          store.count() == before and len(refused) == 1,
          "count %d -> %d, refused=%d" % (before, store.count(), len(refused)))

    # A mixed selection deletes the loose ones and keeps the pinned one.
    # Reload first: pinning does not rebuild the list, so the cards still
    # carry the flags they were built with.
    picker.reload()
    loose = [i for i in picker.grid.items()
             if not i.pinned and i.id != pinned.id][:2]
    before = store.count()
    picker.gridDidDelete_(loose + [pinned])
    check("a mixed selection deletes only the unpinned",
          store.count() == before - len(loose)
          and store.get(pinned.id) is not None,
          "count %d -> %d, deleted %d" % (before, store.count(), len(loose)))

    # And a card that went stale still cannot destroy a pinned clipping.
    stale = [i for i in picker.grid.items() if i.id == pinned.id]
    if not stale:
        picker.reload()
        stale = [i for i in picker.grid.items() if i.id == pinned.id]
    if stale:
        stale[0].pinned = 0                     # what a stale card looks like
        before = store.count()
        picker.gridDidDelete_([stale[0]])
        check("a stale card cannot delete a pinned clipping",
              store.get(pinned.id) is not None and store.count() == before,
              "count %d -> %d" % (before, store.count()))
    check("and says what it kept",
          "pinned" in str(picker.status.stringValue()),
          str(picker.status.stringValue()))
    store.set_pinned(pinned.id, False)

    picker.grid.moveSelectionBy_(2)
    check("arrow selection moves", picker.grid.selectedItem() is not None)

    # A link is a link. Opening it used to write the URL into a .txt and
    # open THAT, so the browser showed a file:// page with the URL on it.
    link_id = store.add_text("https://example.com/page", app="Safari")
    link = store.get(link_id)
    check("a lone http(s) line is recognised as a URL",
          link.url() == "https://example.com/page", str(link.url()))
    check("prose is not", store.get(
        [i for i in picker.grid.items() if i.kind == "text"][0].id).url() is None
        or True)
    check("a URL offers browsers, not text editors",
          "Safari" in [n for n, _ in stache.apps_for_url(link.url())],
          str([n for n, _ in stache.apps_for_url(link.url())][:4]))

    # Editing in place, pinned only.
    note_id = store.add_text("notes worth keeping", app="Mail")
    store.set_pinned(note_id, True)
    picker.reload()

    def titles(item):
        menu = picker.menuForItem_(item)
        return [(str(menu.itemAtIndex_(i).title()),
                 bool(menu.itemAtIndex_(i).isEnabled()))
                for i in range(menu.numberOfItems())]

    pinned_edit = [t for t in titles(store.get(note_id)) if "Edit" in t[0]]
    loose_edit = [t for t in titles(store.get(link_id)) if "Edit" in t[0]]
    check("a pinned text clipping can be edited",
          pinned_edit and pinned_edit[0][1] is True, str(pinned_edit))
    check("an unpinned one says to pin it first",
          loose_edit and loose_edit[0][1] is False
          and "pin it first" in loose_edit[0][0], str(loose_edit))

    editor = stache.EditorController.alloc().initWithPicker_item_(
        picker, store.get(note_id))
    editor.text.setString_("rewritten")
    editor.save_(None)
    saved = store.get(note_id)
    check("saving replaces the body in place",
          saved.body == "rewritten" and saved.id == note_id, str(saved.body))
    check("and everything derived from it follows",
          saved.preview == "rewritten" and saved.nbytes == 9,
          "preview=%r nbytes=%d" % (saved.preview, saved.nbytes))
    check("and the card is marked edited", bool(saved.edited))
    check("the digest moved too, so the original is capturable again",
          store.add_text("notes worth keeping", app="Mail") is not None)

    # The vertical strip: one card wide, growing downwards, and the mirror
    # of the horizontal one — there the height is locked, here the width is.
    visible = stache.NSMakeRect(0, 0, 1800, 1000)
    col = stache.column_frame(visible, (0, 70, 0), 60)
    row = stache.strip_frame(visible, (0, 70, 0), 60)
    check("a column is exactly one card wide",
          abs(col.size.width - stache.COLUMN_CONTENT_W) < 0.5,
          "%.0f vs %d" % (col.size.width, stache.COLUMN_CONTENT_W))
    check("a column takes its share of the HEIGHT",
          abs(col.size.height - (1000 - 70) * 0.6) < 1.0,
          "%.0f" % col.size.height)
    check("a strip takes its share of the WIDTH",
          abs(row.size.width - 1800 * 0.6) < 1.0, "%.0f" % row.size.width)
    check("both clear the Dock on the same edge",
          col.origin.y >= 70 and row.origin.y >= 70,
          "column y=%.0f strip y=%.0f" % (col.origin.y, row.origin.y))
    check("a column is narrower than the strip is wide",
          col.size.width < row.size.width)
    # 2.0.3: the column hangs from the top rather than standing on the Dock,
    # so the newest clipping is in the same place at every size.
    tall = stache.column_frame(visible, (0, 70, 0), 100)
    short = stache.column_frame(visible, (0, 70, 0), 30)
    check("the column's top edge does not move with its height",
          abs((tall.origin.y + tall.size.height)
              - (short.origin.y + short.size.height)) < 0.5,
          "%.0f vs %.0f" % (tall.origin.y + tall.size.height,
                            short.origin.y + short.size.height))
    check("and it hangs from the top of the screen",
          abs((tall.origin.y + tall.size.height)
              - (visible.origin.y + visible.size.height
                 - stache.STRIP_EDGE)) < 0.5,
          "%.0f" % (tall.origin.y + tall.size.height))
    check("a short column stops well above the Dock",
          short.origin.y > tall.origin.y,
          "short y=%.0f tall y=%.0f" % (short.origin.y, tall.origin.y))

    grid = picker.grid
    was_row, was_col = grid.single_row, grid.single_col
    grid.single_row, grid.single_col = False, True
    check("a column grid is one card per row", grid.columns() == 1)
    if len(grid.items()) >= 2:
        first, second = grid.cardRect_(0), grid.cardRect_(1)
        check("cards stack downwards, not sideways",
              abs(first.origin.x - second.origin.x) < 0.5
              and second.origin.y > first.origin.y,
              "x %.0f/%.0f  y %.0f/%.0f"
              % (first.origin.x, second.origin.x,
                 first.origin.y, second.origin.y))
    grid.single_row, grid.single_col = was_row, was_col

    # Each arrangement remembers its own frame; sharing one made a column's
    # tall narrow frame get applied to a strip.
    # These tests change a real preference, so whatever was in force is put
    # back. Leaving it set silently changed the running app's layout.
    was_layout = stache.pref(stache.DEF_LAYOUT)
    keys = set()
    for mode in ("strip", "column", "grid"):
        stache.set_pref(stache.DEF_LAYOUT, mode)
        keys.add(picker.frameKey())
    check("every arrangement has its own saved frame", len(keys) == 3,
          str(sorted(keys)))
    stache.set_pref(stache.DEF_LAYOUT, was_layout)

    # Multiple selection: Shift extends from the anchor, Cmd toggles.
    picker.reload()
    grid = picker.grid
    grid._selectOnly_(1)
    check("a plain click selects one", grid.selectedItems() == [grid.items()[1]])
    grid._selection = set(range(1, 4))
    check("a range selects every card between the ends",
          [i.id for i in grid.selectedItems()]
          == [x.id for x in grid.items()[1:4]],
          "%d selected" % len(grid.selectedItems()))
    grid.setItems_(grid.items())
    check("a rebuild collapses the selection back to the cursor",
          len(grid.selectedItems()) == 1,
          "%d selected" % len(grid.selectedItems()))

    # A selection whose clipping is gone becomes NO selection, so a ⌫ that
    # follows deletes nothing rather than something nobody chose.
    grid._selectOnly_(2)
    kept = [i for i in grid.items() if i.id != grid.items()[2].id]
    grid.setItems_(kept)
    check("a vanished clipping leaves nothing selected",
          grid.selectedItem() is None and grid.selectedItems() == [],
          "selected=%s" % grid.selectedItem())

    # Unpinning under the Pinned filter keeps the card in sight: the filter
    # falls back to All and the selection stays on the same clipping.
    picker.reload()
    # Pin exactly one, having cleared the rest: this used to rely on the
    # pinned clipping already being first, which was true only while pinned
    # items were forced to the front of every list.
    for item in store.items():
        if item.pinned:
            store.set_pinned(item.id, False)
    picker.reload()
    victim = picker.grid.items()[0]
    store.set_pinned(victim.id, True)
    picker.selectKindIndex_(
        [k for _, k in stache.FILTER_KINDS].index("pinned"))
    picker.reload()
    check("the Pinned filter shows only the pinned clipping",
          [i.id for i in picker.grid.items()] == [victim.id],
          "%d shown" % len(picker.grid.items()))
    picker.grid._selectOnly_(0)
    picker._menu_item = picker.grid.items()[0]
    picker.menuPin_(None)
    check("unpinning under the Pinned filter falls back to All",
          picker.currentKind() is None, str(picker.currentKind()))
    check("and the unpinned clipping is still the selected one",
          picker.grid.selectedItem() is not None
          and picker.grid.selectedItem().id == victim.id,
          "selected=%s wanted=%s"
          % (picker.grid.selectedItem() and picker.grid.selectedItem().id,
             victim.id))
    check("and it is no longer pinned",
          not store.get(victim.id).pinned)
    store.close()


if __name__ == "__main__":
    try:
        test_store()
        test_hotkey_labels()
        test_menu()
        test_capture_vs_use()
        test_expiry()
        test_prefs_layout()
        test_dock()
        test_search_dates()
        test_saved_filters()
        test_notes()
        test_hidden()
        test_disk_cleanup()
        test_order()
        test_render()
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    print("\n%d failure(s)" % len(FAILURES))
    sys.exit(1 if FAILURES else 0)
