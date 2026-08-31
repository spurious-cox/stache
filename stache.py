#!/usr/bin/env python3
"""
Stache - clipboard history for macOS
Version: 1.0.0

A background (LSUIElement) agent that watches the general pasteboard and
records everything copied to it - plain text and images alike - with the date
and time of the capture and the name of the app it was copied from.  A global
hotkey raises a floating picker: a grid of thumbnails and text cards, newest
first, searchable and filterable.  Choosing a card puts that item back on the
pasteboard, so the next Cmd-V (or `pbpaste`) hands it over.

Behaviour:
  * Capture: an NSTimer polls NSPasteboard.changeCount() several times a
    second.  There is no notification for pasteboard changes on macOS -
    polling the change count is the only route, and it is cheap because the
    count is an integer read, not a data read.
  * Images are stored as PNG files under Application Support with a PNG
    thumbnail beside them; text is stored in the database.  A SQLite index
    holds the metadata for both.
  * Password managers mark their pasteboard writes with the community
    org.nspasteboard.ConcealedType flag; those are never recorded.
  * Recall: the picker copies the chosen item and KEEPS focus, so the next
    pick or search needs no click.  Focus returns to the app that had it
    when the picker closes, so the sequence is pick, Esc, Cmd-V.
  * Retention prunes to a maximum item count and a maximum age.  Pinned
    items are exempt.

Requires no special permissions: the global hotkey is a Carbon hot key, which
the window server delivers without Accessibility, and putting data on the
pasteboard needs no grant at all.  That is why the picker copies rather than
typing Cmd-V for you - synthesising a keystroke is the one thing here that
would have demanded Accessibility.

History:
  1.17.1 Documentation caught up with Quick Look: the help still described
         Space as "open an image in Preview", the hint bar still said
         "Space preview", and neither the help nor the README listed Quick
         Look in the context menu.
  1.17.0 Quick Look previews the SELECTED clipping and nothing else.

         Handing it the whole visible list was the mistake behind both of
         the last two versions' problems. The panel asks its data source
         repeatedly, and preparing a text clipping WRITES a file, so every
         query rewrote every text file in the history — and showing the list
         meant it opened on item 0 and jumped. 1.16.2 papered over both with
         a cache and a second index assignment; neither was needed once the
         work was scoped to the one clipping being looked at, which is also
         what the Finder does. 20 queries now cost 0.0004s.

         Arrow keys still work: they go back to the grid and Quick Look
         follows the selection, rather than navigating its own copy of the
         list.
  1.16.2 Quick Look is fast, and opens on the right clipping.

         It was crawling because the data source rebuilt its file list on
         every query, and building that list WRITES a .txt for every text
         clipping — so the panel rewrote every text file on the machine
         continuously while it was open. Measured at 20 clippings: 0.526s
         for twenty rebuilds against 0.0002s cached, about three thousand
         times. The list is now built once when the panel opens and thrown
         away when it closes, and a rebuilt grid invalidates it.

         And it briefly showed the FIRST clipping on the strip before
         landing on the selected one, because the panel was ordered front
         and only then told which item to show. The index is set before as
         well as after.
  1.16.1 Quick Look no longer dismisses the picker, and comes up with the
         keyboard. Two faults with one cause: the picker hides when it loses
         key, which is what makes clicking away close it, and Quick Look
         takes key — so most of the time Stache vanished behind it. It is
         now told to hold its ground, as it already was for Preferences and
         the help, and released when Quick Look gives control back.

         The panel also had to be CLICKED before Space or Esc would close
         it. An accessory app's Quick Look panel comes up without key unless
         the app is activated first, so the activation now happens before
         the panel is ordered front.
  1.16.0 Quick Look, on any clipping, at the top of the context menu and on
         Space. It gets the whole visible list rather than one card, so the
         arrow keys walk the clippings inside it exactly as they do in the
         grid — and it follows the filter, so a Quick Look through Images
         steps only through images. Text and images alike, because
         openable_path already produces a real file for both.

         Quartz is bundled as a PACKAGE, not an include: py2app compiles an
         include into python314.zip where codesign cannot reach it, which is
         how PixProFitText shipped 18 unsigned dylibs and had the archive
         rejected. Checked after building — nothing unsignable left in the
         zip, ten Quartz extensions extracted, none unsigned.
  1.15.0 Three things a clipping could not do.

         A LINK opens as a link. Every text clipping was written to a .txt
         and that file opened, so a URL reached the browser as a file:// page
         with the address printed on it, and Open With offered Emacs and Word
         for a web page. A clipping whose whole body is one http(s) URL now
         goes to the browser, and Open With asks the system what opens URLs.

         A PINNED TEXT clipping can be edited in place. Pinned only, and the
         restriction is the point: pinning is what exempts a clipping from
         the item cap, the age cap and Clear History, so it is the only kind
         where an edit is not work the retention sweep deletes later.

         A PINNED IMAGE can be replaced from the clipboard. This is the other
         half of "Open in Pixelmator": copying the edit back is an ordinary
         pasteboard write, so it made a SECOND clipping and left the pinned
         original alone — and at card size a crop of a few pixels looks
         identical, so it appeared to have worked when it had not.

         Everything derived from the content moves with it: the preview, the
         byte count, and the DIGEST — without that last one, re-copying the
         original text would have been swallowed as a recall of the row that
         no longer holds it. Editing counts as a use, so the clipping goes to
         the front and its retention clock restarts, and the card shows
         "edited" beside the date rather than claiming to be a verbatim
         capture.
  1.14.1 Documentation made true. The README claimed chip counts follow the
         search and that the hint bar is always present, both false since
         1.13, and the in-app help had never mentioned Cmd-0 or the three
         layouts. The test suite stopped leaving DEF_LAYOUT set, which had
         been silently changing the running app's layout, and the card-size
         test stopped hard-coding "large" — it passed only while that
         happened to be the preference in force.
  1.14.0 The name and copyright are back in column layout, as ordinary text
         above the search field. The title bar could not hold them — at
         230pt the traffic lights, version, centred name and copyright
         overlapped into an unreadable pile, which is why 1.13.1 dropped
         them — but the header has a row to spare.
  1.13.3 The status line stopped being truncated — in the STRIP as well,
         where it had been since 1.10.0 moved the search field right and
         left it 155pt for 247pt of text, unnoticed because the end that
         fell off was the least interesting. The reopen chord is now a
         tooltip rather than something paid for on every view.
  1.13.2 "2 visible" fits in a column. The status field was given whatever
         was left after a fixed 132pt popup, which at the small card size —
         a 230pt column — was 40pt, so the text truncated to "2". The popup
         is now sized to its own title and the status takes the rest, and
         the phrase drops its "of N", since the All chip beside it already
         carries the total.
  1.13.1 Chip counts stop moving when you type. They answered under the
         search in force, so every number changed as the search narrowed —
         which defeats the point of a number on a chip, which is to decide
         where to look before you look. They now count what EXISTS, and how
         many the search left is reported by the status line, which says
         "2 visible of 6" rather than "2 of 6".

         And the title bar drops the version and copyright in column
         layout. At 312pt the traffic lights, version, centred name and
         copyright overlapped into an unreadable pile.
  1.13.0 The column header is two rows, so nothing is truncated. One row of
         status, five chips and a search field needs about 700pt; a column
         is around 270. The search field now spans the full width on top,
         and below it the five kinds become a single popup carrying the same
         counts, with the item count beside it and help on the right. The
         longer status line — size on disk and the reopen chord — becomes a
         tooltip there, since a truncated line says less than a short one.

         An ellipsis opening the help was the other option and would have
         cost the filters entirely in column layout.
  1.12.5 A replaced picker is retired properly rather than merely hidden.
         rebuildPicker ordered the old panel out but left the old controller
         as its delegate and the window alive, so anything still holding
         that controller could put it back on screen — which is how two
         pickers, in two different layouts, can be up at once.
  1.12.4 Opening Preferences or the help no longer dismisses the picker.
         The panel hides when it loses key, which is what makes clicking
         away dismiss it — but losing key to one of Stache's OWN windows is
         not clicking away. The obvious fix, asking NSApp.keyWindow() which
         window took over, does not work: at the moment a resign is
         delivered the replacement may not be key yet, and it reads as
         nothing at all. So the picker is TOLD to hold its ground, the same
         flag an alert already sets, and the hold is released when that
         window closes.
  1.12.3 Changing a preference no longer makes the picker disappear.
         rebuildPicker ordered the old panel out and built a replacement
         that nobody ever showed, so every change in Preferences looked like
         a crash — most convincingly in column layout, where Tim reported
         exactly that. It now comes straight back, carrying the search text
         and filter that were in force, so the change is visible as it is
         made. It is ordered FRONT rather than made key: the change came
         from the Preferences window and focus belongs there.
  1.12.2 Two faults in the new column layout. Its WIDTH is derived from the
         card size, and apply_card_size did not recompute it — so choosing a
         smaller card left a 190px card sitting in a 312px column, since the
         width kept whatever was in force at import.

         And the hint bar is gone in column layout. It is one line about
         700pt wide and a column is roughly 310, so it could only ever
         appear truncated, which is worse than absent: a legend you cannot
         read is furniture. The keys are all in the help (⌘/), and the space
         goes to the cards.
  1.12.1 The help window answers ⌘+, ⌘− and ⌘0. Its text was a fixed size,
         which is a poor joke in a window that exists to be read. The body
         is rebuilt at the new size rather than scaled as a view, so the
         monospaced key names stay crisp, and the size is remembered.
  1.12.0 A COLUMN arrangement: the strip stood on end. One card wide,
         growing downwards, parked up the left edge clear of the Dock, and
         the exact mirror of the horizontal strip — there the height is
         dictated by the card and the width is yours to drag, here the width
         is dictated and the height is yours. Arrow keys step by one in
         either, as they always did in a single row.

         Each arrangement now remembers its OWN frame. Sharing one key made
         switching a fight: a column's tall narrow frame is nonsense applied
         to a strip.

         And Cmd-0 puts the panel back where it calculated it belonged,
         forgetting where it was dragged. Remembering the position is what
         makes dragging useful and is also what makes it a trap — a strip
         dragged onto a screen that is no longer attached is remembered
         just as faithfully as one dragged somewhere sensible.
  1.11.3 The name in the title bar is not clipped. _bar_label sizes the field
         to its text, but the centre piece then switched to 13pt bold without
         re-measuring, so the frame was still the width 11pt regular needed.
  1.11.2 Delete is the default button on the batch confirmation.  Return now
         deletes; Escape still cancels.
  1.11.1 Unpinning no longer loses the card.  It re-sorts out of the front
         the instant it is unpinned, and under the Pinned chip it left the
         list entirely - at which point the selection fell back to card 0
         without saying so, and the next ⌫ deleted a clipping nobody had
         chosen.  Unpinning under that chip now switches to All, the
         selection is scrolled into view after every rebuild, and a
         selection whose clipping is gone becomes NO selection rather than
         a different one.
  1.11.0 Several cards can be selected at once - Shift-click for a range,
         Cmd-click to add or remove one - and Delete acts on all of them,
         asking once when there is more than one.  Neither modifier copies:
         building a selection is not choosing from it.  A rebuilt list
         collapses the selection back to the cursor, because after a delete
         the indices mean different clippings and carrying them over would
         put the next delete on the wrong cards.

         A pinned clipping can no longer be deleted at all.  It used to be
         deletable behind a confirmation, but a confirmation puts the
         decision in the same keystroke as the mistake; unpinning is now the
         deliberate act that makes a clipping deletable.  Deleting a mixed
         selection deletes the loose ones and says how many pinned ones it
         kept.  The "Confirm before deleting a pinned clipping" preference
         went with it - there is nothing left for it to confirm.
  1.10.0 Picking a clipping no longer hands focus back.  It used to, so that
         Cmd-V worked without a click, but the panel then went quiet under
         the cursor while still on screen and a second pick needed a click
         to wake it.  Focus stays until the picker closes, and closing still
         restores it, so the sequence is pick, Esc, Cmd-V.

         The filter is five chips carrying their own counts - All, Pinned,
         Images, Text, URL - and the search field has moved to the far
         right.  URL is derived in SQL rather than stored (a text clipping
         whose whole body is one link), so there is no schema change and
         nothing to migrate; a URL is NOT also counted as text, so the four
         kinds sum to the total.  The header now lays itself out by
         measurement: the chips are as wide as their labels, which changes
         with the counts, and fixed columns collided in the 820pt grid.

         Title bar carries the version on the left, the name and icon in
         the centre, and the copyright on the right.  The centre is a view
         dropped into the titlebar container rather than an accessory,
         because an accessory can only sit left or right and a represented
         URL would put the icon before the name instead of after it.

         Each card shows the icon of the application it came from, bottom
         right, on the line that already names it.
  1.9.0  Using a clipping keeps it alive.  The age limit now counts from the
         last recall rather than from the capture, so something reached for
         regularly never ages out, and the item-count cap keeps the most
         recently USED rather than the most recently captured.  A clipping
         inside the last tenth of its life says so in red on the card, so
         the limit never takes something away without warning.
  1.8.0  When a clipping was captured and when it was last used are two
         different facts, and recalling one used to overwrite the first with
         the second.  `created` is now written once and never touched again;
         a `used` column records the last recall, and that is what the order
         is built on — so the most recently used clipping still comes to the
         front, but the card goes on saying when it was actually captured,
         with the recall alongside it.
  1.7.2  The cards no longer shuffle under the pointer after a pick.
         Picking bumps a clipping's timestamp so it sorts to the front —
         which was invisible while the picker closed on every pick, but from
         1.7.0 the flash timer rebuilt the list four seconds later and the
         card you had just clicked slid to the front while you were looking
         at it.  Clearing the message now only restores the status line; the
         order settles the next time the picker opens.
  1.7.1  ⌫ could delete a clipping other than the one you were looking at.
         Two causes, both introduced by keeping the picker open:
           * Rebuilding the list reset the selection to the first card, and
             the first card is whatever is pinned.  Four seconds after any
             pick the flash cleared, the list rebuilt, and the selection
             silently jumped to the pinned clipping — so ⌫ asked to delete
             that instead of whatever had been clicked.  The selection now
             follows the clipping it was on, by id, across a rebuild.
           * After handing focus back, the first click on the strip only
             reactivated the app and never reached the card, leaving the
             selection where it was.  The grid accepts that first click now.
  1.7.0  Picking a clipping no longer closes the picker.  It says so instead
         — a line to the right of the search field, in the accent colour,
         naming what went on the clipboard — and hands the keyboard back to
         the app you came from so ⌘V works straight away while the strip
         stays up.  The strip closes on the hotkey, on esc, or by clicking
         away from it.
  1.6.2  Badge every alert with the icon read straight off disk.  Setting
         applicationIconImage at launch (1.6.1) was not enough — the alert
         still wore a mark that is nowhere in this bundle — so the alerts
         now set their own icon and do not depend on the application's at
         all.
  1.6.1  Set the application icon explicitly at launch.  The alert badged
         itself with somebody else's mark: every size inside Stache.icns is
         correct and LaunchServices hands out the right icon, but launchd
         starts the app by running the executable directly rather than
         through LaunchServices, and applicationIconImage does not reliably
         pick the bundle's icon up that way.  Reading the icns and setting
         it does not depend on how the process was started.
  1.6.0  Deleting a PINNED clipping now asks first.  Pinning is the way to
         say "keep this", and ⌫ sat one keystroke away from undoing that
         with no way back.  The alert carries a Don't-ask-again switch, and
         Preferences has the same switch so it can be turned back on.  The
         shell client asks too, and takes --force instead.
  1.5.1  A remembered strip keeps its place and its width, but no longer its
         height.  The strip's height is not the user's to choose — it is
         whatever one card, the header and the hint bar need — so a frame
         saved before the hint bar existed came back 22pt short and clipped
         it.  Restoring now takes the saved origin and width and recomputes
         the height, which also covers changing the card size while a frame
         from the old size is remembered.
  1.5.0  Help, in two sizes.  A hint bar runs along the bottom of the picker
         the whole time it is open, so the keys are readable without
         remembering them, and a ? in the header opens the full usage —
         including where the name comes from.
  1.4.0  Dates are searchable, and any application can open a clipping.
         Every clipping now carries a `stamp` — the same moment written
         several ways ("2026-08-28", "Aug 28", "August", "Thursday",
         "12:55 PM", "2026") — which the search matches whenever the query
         looks like a date, so "aug", "8/28" and "2026" all find things
         without polluting ordinary word searches.  "today", "yesterday",
         "this week" and "last week" are resolved to real time ranges
         instead.  The context menu grew an Open With submenu listing every
         application that can handle the clipping, plus Other… to pick one
         from anywhere, and it now covers text clippings too: they are
         written out to a .txt beside the images first.
  1.3.1  "Open in Preview" was a lie: it called NSWorkspace.openURL_, which
         opens the user's DEFAULT application for the file — Pixelmator Pro
         on Tim's Mac, not Preview.  The item is now named after the
         application that will really open it, and Preview is offered as a
         second item whenever it is not already the default, so a quick look
         does not have to wake an image editor.  The menu bar mark is the
         Old English S from the app's own icon now, rather than a stock
         moustache symbol.  Space, which is
         meant to be exactly that quick look, goes to Preview now for the
         same reason.
  1.3.0  Card size is a preference, and Large is the default: 272x220, with
         a 260x175 thumbnail against the 178x113 of 1.2.0.  Small is the old
         card for when more of the history matters more than the picture.
         Stored thumbnails went up to 560x380 to stay sharp at Large, and a
         thumbnail that is too small for the card it has to fill is quietly
         regenerated from the full-resolution PNG the first time it is drawn,
         so clippings captured before this still look right.
         Also fixes a height bug that predates the strip: STRIP_H was used
         both as the panel's CONTENT height and as its window frame height,
         so the title bar ate about 24pt off the bottom and the source line
         under each thumbnail was clipped.  The window height is now the
         content height plus the panel's own measured chrome.
  1.2.0  Card rebuilt around the picture: the date is a line above the
         thumbnail, the source and size a line below it, and the thumbnail
         takes every point left over instead of sharing the card with a
         two-line footer.  113pt tall by 178 wide, against 100 by 174.
  1.1.1  Keep clear of a hidden Dock.  visibleFrame only excludes the Dock
         while the Dock is on screen; with autohide on it runs to the very
         edge, so "just above the Dock" put the strip exactly where the Dock
         slides up over it.  The reserve is now worked out from
         com.apple.dock (orientation, autohide, tilesize, magnification,
         largesize) and applied on whichever edge the Dock lives on: a
         Dock on the left or right insets the strip sideways and leaves it on
         the bottom edge, a Dock on the bottom lifts it clear.  All four
         arrangements are covered by test_stache.py.
  1.1.0  Strip layout, and it is now the default: one horizontally scrolling
         row of clippings across the bottom of the screen, sitting just above
         the Dock, which is where Tim wants to reach for them.  The grid is
         still there under Preferences > Layout for when the whole history
         needs looking at rather than the last few.
  1.0.2  The picker was opening where nobody could see it, and then hiding
         itself.  Two independent faults, both now fixed:
           * NSPanel's hidesOnDeactivate defaults to YES, so the picker
             vanished the moment Stache was not the active app - which for
             an accessory app is most of the time, and always during the
             instant between ordering the panel front and activating.  It is
             now explicitly NO.
           * setFrameAutosaveName_ persists the window's CURRENT frame the
             moment it is called, so the frame saved at build time (the
             creation rect, 0,0) was always there to be restored and
             _centerOnActiveScreen() never ran.  The panel opened in the
             bottom-left corner under the Dock, 31pt off the bottom of the
             screen.  The frame is now saved and restored by hand, validated
             against the screens that actually exist, and centred whenever
             the saved one would not be properly visible.
         The panel is also a floating window now, and joins every Space, so
         it comes up over full-screen apps and wherever Tim happens to be.
  1.0.1  Tim's own artwork as the app icon - three moustaches on yellow
         behind a translucent S - and the menu bar mark changed to match it.
  1.0.0  First release.
"""

APP_VERSION = "1.17.1"
COPYRIGHT = "© 2026 Tim McCoy"
APP_NAME = "Stache"
BUNDLE_ID = "com.timmccoy.stache"

import ctypes
import hashlib
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

import objc
from AppKit import (
    NSAlert,
    NSOpenPanel,
    NSTextView,
    NSWorkspaceOpenConfiguration,
    NSApplication,
    NSApp,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSBitmapImageRep,
    NSBitmapImageFileTypePNG,
    NSButton,
    NSColor,
    NSCompositingOperationSourceOver,
    NSDeviceRGBColorSpace,
    NSEvent,
    NSEventModifierFlagCommand,
    NSEventModifierFlagControl,
    NSEventModifierFlagOption,
    NSEventModifierFlagShift,
    NSEventMaskKeyDown,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSGraphicsContext,
    NSImage,
    NSImageScaleProportionallyUpOrDown,
    NSImageView,
    NSLineBreakByTruncatingTail,
    NSMakeRect,
    NSMakeSize,
    NSMenu,
    NSMenuItem,
    NSMutableParagraphStyle,
    NSPanel,
    NSParagraphStyleAttributeName,
    NSPasteboard,
    NSPopUpButton,
    NSPasteboardTypePNG,
    NSPasteboardTypeString,
    NSPasteboardTypeTIFF,
    NSScreen,
    NSScrollView,
    NSSearchField,
    NSSegmentedControl,
    NSSegmentSwitchTrackingSelectOne,
    NSStatusBar,
    NSTextField,
    NSTrackingActiveInKeyWindow,
    NSTrackingArea,
    NSTrackingMouseEnteredAndExited,
    NSVariableStatusItemLength,
    NSView,
    NSViewHeightSizable,
    NSViewMaxXMargin,
    NSViewMinXMargin,
    NSLayoutAttributeLeft,
    NSLayoutAttributeRight,
    NSTitlebarAccessoryViewController,
    NSWindowCloseButton,
    NSWindowTitleHidden,
    NSViewMinYMargin,
    NSViewWidthSizable,
    NSFloatingWindowLevel,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskUtilityWindow,
    NSWorkspace,
)
from Quartz import QLPreviewPanel
from Foundation import (
    NSAttributedString,
    NSBundle,
    NSRectFromString,
    NSStringFromRect,
    NSData,
    NSDate,
    NSMakePoint,
    NSObject,
    NSRunLoop,
    NSRunLoopCommonModes,
    NSTimer,
    NSURL,
    NSUserDefaults,
    NSZeroRect,
)

# ---------------------------------------------------------------------------
# Paths and defaults
# ---------------------------------------------------------------------------

SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/Stache")
BLOB_DIR = os.path.join(SUPPORT_DIR, "blobs")
THUMB_DIR = os.path.join(SUPPORT_DIR, "thumbs")
EXPORT_DIR = os.path.join(SUPPORT_DIR, "exports")   # text written out to open
DB_PATH = os.path.join(SUPPORT_DIR, "stache.sqlite3")
AGENT_PLIST = os.path.expanduser(
    "~/Library/LaunchAgents/%s.plist" % BUNDLE_ID)

POLL_SECONDS = 0.35
RECENT_IN_MENU = 10        # clippings listed in the menu bar menu

# NSUserDefaults keys.
DEF_HOTKEY_CODE = "StacheHotKeyCode"
DEF_HOTKEY_MODS = "StacheHotKeyMods"      # Carbon modifier mask
DEF_MAX_ITEMS = "StacheMaxItems"
DEF_MAX_DAYS = "StacheMaxDays"
DEF_CAPTURE_IMAGES = "StacheCaptureImages"
DEF_PANEL_FRAME = "StachePanelFrame"      # grid layout's saved frame
DEF_STRIP_FRAME = "StacheStripFrame"      # strip layout's saved frame
DEF_LAYOUT = "StacheLayout"               # "strip", "column" or "grid"
DEF_COLUMN_FRAME = "StacheColumnFrame"    # column layout's saved frame
DEF_HELP_SCALE = "StacheHelpTextScale"    # help window text size, x1.0
DEF_STRIP_PCT = "StacheStripWidthPercent"  # strip width, % of the screen
DEF_CARD_SIZE = "StacheCardSize"          # "small", "medium" or "large"

# Control-Option-Command-Space, chosen by Tim.  49 is the Space key.
DEFAULT_HOTKEY_CODE = 49
DEFAULT_HOTKEY_MODS = 0x1000 | 0x0800 | 0x0100      # control | option | command

DEFAULTS = {
    DEF_HOTKEY_CODE: DEFAULT_HOTKEY_CODE,
    DEF_HOTKEY_MODS: DEFAULT_HOTKEY_MODS,
    DEF_MAX_ITEMS: 500,
    DEF_MAX_DAYS: 30,
    DEF_CAPTURE_IMAGES: True,
    DEF_LAYOUT: "strip",
    DEF_STRIP_PCT: 60,
    DEF_HELP_SCALE: 100,   # per cent, because prefs store ints cleanly
    DEF_CARD_SIZE: "large",
}

# Pasteboard flags that mean "do not record this".  ConcealedType is what
# 1Password, LastPass, Keychain Access and the rest mark a copied password
# with; the other two mark machine-generated and throwaway content.
PRIVATE_TYPES = (
    "org.nspasteboard.ConcealedType",
    "org.nspasteboard.TransientType",
    "org.nspasteboard.AutoGeneratedType",
)

IMAGE_TYPES = (
    NSPasteboardTypePNG,
    NSPasteboardTypeTIFF,
    "public.jpeg",
    "com.compuserve.gif",
)


def defaults():
    return NSUserDefaults.standardUserDefaults()


def pref(key):
    """Read a preference, falling back to the built-in default."""
    d = defaults()
    if d.objectForKey_(key) is None:
        return DEFAULTS[key]
    fallback = DEFAULTS[key]
    if isinstance(fallback, bool):
        return bool(d.boolForKey_(key))
    if isinstance(fallback, int):
        return int(d.integerForKey_(key))
    return d.objectForKey_(key)


def set_pref(key, value):
    defaults().setObject_forKey_(value, key)


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    kind     TEXT    NOT NULL,          -- 'text' or 'image'
    created  REAL    NOT NULL,          -- unix time of the capture
    digest   TEXT    NOT NULL,          -- sha256 of the payload, for dedupe
    preview  TEXT    NOT NULL DEFAULT '',
    body     TEXT,                      -- full text ('text'), or any string
                                        -- that came alongside an image
    blob     TEXT,                      -- PNG filename under blobs/
    thumb    TEXT,                      -- PNG filename under thumbs/
    width    INTEGER DEFAULT 0,
    height   INTEGER DEFAULT 0,
    nbytes   INTEGER DEFAULT 0,
    app      TEXT    DEFAULT '',
    pinned   INTEGER NOT NULL DEFAULT 0,
    used     REAL,                        -- last recalled; created is the
                                          -- capture and never changes
    stamp    TEXT    DEFAULT ''          -- the capture time, written several
                                         -- ways, so dates are searchable
);
CREATE INDEX IF NOT EXISTS items_created ON items (created DESC);
CREATE INDEX IF NOT EXISTS items_digest  ON items (digest);
"""


MONTHS = ("january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday")


def time_stamp(created):
    """One moment written every way somebody might type it.

    Searching a unix timestamp is hopeless, and SQLite cannot produce month
    names, so the searchable form is built once at capture and stored beside
    the clipping.
    """
    when = datetime.fromtimestamp(created)
    return " ".join((
        when.strftime("%Y-%m-%d"),          # 2026-08-28
        when.strftime("%m/%d/%Y"),          # 08/28/2026
        when.strftime("%-m/%-d"),           # 8/28
        when.strftime("%b %-d"),            # Aug 28
        when.strftime("%B"),                # August
        when.strftime("%A"),                # Thursday
        when.strftime("%-I:%M %p"),         # 12:55 PM
        when.strftime("%H:%M"),             # 12:55
    ))


def date_query(query):
    """Read a search box entry as a date.

    Returns ("range", start, end) for a relative phrase, ("stamp",) when the
    text should be matched against the stored stamp, or None when it is an
    ordinary word search.  Deciding this up front is what keeps a search for
    "may" or "march" from being treated as a date only sometimes — and keeps
    a search for "report" from matching every clipping that happens to fall
    on a Thursday.
    """
    text = " ".join(query.lower().split())
    if not text:
        return None

    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day = 86400.0
    today = midnight.timestamp()
    relative = {
        "today": (today, today + day),
        "yesterday": (today - day, today),
        "this week": (today - now.weekday() * day, today + day),
        "last week": (today - (now.weekday() + 7) * day,
                      today - now.weekday() * day),
        "this month": (midnight.replace(day=1).timestamp(), today + day),
    }
    if text in relative:
        start, end = relative[text]
        return ("range", start, end)

    if any(ch.isdigit() for ch in text):
        return ("stamp",)
    if len(text) >= 3 and any(name.startswith(text)
                              for name in MONTHS + WEEKDAYS):
        return ("stamp",)
    return None


def expiry_warning_days(max_days):
    """How long before the age limit a clipping starts saying so.

    A tenth of the limit, and never less than a day: long enough on a
    30-day limit (3 days) to do something about it, short enough on a
    3-day limit not to be red for its whole life.
    """
    return max(1.0, max_days * 0.1)


def preview_of(text):
    """The one-line summary a card draws. Shared by capture and by editing:
    two ways of deriving it would eventually disagree."""
    return " ".join((text or "").split())[:400]


class Item(object):
    """One row of the history, in a form the views can draw without SQL."""

    __slots__ = ("id", "kind", "created", "preview", "body", "blob", "thumb",
                 "width", "height", "nbytes", "app", "pinned", "used",
                 "edited")

    def __init__(self, row):
        (self.id, self.kind, self.created, self.preview, self.body,
         self.blob, self.thumb, self.width, self.height, self.nbytes,
         self.app, self.pinned, self.used, self.edited) = row

    def url(self):
        """The link, if this clipping is one — otherwise None.

        The same rule the URL filter counts: a text clipping whose whole
        body is a single http(s) link. Deciding it here rather than only in
        SQL keeps the two answers from drifting apart."""
        if self.kind != "text":
            return None
        text = (self.body or self.preview or "").strip()
        if " " in text or "\n" in text:
            return None
        return text if text.startswith(("http://", "https://")) else None

    @property
    def blob_path(self):
        return os.path.join(BLOB_DIR, self.blob) if self.blob else None

    @property
    def thumb_path(self):
        return os.path.join(THUMB_DIR, self.thumb) if self.thumb else None

    def when(self):
        """When it was captured.  This never changes."""
        return datetime.fromtimestamp(self.created).strftime("%b %-d, %-I:%M %p")

    def used_label(self):
        """When it was last put back on the clipboard, if that has happened
        since it was captured.  Same day gets just the time."""
        if not self.used or self.used - self.created < 1.0:
            return ""
        captured = datetime.fromtimestamp(self.created)
        recalled = datetime.fromtimestamp(self.used)
        if recalled.date() == captured.date():
            return recalled.strftime("used %-I:%M %p")
        return recalled.strftime("used %b %-d, %-I:%M %p")

    def last_active(self):
        """The moment the age limit counts from: the last recall, or the
        capture if it has never been recalled."""
        return self.used or self.created

    def days_left(self, max_days):
        """Days until the age limit takes it, or None if it is safe."""
        if self.pinned or not max_days:
            return None
        return max_days - (time.time() - self.last_active()) / 86400.0

    def expiry_label(self, max_days):
        left = self.days_left(max_days)
        if left is None or left > expiry_warning_days(max_days):
            return ""
        if left <= 0:
            return "expiring"
        if left < 1:
            return "expires today"
        days = int(round(left))
        return "%d day%s left" % (days, "" if days == 1 else "s")

    def detail(self):
        bits = []
        if self.app:
            bits.append(self.app)
        if self.kind == "image":
            bits.append("%d x %d" % (self.width, self.height))
        else:
            n = len(self.body or "")
            bits.append("%s char%s" % (f"{n:,}", "" if n == 1 else "s"))
        return "  ·  ".join(bits)


class Store(object):
    """SQLite index plus the PNG files on disk.

    Blobs live outside the database on purpose: an image item is then a real
    file that Preview and the Finder can open straight from the picker's
    context menu, and the database stays small enough to be read on every
    keystroke of the search field.
    """

    COLUMNS = ("id, kind, created, preview, body, blob, thumb, "
               "width, height, nbytes, app, pinned, used, "
               "COALESCE(edited, 0)")

    def __init__(self, path=DB_PATH):
        for d in (SUPPORT_DIR, BLOB_DIR, THUMB_DIR, EXPORT_DIR):
            os.makedirs(d, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)
        self._migrate()
        self.db.commit()

    def _migrate(self):
        """Add the stamp column to a database written before 1.4.0, and fill
        it in for everything already there."""
        columns = [r[1] for r in self.db.execute("PRAGMA table_info(items)")]
        if "stamp" not in columns:
            self.db.execute("ALTER TABLE items ADD COLUMN stamp TEXT DEFAULT ''")
        if "used" not in columns:
            # Before 1.8.0 a recall overwrote `created`. Nothing can recover
            # the original capture times that were lost, but from here on the
            # two are kept apart.
            self.db.execute("ALTER TABLE items ADD COLUMN used REAL")
            self.db.execute("UPDATE items SET used = created")
        if "edited" not in columns:
            # 1.15.0: a pinned clipping can be edited in place, and a card
            # that has been must stop claiming to be a verbatim capture.
            self.db.execute(
                "ALTER TABLE items ADD COLUMN edited INTEGER NOT NULL DEFAULT 0")
        rows = self.db.execute(
            "SELECT id, created FROM items WHERE stamp IS NULL OR stamp = ''"
        ).fetchall()
        for item_id, created in rows:
            self.db.execute("UPDATE items SET stamp = ? WHERE id = ?",
                            (time_stamp(created), item_id))
        if rows:
            self.db.commit()

    def close(self):
        self.db.close()

    # -- reading ----------------------------------------------------------

    # What counts as a URL, decided in SQL rather than stored: a text
    # clipping whose whole body is one link.  Deriving it means no schema
    # change and no migration for the clippings already captured.  A URL is
    # NOT also counted as text, so the four kinds sum to the total.
    URL_TEST = ("kind = 'text'"
                " AND (TRIM(COALESCE(body, '')) LIKE 'http://%'"
                "      OR TRIM(COALESCE(body, '')) LIKE 'https://%')"
                " AND INSTR(TRIM(COALESCE(body, '')), ' ') = 0")

    def _kind_clause(self, kind):
        if kind == "image":
            return "kind = 'image'"
        if kind == "url":
            return self.URL_TEST
        if kind == "text":
            return "kind = 'text' AND NOT (%s)" % self.URL_TEST
        if kind == "pinned":
            return "pinned = 1"
        return None

    def _search_clause(self, query):
        """The text/date search, as (sql, args). Shared by items() and
        counts() so a chip's number always describes the list the same
        search would produce."""
        if not query:
            return None, []
        like = "%" + query + "%"
        clause = "preview LIKE ? OR body LIKE ? OR app LIKE ?"
        args = [like, like, like]
        dated = date_query(query)
        if dated and dated[0] == "range":
            # A relative phrase is a time range, not a string to match.
            clause += " OR (created >= ? AND created < ?)"
            args += [dated[1], dated[2]]
        elif dated:
            clause += " OR stamp LIKE ?"
            args.append(like)
        return clause, args

    def counts(self, query=""):
        """How many clippings each chip would show, under this search."""
        search, base = self._search_clause(query)
        out = {}
        for kind in (None, "pinned", "image", "text", "url"):
            where, args = [], list(base)
            clause = self._kind_clause(kind)
            if clause:
                where.append("(%s)" % clause)
            if search:
                where.append("(%s)" % search)
            sql = "SELECT COUNT(*) FROM items"
            if where:
                sql += " WHERE " + " AND ".join(where)
            out[kind or "all"] = self.db.execute(sql, args).fetchone()[0]
        return out

    def items(self, query="", kind=None, limit=1000):
        sql = "SELECT %s FROM items" % self.COLUMNS
        where, args = [], []
        clause = self._kind_clause(kind)
        if clause:
            where.append("(%s)" % clause)
        search, search_args = self._search_clause(query)
        if search:
            where.append("(%s)" % search)
            args += search_args
        if where:
            sql += " WHERE " + " AND ".join(where)
        # Ordered by last use, so a recalled clipping comes to the front —
        # without disturbing the capture time the card shows.
        sql += " ORDER BY pinned DESC, COALESCE(used, created) DESC LIMIT ?"
        args.append(limit)
        return [Item(r) for r in self.db.execute(sql, args)]

    def get(self, item_id):
        row = self.db.execute(
            "SELECT %s FROM items WHERE id = ?" % self.COLUMNS,
            (item_id,)).fetchone()
        return Item(row) if row else None

    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM items").fetchone()[0]

    def disk_bytes(self):
        total = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        for d in (BLOB_DIR, THUMB_DIR):
            for name in os.listdir(d):
                try:
                    total += os.path.getsize(os.path.join(d, name))
                except OSError:
                    pass
        return total

    # -- writing ----------------------------------------------------------

    def add_text(self, text, app=""):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if self._promote(digest):
            return None
        preview = preview_of(text)
        now = time.time()
        cur = self.db.execute(
            "INSERT INTO items (kind, created, digest, preview, body, "
            "nbytes, app, stamp, used) "
            "VALUES ('text', ?, ?, ?, ?, ?, ?, ?, ?)",
            (now, digest, preview, text,
             len(text.encode("utf-8")), app, time_stamp(now), now))
        self.db.commit()
        return cur.lastrowid

    def add_image(self, png_bytes, width, height, app="", alt_text=None):
        digest = hashlib.sha256(png_bytes).hexdigest()
        if self._promote(digest):
            return None
        blob = "%s.png" % digest[:24]
        with open(os.path.join(BLOB_DIR, blob), "wb") as fh:
            fh.write(png_bytes)
        thumb = make_thumbnail(os.path.join(BLOB_DIR, blob), blob)
        preview = "Image %d x %d" % (width, height)
        now = time.time()
        cur = self.db.execute(
            "INSERT INTO items (kind, created, digest, preview, body, blob, "
            "thumb, width, height, nbytes, app, stamp, used) "
            "VALUES ('image', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now, digest, preview, alt_text, blob, thumb,
             width, height, len(png_bytes), app, time_stamp(now), now))
        self.db.commit()
        return cur.lastrowid

    def _promote(self, digest):
        """Move an identical earlier capture back to the top.

        Copying the same thing twice should not fill the history with
        duplicates, but it should still be the newest thing in the picker -
        that is usually exactly why it was copied again.
        """
        row = self.db.execute(
            "SELECT id FROM items WHERE digest = ? LIMIT 1",
            (digest,)).fetchone()
        if not row:
            return False
        # Copying the same thing again is a fresh use of it, not a fresh
        # capture: the capture time stays where it was.
        now = time.time()
        self.db.execute("UPDATE items SET used = ? WHERE id = ?",
                        (now, row[0]))
        self.db.commit()
        return True

    def touch(self, item_id):
        """Record a recall.  Never moves the capture time."""
        self.db.execute("UPDATE items SET used = ? WHERE id = ?",
                        (time.time(), item_id))
        self.db.commit()

    def set_thumb(self, item_id, name):
        self.db.execute("UPDATE items SET thumb = ? WHERE id = ?",
                        (name, item_id))
        self.db.commit()

    def set_body(self, item_id, text):
        """Replace a text clipping's content, in place.

        Everything derived from the body goes with it — the preview the card
        draws and the byte count it reports — or the card would describe the
        old content. `edited` is set so it stops claiming to be a verbatim
        capture, and `used` is touched because editing is using it: it goes
        to the front and its retention clock restarts.
        """
        text = text or ""
        self.db.execute(
            "UPDATE items SET body = ?, preview = ?, nbytes = ?, "
            "digest = ?, edited = 1, used = ? WHERE id = ?",
            (text, preview_of(text), len(text.encode("utf-8")),
             hashlib.sha256(text.encode("utf-8")).hexdigest(),
             time.time(), item_id))
        self.db.commit()

    def replace_image(self, item_id, png, width, height):
        """Swap an image clipping's picture for another, keeping its row.

        The blob keeps its filename, so nothing else has to be told. The
        thumbnail is rebuilt rather than left describing the old picture,
        which is exactly the trap a crop falls into: at card size a small
        change is invisible and the stale thumbnail looks correct.
        """
        row = self.db.execute(
            "SELECT blob FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None or not row[0]:
            return False
        name = row[0]
        path = os.path.join(BLOB_DIR, name)
        try:
            os.makedirs(BLOB_DIR, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(png)
        except OSError:
            return False
        thumb = make_thumbnail(path, name)
        self.db.execute(
            "UPDATE items SET width = ?, height = ?, nbytes = ?, thumb = ?, "
            "digest = ?, edited = 1, used = ? WHERE id = ?",
            (width, height, len(png), thumb or "",
             hashlib.sha256(png).hexdigest(), time.time(), item_id))
        self.db.commit()
        return True

    def set_pinned(self, item_id, pinned):
        self.db.execute("UPDATE items SET pinned = ? WHERE id = ?",
                        (1 if pinned else 0, item_id))
        self.db.commit()

    def delete(self, item_ids):
        if not item_ids:
            return
        marks = ",".join("?" * len(item_ids))
        rows = self.db.execute(
            "SELECT blob, thumb FROM items WHERE id IN (%s)" % marks,
            item_ids).fetchall()
        self.db.execute("DELETE FROM items WHERE id IN (%s)" % marks, item_ids)
        self.db.commit()
        for blob, thumb in rows:
            _unlink(os.path.join(BLOB_DIR, blob) if blob else None)
            _unlink(os.path.join(THUMB_DIR, thumb) if thumb else None)

    def clear(self, keep_pinned=True):
        sql = "SELECT id FROM items"
        if keep_pinned:
            sql += " WHERE pinned = 0"
        self.delete([r[0] for r in self.db.execute(sql)])

    def prune(self, max_items, max_days):
        """Retention: an item count cap and an age cap, pinned items exempt."""
        doomed = []
        if max_days > 0:
            # Counted from the last USE, not the capture: a clipping being
            # reached for regularly should not age out from under you.
            cutoff = time.time() - max_days * 86400
            doomed += [r[0] for r in self.db.execute(
                "SELECT id FROM items WHERE pinned = 0 "
                "AND COALESCE(used, created) < ?", (cutoff,))]
        if max_items > 0:
            doomed += [r[0] for r in self.db.execute(
                "SELECT id FROM items WHERE pinned = 0 "
                "ORDER BY COALESCE(used, created) DESC LIMIT -1 OFFSET ?",
                (max_items,))]
        self.delete(sorted(set(doomed)))
        return len(set(doomed))


def _unlink(path):
    if path and os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

THUMB_W, THUMB_H = 560, 380          # >2x the largest card's box, for retina


def make_thumbnail(src_path, blob_name):
    """Render a downscaled PNG next to the blob.  Returns the filename."""
    img = NSImage.alloc().initWithContentsOfFile_(src_path)
    if img is None:
        return None
    size = img.size()
    if size.width <= 0 or size.height <= 0:
        return None
    scale = min(THUMB_W / size.width, THUMB_H / size.height, 1.0)
    tw = max(1, int(round(size.width * scale)))
    th = max(1, int(round(size.height * scale)))
    rep = NSBitmapImageRep.alloc().\
        initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, tw, th, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0)
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    if ctx is None:
        return None
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(ctx)
    img.drawInRect_fromRect_operation_fraction_(
        NSMakeRect(0, 0, tw, th), NSZeroRect,
        NSCompositingOperationSourceOver, 1.0)
    NSGraphicsContext.restoreGraphicsState()
    data = rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, {})
    name = "t_" + blob_name
    if data and data.writeToFile_atomically_(os.path.join(THUMB_DIR, name), True):
        return name
    return None


def png_from_pasteboard(pb):
    """Pull the pasteboard's image out as PNG bytes plus its pixel size.

    PNG is asked for first because that is what screenshots and most web
    images already are; anything else is round-tripped through
    NSBitmapImageRep, which is also what normalises the TIFF flavour every
    Cocoa app writes.
    """
    kind = pb.availableTypeFromArray_(list(IMAGE_TYPES))
    if kind is None:
        return None, 0, 0
    data = pb.dataForType_(kind)
    if data is None or data.length() == 0:
        return None, 0, 0
    rep = NSBitmapImageRep.imageRepWithData_(data)
    if rep is None:
        return None, 0, 0
    width, height = int(rep.pixelsWide()), int(rep.pixelsHigh())
    if width <= 0 or height <= 0:
        return None, 0, 0
    if kind == NSPasteboardTypePNG:
        png = data
    else:
        png = rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, {})
    if png is None:
        return None, 0, 0
    return bytes(png), width, height


# ---------------------------------------------------------------------------
# Global hot key (Carbon)
# ---------------------------------------------------------------------------
#
# RegisterEventHotKey is the only way to claim a system-wide chord without
# asking for Accessibility: the window server delivers the event and swallows
# the keystroke, so it never reaches the app underneath.  The Cocoa
# alternative, NSEvent's global monitor, needs the Accessibility grant AND
# lets the keystroke through to whatever is in front - a space would land in
# the frontmost text field every time the picker was opened.
#
# The framework is reached through ctypes because PyObjC does not wrap the
# Carbon Event Manager.

_carbon = ctypes.CDLL("/System/Library/Frameworks/Carbon.framework/Carbon")

kEventClassKeyboard = 0x6B657962         # 'keyb'
kEventHotKeyPressed = 5

cmdKey, shiftKey, optionKey, controlKey = 0x0100, 0x0200, 0x0800, 0x1000


class _EventTypeSpec(ctypes.Structure):
    _fields_ = [("eventClass", ctypes.c_uint32), ("eventKind", ctypes.c_uint32)]


class _EventHotKeyID(ctypes.Structure):
    _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]


_HANDLER = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p)

_carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
_carbon.RegisterEventHotKey.argtypes = [
    ctypes.c_uint32, ctypes.c_uint32, _EventHotKeyID, ctypes.c_void_p,
    ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
_carbon.RegisterEventHotKey.restype = ctypes.c_int32
_carbon.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]
_carbon.UnregisterEventHotKey.restype = ctypes.c_int32
_carbon.InstallEventHandler.argtypes = [
    ctypes.c_void_p, _HANDLER, ctypes.c_ulong,
    ctypes.POINTER(_EventTypeSpec), ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p)]
_carbon.InstallEventHandler.restype = ctypes.c_int32


class HotKey(object):
    """One registered chord.  Keeping the ctypes callback alive matters:
    if Python collects it the window server calls a freed trampoline and the
    app dies the first time the hotkey is pressed."""

    def __init__(self, callback):
        self._callback = callback
        self._ref = ctypes.c_void_p()
        self._registered = False
        self._trampoline = _HANDLER(self._fire)
        spec = _EventTypeSpec(kEventClassKeyboard, kEventHotKeyPressed)
        handler_ref = ctypes.c_void_p()
        _carbon.InstallEventHandler(
            _carbon.GetApplicationEventTarget(), self._trampoline, 1,
            ctypes.byref(spec), None, ctypes.byref(handler_ref))

    def _fire(self, next_handler, event, user_data):
        try:
            self._callback()
        except Exception as exc:                      # never let it reach C
            sys.stderr.write("Stache: hotkey handler: %r\n" % (exc,))
        return 0                                      # noErr

    def register(self, key_code, modifiers):
        self.unregister()
        hk_id = _EventHotKeyID(0x53545348, 1)         # 'STSH'
        status = _carbon.RegisterEventHotKey(
            int(key_code), int(modifiers), hk_id,
            _carbon.GetApplicationEventTarget(), 0, ctypes.byref(self._ref))
        self._registered = (status == 0)
        return self._registered

    def unregister(self):
        if self._registered and self._ref:
            _carbon.UnregisterEventHotKey(self._ref)
        self._registered = False
        self._ref = ctypes.c_void_p()


# Key codes worth naming in the hotkey field.  Everything else falls back to
# whatever character the keyboard layout produces.
KEY_NAMES = {
    36: "Return", 48: "Tab", 49: "Space", 51: "Delete", 53: "Esc",
    76: "Enter", 96: "F5", 97: "F6", 98: "F7", 99: "F3", 100: "F8",
    101: "F9", 103: "F11", 105: "F13", 107: "F14", 109: "F10", 111: "F12",
    113: "F15", 114: "Help", 115: "Home", 116: "Page Up", 117: "Fwd Del",
    118: "F4", 119: "End", 120: "F2", 121: "Page Down", 122: "F1",
    123: "Left", 124: "Right", 125: "Down", 126: "Up",
    0: "A", 1: "S", 2: "D", 3: "F", 4: "H", 5: "G", 6: "Z", 7: "X", 8: "C",
    9: "V", 11: "B", 12: "Q", 13: "W", 14: "E", 15: "R", 16: "Y", 17: "T",
    18: "1", 19: "2", 20: "3", 21: "4", 22: "6", 23: "5", 24: "=", 25: "9",
    26: "7", 27: "-", 28: "8", 29: "0", 30: "]", 31: "O", 32: "U", 33: "[",
    34: "I", 35: "P", 37: "L", 38: "J", 39: "'", 40: "K", 41: ";", 42: "\\",
    43: ",", 44: "/", 45: "N", 46: "M", 47: ".", 50: "`",
}


def hotkey_label(code, mods):
    out = ""
    if mods & controlKey:
        out += "⌃"
    if mods & optionKey:
        out += "⌥"
    if mods & shiftKey:
        out += "⇧"
    if mods & cmdKey:
        out += "⌘"
    return out + KEY_NAMES.get(int(code), "Key %d" % code)


def carbon_mods(ns_flags):
    mods = 0
    if ns_flags & NSEventModifierFlagCommand:
        mods |= cmdKey
    if ns_flags & NSEventModifierFlagShift:
        mods |= shiftKey
    if ns_flags & NSEventModifierFlagOption:
        mods |= optionKey
    if ns_flags & NSEventModifierFlagControl:
        mods |= controlKey
    return mods


# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------
#
# The whole grid is ONE view that draws every card itself, rather than a view
# per card.  A thousand-item history would otherwise be a thousand NSViews to
# build, lay out and tear down on every keystroke in the search field; drawing
# only the cards the scroller has exposed keeps that flat.

CARD_SIZES = {                       # name -> (width, height)
    "small": (190, 158),
    "medium": (230, 188),
    "large": (272, 220),
}
CARD_W, CARD_H = CARD_SIZES["large"]
GAP, MARGIN = 12, 12
# The card is a picture with a caption above and below it, rather than a
# picture sharing the card with a footer: the date goes on top, the source
# and size underneath, and the thumbnail takes every point neither needs.
CARD_PAD = 6
DATE_H = 14
META_H = 13
THUMB_BOX_H = CARD_H - 2 * CARD_PAD - DATE_H - META_H - 6


def apply_card_size():
    """Card size is a preference, so the measurements that hang off it are
    recomputed rather than fixed at import time.  Everything that draws or
    places a card reads these at the moment it needs them."""
    global CARD_W, CARD_H, THUMB_BOX_H, STRIP_CONTENT_H, STRIP_H
    global COLUMN_CONTENT_W
    CARD_W, CARD_H = CARD_SIZES.get(str(pref(DEF_CARD_SIZE)),
                                    CARD_SIZES["large"])
    THUMB_BOX_H = CARD_H - 2 * CARD_PAD - DATE_H - META_H - 6
    STRIP_CONTENT_H = HEADER_H + 2 * MARGIN + CARD_H + 18 + HINT_H
    STRIP_H = STRIP_CONTENT_H + TITLE_H
    # The column's WIDTH hangs off the card exactly as the strip's height
    # does. Left out of here, it kept the width of whatever card size was
    # in force at import — a 190px card in a 312px column.
    COLUMN_CONTENT_W = CARD_W + 2 * MARGIN + 16


def _para(alignment=0, wrap=True):
    p = NSMutableParagraphStyle.alloc().init()
    p.setAlignment_(alignment)
    if not wrap:
        p.setLineBreakMode_(NSLineBreakByTruncatingTail)
    return p


class GridView(NSView):
    """Newest-first grid of clipboard cards with mouse and keyboard selection."""

    def initWithFrame_(self, frame):
        self = objc.super(GridView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._items = []
        self._selected = 0
        # Everything currently selected, the cursor included.  A set
        # rather than a range: Cmd-click can leave gaps in it.
        self._selection = {0}
        self._anchor = 0        # where a Shift-click measures from
        self._hover = -1
        self._thumbs = {}                 # item id -> NSImage, drawn lazily
        self.single_row = False           # strip layout: one scrolling row
        self.single_col = False           # column layout: one scrolling column
        self.delegate = None
        self._tracking = None
        return self

    # -- geometry ---------------------------------------------------------

    def isFlipped(self):
        return True

    def acceptsFirstResponder(self):
        return True

    def acceptsFirstMouse_(self, event):
        # After a pick the picker hands focus back to the app you came from,
        # so the next click arrives while Stache is inactive.  Without this
        # that click only reactivates the app and never reaches a card,
        # which left the selection pointing at something else.
        return True

    def columns(self):
        if self.single_col:
            return 1
        if self.single_row:
            return max(1, len(self._items))
        usable = self.bounds().size.width - 2 * MARGIN + GAP
        return max(1, int(usable // (CARD_W + GAP)))

    def cardRect_(self, index):
        cols = self.columns()
        row, col = divmod(index, cols)
        return NSMakeRect(MARGIN + col * (CARD_W + GAP),
                          MARGIN + row * (CARD_H + GAP), CARD_W, CARD_H)

    def indexAt_(self, point):
        for i in range(len(self._items)):
            r = self.cardRect_(i)
            if (r.origin.x <= point.x <= r.origin.x + r.size.width and
                    r.origin.y <= point.y <= r.origin.y + r.size.height):
                return i
        return -1

    def contentHeight(self):
        if self.single_row:
            return MARGIN * 2 + CARD_H
        if self.single_col:
            count = len(self._items)
            if not count:
                return 200
            return MARGIN * 2 + count * CARD_H + (count - 1) * GAP
        if not self._items:
            return 200
        rows = (len(self._items) + self.columns() - 1) // self.columns()
        return MARGIN * 2 + rows * CARD_H + (rows - 1) * GAP

    def contentWidth(self):
        if self.single_col:
            return MARGIN * 2 + CARD_W
        count = len(self._items)
        if not count:
            return 200
        return MARGIN * 2 + count * CARD_W + (count - 1) * GAP

    def relayout(self):
        clip = self.superview()
        bounds = clip.bounds().size if clip else self.bounds().size
        if self.single_row:
            # The row grows sideways and fills the strip vertically, so the
            # scroll view scrolls horizontally and never vertically.
            self.setFrameSize_(NSMakeSize(
                max(self.contentWidth(), bounds.width), bounds.height))
        elif self.single_col:
            # The mirror: one card wide, growing downwards.
            self.setFrameSize_(NSMakeSize(
                bounds.width, max(self.contentHeight(), bounds.height)))
        else:
            self.setFrameSize_(NSMakeSize(bounds.width, self.contentHeight()))
        self.setNeedsDisplay_(True)

    def setFrameSize_(self, size):
        objc.super(GridView, self).setFrameSize_(size)
        self.updateTrackingAreas()

    def updateTrackingAreas(self):
        if self._tracking is not None:
            self.removeTrackingArea_(self._tracking)
        self._tracking = NSTrackingArea.alloc().\
            initWithRect_options_owner_userInfo_(
                self.bounds(),
                NSTrackingMouseEnteredAndExited | 0x02 |   # MouseMoved
                NSTrackingActiveInKeyWindow,
                self, None)
        self.addTrackingArea_(self._tracking)

    # -- content ----------------------------------------------------------

    def setItems_(self, items):
        """Replace the list, keeping the selection on the same clipping.

        Resetting to index 0 looked harmless until the picker started
        staying open: every rebuild moved the selection to the first card —
        which is whatever is pinned, since pinned sorts first — so ⌫ after a
        pick asked about the pinned clipping rather than the one under the
        pointer.
        """
        previous = self.selectedItem()
        previous_id = previous.id if previous is not None else None
        self._items = list(items)
        self._thumbs = {}
        index = 0
        if previous_id is not None:
            # Gone from this list — unpinned out of the Pinned filter,
            # searched away, deleted.  Select NOTHING rather than falling
            # back to card 0: the old behaviour moved the selection onto a
            # different clipping without saying so, and the very next ⌫ then
            # deleted something nobody had chosen.
            index = -1
            for i, item in enumerate(self._items):
                if item.id == previous_id:
                    index = i
                    break
        self._selected = index if self._items else -1
        # A rebuild collapses a multiple selection back to the cursor. The
        # list it was made against no longer exists — after a delete the
        # indices mean different clippings — and silently carrying it over
        # would put a later delete on the wrong cards.
        self._selection = ({self._selected}
                           if self._items and self._selected >= 0 else set())
        self._anchor = max(0, self._selected)
        self.relayout()

    def scrollSelectionIntoView(self):
        """Keep the selected card where it can be seen.

        Unpinning re-sorts the list, so the card moves — often a long way
        along a wide strip.  The selection followed it correctly and the eye
        did not."""
        if 0 <= self._selected < len(self._items):
            self.scrollRectToVisible_(_outset(self.cardRect_(self._selected),
                                              GAP))

    def items(self):
        return self._items

    def selectedItem(self):
        if 0 <= self._selected < len(self._items):
            return self._items[self._selected]
        return None

    def selectedItems(self):
        """Every selected clipping, in the order they appear."""
        return [self._items[i] for i in sorted(self._selection)
                if 0 <= i < len(self._items)]

    def _selectOnly_(self, index):
        self._selected = index
        self._anchor = index
        self._selection = {index}

    def _thumbFor_(self, item):
        """The thumbnail, rebuilt from the full-resolution PNG if the one on
        disk is too small for the card it now has to fill.

        Card size is a setting, so a thumbnail made for a small card would
        otherwise be stretched across a large one.  The blobs are always
        full resolution, so this costs one redraw per clipping, once.
        """
        if item.id in self._thumbs:
            return self._thumbs[item.id]
        wanted = (CARD_W - 2 * CARD_PAD) * 2
        img = None
        if item.thumb_path and os.path.exists(item.thumb_path):
            img = NSImage.alloc().initWithContentsOfFile_(item.thumb_path)
            if img is not None and _pixel_width(img) < wanted:
                img = None
        if img is None and item.blob_path and os.path.exists(item.blob_path):
            name = make_thumbnail(item.blob_path, item.blob)
            if name:
                item.thumb = name
                if self.delegate is not None:
                    self.delegate.thumbnailRebuilt_name_(item, name)
                img = NSImage.alloc().initWithContentsOfFile_(
                    os.path.join(THUMB_DIR, name))
            else:
                img = NSImage.alloc().initWithContentsOfFile_(item.blob_path)
        self._thumbs[item.id] = img
        return img

    # -- drawing ----------------------------------------------------------

    def drawRect_(self, dirty):
        NSColor.windowBackgroundColor().setFill()
        NSBezierPath.fillRect_(dirty)
        if not self._items:
            self._drawEmpty_(dirty)
            return
        for i in range(len(self._items)):
            r = self.cardRect_(i)
            if (r.origin.y + r.size.height < dirty.origin.y or
                    r.origin.y > dirty.origin.y + dirty.size.height or
                    r.origin.x + r.size.width < dirty.origin.x or
                    r.origin.x > dirty.origin.x + dirty.size.width):
                continue
            self._drawCard_index_(r, i)

    def _drawEmpty_(self, dirty):
        text = "Nothing here yet.\nCopy something and it will show up."
        if self.delegate is not None and self.delegate.hasQuery():
            text = "No matches."
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(13),
            NSForegroundColorAttributeName: NSColor.secondaryLabelColor(),
            NSParagraphStyleAttributeName: _para(alignment=2),
        }
        box = NSMakeRect(0, 60, self.bounds().size.width, 60)
        NSAttributedString.alloc().initWithString_attributes_(
            text, attrs).drawInRect_(box)

    def _drawCard_index_(self, rect, index):
        item = self._items[index]
        selected = (index in self._selection)
        hovered = (index == self._hover)

        body = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            rect, 8, 8)
        NSColor.textBackgroundColor().setFill()
        body.fill()
        if selected:
            NSColor.controlAccentColor().colorWithAlphaComponent_(0.15).setFill()
            body.fill()
        elif hovered:
            NSColor.labelColor().colorWithAlphaComponent_(0.05).setFill()
            body.fill()
        if selected:
            NSColor.controlAccentColor().setStroke()
            body.setLineWidth_(2.0)
        else:
            NSColor.separatorColor().setStroke()
            body.setLineWidth_(1.0)
        body.stroke()

        text_w = CARD_W - 2 * CARD_PAD - 4
        stamp = NSMakeRect(rect.origin.x + CARD_PAD + 2,
                           rect.origin.y + CARD_PAD - 1, text_w, DATE_H)
        title = ("📌 " if item.pinned else "") + item.when()
        if getattr(item, "edited", 0):
            title += "  · edited"
        drawn = NSAttributedString.alloc().initWithString_attributes_(title, {
            NSFontAttributeName: NSFont.systemFontOfSize_(11.5),
            NSForegroundColorAttributeName: NSColor.labelColor(),
            NSParagraphStyleAttributeName: _para(wrap=False),
        })
        drawn.drawInRect_(stamp)
        # The recall, if there has been one, follows the capture time in the
        # dimmer colour — two facts, plainly separated.
        recalled = item.used_label()
        if recalled:
            used_x = stamp.origin.x + drawn.size().width + 7
            room = rect.origin.x + CARD_W - CARD_PAD - used_x
            if room > 40:
                NSAttributedString.alloc().initWithString_attributes_(
                    recalled, {
                        NSFontAttributeName: NSFont.systemFontOfSize_(10),
                        NSForegroundColorAttributeName:
                            NSColor.tertiaryLabelColor(),
                        NSParagraphStyleAttributeName: _para(wrap=False),
                    }).drawInRect_(NSMakeRect(used_x, stamp.origin.y + 1,
                                              room, DATE_H))

        inner = NSMakeRect(rect.origin.x + CARD_PAD,
                           rect.origin.y + CARD_PAD + DATE_H + 3,
                           CARD_W - 2 * CARD_PAD, THUMB_BOX_H)
        if item.kind == "image":
            self._drawThumb_item_(inner, item)
        else:
            self._drawText_item_(inner, item)

        meta = NSMakeRect(rect.origin.x + CARD_PAD + 2,
                          rect.origin.y + CARD_H - CARD_PAD - META_H,
                          text_w, META_H)
        # A clipping close to the age limit says so, in red, on the right of
        # the line that already carries where it came from.
        # The source application's icon sits at the bottom right of the
        # card, on the same line as where it came from.  The text gives up
        # the room first so it can never run underneath.
        icon = app_icon(item.app)
        if icon is not None:
            spot = NSMakeRect(rect.origin.x + CARD_W - CARD_PAD - SOURCE_ICON,
                              rect.origin.y + CARD_H - CARD_PAD - META_H + 1,
                              SOURCE_ICON, SOURCE_ICON)
            icon.drawInRect_fromRect_operation_fraction_respectFlipped_hints_(
                spot, NSZeroRect, NSCompositingOperationSourceOver, 1.0,
                True, None)
            meta.size.width -= SOURCE_ICON + 6

        warning = item.expiry_label(pref(DEF_MAX_DAYS))
        if warning:
            drawn_warning = NSAttributedString.alloc().\
                initWithString_attributes_(warning, {
                    NSFontAttributeName: NSFont.boldSystemFontOfSize_(10),
                    NSForegroundColorAttributeName: NSColor.systemRedColor(),
                    NSParagraphStyleAttributeName: _para(alignment=1),
                })
            drawn_warning.drawInRect_(meta)
            meta.size.width -= drawn_warning.size().width + 8
        NSAttributedString.alloc().initWithString_attributes_(item.detail(), {
            NSFontAttributeName: NSFont.systemFontOfSize_(10),
            NSForegroundColorAttributeName: NSColor.secondaryLabelColor(),
            NSParagraphStyleAttributeName: _para(wrap=False),
        }).drawInRect_(meta)

    def _drawThumb_item_(self, box, item):
        NSColor.windowBackgroundColor().setFill()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            box, 4, 4).fill()
        img = self._thumbFor_(item)
        if img is None:
            return
        size = img.size()
        if size.width <= 0 or size.height <= 0:
            return
        scale = min(box.size.width / size.width,
                    box.size.height / size.height, 1.0)
        w, h = size.width * scale, size.height * scale
        dest = NSMakeRect(box.origin.x + (box.size.width - w) / 2.0,
                          box.origin.y + (box.size.height - h) / 2.0, w, h)
        img.drawInRect_fromRect_operation_fraction_respectFlipped_hints_(
            dest, NSZeroRect, NSCompositingOperationSourceOver, 1.0, True, None)

    def _drawText_item_(self, box, item):
        text = (item.body or item.preview or "")[:600]
        NSAttributedString.alloc().initWithString_attributes_(text, {
            NSFontAttributeName: NSFont.systemFontOfSize_(11),
            NSForegroundColorAttributeName: NSColor.labelColor(),
            NSParagraphStyleAttributeName: _para(),
        }).drawInRect_(box)

    # -- mouse ------------------------------------------------------------

    def mouseMoved_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.indexAt_(point)
        if index != self._hover:
            self._hover = index
            self.setNeedsDisplay_(True)

    def mouseExited_(self, event):
        self._hover = -1
        self.setNeedsDisplay_(True)

    def mouseDown_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.indexAt_(point)
        if index < 0:
            return
        flags = event.modifierFlags()
        # Shift extends from the anchor, Cmd adds or removes one. Neither
        # copies: building a selection is not choosing from it, and putting
        # each card on the pasteboard as it was added would be useless.
        if flags & NSEventModifierFlagShift:
            low, high = sorted((self._anchor, index))
            self._selection = set(range(low, high + 1))
            self._selected = index
            self.setNeedsDisplay_(True)
            return
        if flags & NSEventModifierFlagCommand:
            if index in self._selection and len(self._selection) > 1:
                self._selection.discard(index)
            else:
                self._selection.add(index)
            self._selected = index
            self._anchor = index
            self.setNeedsDisplay_(True)
            return
        self._selectOnly_(index)
        self.setNeedsDisplay_(True)
        if self.delegate is not None:
            # A single click is the whole point of a picker: choose the item
            # and get out of the way.  Option-click selects without choosing,
            # for looking through the history without disturbing the
            # pasteboard.
            if flags & NSEventModifierFlagOption:
                return
            self.delegate.gridDidActivate_(self._items[index])

    def rightMouseDown_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        index = self.indexAt_(point)
        if index < 0 or self.delegate is None:
            return
        # A right-click inside an existing multiple selection acts on all of
        # it; anywhere else it selects the one card first.
        if index not in self._selection:
            self._selectOnly_(index)
        self.setNeedsDisplay_(True)
        menu = self.delegate.menuForItem_(self._items[index])
        NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

    # -- keyboard ---------------------------------------------------------

    def moveSelectionBy_(self, delta):
        if not self._items:
            return
        self._selectOnly_(max(0, min(len(self._items) - 1,
                                     self._selected + delta)))
        self.scrollRectToVisible_(
            _outset(self.cardRect_(self._selected), GAP))
        self.setNeedsDisplay_(True)

    def keyDown_(self, event):
        code = event.keyCode()
        cols = self.columns()
        if code == 123:                                    # left
            self.moveSelectionBy_(-1)
        elif code == 124:                                  # right
            self.moveSelectionBy_(1)
        elif code == 126:                                  # up
            self.moveSelectionBy_(
                -1 if (self.single_row or self.single_col) else -cols)
        elif code == 125:                                  # down
            self.moveSelectionBy_(
                1 if (self.single_row or self.single_col) else cols)
        elif code == 115:                                  # home
            self.moveSelectionBy_(-len(self._items))
        elif code == 119:                                  # end
            self.moveSelectionBy_(len(self._items))
        elif code in (36, 76):                             # return / enter
            item = self.selectedItem()
            if item is not None and self.delegate is not None:
                self.delegate.gridDidActivate_(item)
        elif code in (51, 117):                            # delete
            chosen = self.selectedItems()
            if chosen and self.delegate is not None:
                self.delegate.gridDidDelete_(chosen)
        elif code == 49:                                   # space: Quick Look
            self.toggleQuickLook()
        elif (event.modifierFlags() & NSEventModifierFlagCommand and
              (event.charactersIgnoringModifiers() or "") in ("/", "?")):
            if self.delegate is not None:
                self.delegate.gridDidAskForHelp()
        elif (event.modifierFlags() & NSEventModifierFlagCommand and
              (event.charactersIgnoringModifiers() or "") == "0"):
            if self.delegate is not None:
                self.delegate.gridDidAskToReset()
        elif self.delegate is not None and _is_typing(event):
            self.delegate.gridDidType_(event)
        else:
            objc.super(GridView, self).keyDown_(event)

    # -- Quick Look --------------------------------------------------------

    def toggleQuickLook(self):
        """Show or hide Quick Look, without the picker dismissing itself.

        Quick Look takes key, and the picker hides when it loses key — that
        is what makes clicking away close it. So the picker is told to hold
        its ground first, the same as for Preferences and the help.

        The app is activated BEFORE the panel is ordered front. Without
        that, an accessory app's Quick Look panel comes up without key, and
        it has to be clicked before Space or Esc will close it again.
        """
        if not self._items:
            return
        panel = QLPreviewPanel.sharedPreviewPanel()
        if panel.isVisible():
            panel.orderOut_(None)
            return
        if self.delegate is not None:
            self.delegate.holdOpen()
        NSApp.activateIgnoringOtherApps_(True)
        panel.makeKeyAndOrderFront_(None)

    def acceptsPreviewPanelControl_(self, panel):
        return True

    def beginPreviewPanelControl_(self, panel):
        panel.setDelegate_(self)
        panel.setDataSource_(self)

    def endPreviewPanelControl_(self, panel):
        # Quick Look has given the keyboard back; the picker may dismiss on
        # click-away again.
        if self.delegate is not None:
            self.delegate.releaseHold()

    def numberOfPreviewItemsInPreviewPanel_(self, panel):
        """ONE — whichever clipping is selected.

        Handing Quick Look the whole list was a mistake with a cost: the
        panel asks its data source repeatedly, and preparing a text clipping
        WRITES a file, so every query rewrote every text file in the
        history. Previewing only the selection is both what Finder does and
        the only work worth doing.
        """
        return 1 if self.selectedItem() is not None else 0

    def previewPanel_previewItemAtIndex_(self, panel, index):
        item = self.selectedItem()
        if item is None:
            return None
        path = openable_path(item)
        return NSURL.fileURLWithPath_(path) if path else None

    def previewPanel_handleEvent_(self, panel, event):
        """Arrow keys go back to the grid, and Quick Look follows the
        selection — the same way it does in the Finder."""
        if event.type() == 10 and event.keyCode() in (123, 124, 125, 126):
            self.keyDown_(event)
            QLPreviewPanel.sharedPreviewPanel().reloadData()
            return True
        return False

    def cancelOperation_(self, sender):                    # Esc
        if self.delegate is not None:
            self.delegate.gridDidCancel()


def _pixel_width(image):
    """An NSImage's size() is in points; the pixels are on its reps."""
    return max([int(r.pixelsWide()) for r in image.representations()] or [0])


def _is_typing(event):
    """True for a plain printable keystroke, which belongs in the search
    field.  Anything with a command or control modifier is a shortcut."""
    if event.modifierFlags() & (NSEventModifierFlagCommand |
                                NSEventModifierFlagControl):
        return False
    chars = event.charactersIgnoringModifiers() or ""
    return bool(chars) and chars[0].isprintable()


def _outset(rect, by):
    return NSMakeRect(rect.origin.x - by, rect.origin.y - by,
                      rect.size.width + 2 * by, rect.size.height + 2 * by)


# ---------------------------------------------------------------------------
# The picker panel
# ---------------------------------------------------------------------------

PANEL_W, PANEL_H = 820, 620               # grid layout
HEADER_H = 44
# Strip layout: one row of cards, the header above it, and room for the
# horizontal scroller underneath.
# STRIP_CONTENT_H is what the cards and header need; STRIP_H is the WINDOW,
# which is that plus the title bar.  Conflating the two cost 24pt off the
# bottom of every card until 1.3.0.  TITLE_H is only a starting guess — the
# panel's real chrome is measured once it exists.
HINT_H = 22                               # the key-hints bar under the cards
COLUMN_HEADER_H = 98                      # name, search, then filter
STRIP_CONTENT_H = HEADER_H + 2 * MARGIN + CARD_H + 18 + HINT_H
TITLE_H = 24
STRIP_H = STRIP_CONTENT_H + TITLE_H
STRIP_EDGE = 8                            # gap from the screen edge and Dock
# Space around the tiles in the Dock's own rounded bar. Apple publishes no
# API for the Dock's height, and its window is reported as the whole screen,
# so the reserve is computed from the tile size the user has chosen.
DOCK_CHROME = 24


def dock_reserve(dock):
    """How much of a screen the Dock will cover, as (left, bottom, right).

    Only needed when the Dock is HIDDEN: visibleFrame already excludes a Dock
    that is on screen, but with autohide on it runs to the very edge of the
    display and a window placed there is covered the moment the Dock slides
    up.  Magnification counts, because the pointer is over the Dock precisely
    when it is reaching for something sitting just above it.

    Apple publishes no API for the Dock's size, and the Dock's own window is
    reported as the whole screen, so com.apple.dock's own settings are the
    only source.
    """
    if not dock or not dock.get("autohide"):
        return (0.0, 0.0, 0.0)
    tile = float(dock.get("tilesize") or 48)
    if dock.get("magnification"):
        tile = max(tile, float(dock.get("largesize") or tile))
    depth = tile + DOCK_CHROME
    orientation = str(dock.get("orientation") or "bottom")
    if orientation == "left":
        return (depth, 0.0, 0.0)
    if orientation == "right":
        return (0.0, 0.0, depth)
    return (0.0, depth, 0.0)


def strip_frame(visible, reserve, percent, height=None):
    """Where the strip sits: clear of the Dock on whichever edge it occupies,
    along the bottom of the screen, `percent` of the usable width.

    `height` is the WINDOW height, title bar included.  It defaults to the
    current STRIP_H so the geometry can be tested without a panel.
    """
    left, bottom, right = reserve
    usable = visible.size.width - left - right
    percent = max(20, min(100, int(percent)))
    width = max(CARD_W + 2 * MARGIN + 40, usable * percent / 100.0)
    width = min(width, usable - 2 * STRIP_EDGE)
    return NSMakeRect(visible.origin.x + left + STRIP_EDGE,
                      visible.origin.y + bottom + STRIP_EDGE,
                      width, STRIP_H if height is None else height)


COLUMN_CONTENT_W = CARD_W + 2 * MARGIN + 16   # one card, plus the scroller


def column_frame(visible, reserve, percent, width=None):
    """Where the vertical strip sits: down the LEFT edge, clear of the Dock,
    `percent` of the usable height.

    The mirror of strip_frame. There the height is dictated by the card and
    the width is yours; here the WIDTH is dictated by the card and the
    height is yours.
    """
    left, bottom, right = reserve
    usable = visible.size.height - bottom
    percent = max(20, min(100, int(percent)))
    height = max(CARD_H + 120, usable * percent / 100.0)
    height = min(height, usable - 2 * STRIP_EDGE)
    return NSMakeRect(visible.origin.x + left + STRIP_EDGE,
                      visible.origin.y + bottom + STRIP_EDGE,
                      COLUMN_CONTENT_W if width is None else width,
                      height)


class HeaderView(NSView):
    """The strip holding the search field and the filter, drawn rather than
    left transparent so it reads as one bar and carries a divider.

    It also owns re-laying its contents out: the chips are sized to labels
    that change with the counts, so the positions cannot be expressed as
    autoresizing masks.
    """

    controller = None

    def setFrameSize_(self, size):
        objc.super(HeaderView, self).setFrameSize_(size)
        if self.controller is not None:
            self.controller._layoutHeader()

    def drawRect_(self, dirty):
        NSColor.windowBackgroundColor().setFill()
        NSBezierPath.fillRect_(self.bounds())
        NSColor.separatorColor().setFill()
        NSBezierPath.fillRect_(NSMakeRect(0, 0, self.bounds().size.width, 1))


# The filter chips, in the order they appear. "All" stays: without it the
# only way back to the whole list is to deselect a chip, and a segmented
# control in select-one mode will not deselect.
FILTER_KINDS = (("All", None), ("Pinned", "pinned"), ("Images", "image"),
                ("Text", "text"), ("URL", "url"))
SEARCH_W = 220                            # the search field, pinned right
FILTER_X = 300                            # where the chips start, when there
                                          # is room for them there

SOURCE_ICON = 16                          # the source app badge on a card

HINTS = ("click copy", "⌥click select", "⇧click range", "⌘click add",
         "↵ copy", "Space Quick Look", "⌫ delete", "type to search",
         "⌘0 reset place", "⌘/ help", "esc closes")


class HintView(NSView):
    """The keys, along the bottom, the whole time the picker is open.

    A picker whose shortcuts have to be remembered is a picker whose
    shortcuts do not get used.  It is one line, in the secondary colour, so
    it reads as a legend rather than as content.
    """

    def drawRect_(self, dirty):
        NSColor.windowBackgroundColor().setFill()
        NSBezierPath.fillRect_(self.bounds())
        NSColor.separatorColor().setFill()
        NSBezierPath.fillRect_(NSMakeRect(0, self.bounds().size.height - 1,
                                          self.bounds().size.width, 1))
        text = "   ·   ".join(HINTS)
        NSAttributedString.alloc().initWithString_attributes_(text, {
            NSFontAttributeName: NSFont.systemFontOfSize_(10.5),
            NSForegroundColorAttributeName: NSColor.secondaryLabelColor(),
            NSParagraphStyleAttributeName: _para(wrap=False),
        }).drawInRect_(NSMakeRect(12, 3, self.bounds().size.width - 24, 14))


class PickerController(NSObject):
    """The window the hotkey raises: search field, filter, grid.

    The panel takes keyboard focus while it is up - that is what makes arrow
    keys and type-to-search work - and hands focus back to the application
    that had it as soon as it closes, so the Cmd-V that follows a pick lands
    in the right place.
    """

    def initWithApp_(self, app):
        self = objc.super(PickerController, self).init()
        if self is None:
            return None
        self.app = app
        self.previous_app = None
        self._menu_item = None
        self._menu_path = None
        self._menu_apps = {}
        self._was_key = False
        self._modal = False
        self._yielding = False
        self._flash = None
        self._build()
        return self

    def layoutMode(self):
        mode = pref(DEF_LAYOUT)
        return mode if mode in ("grid", "strip", "column") else "strip"

    def isStrip(self):
        return self.layoutMode() == "strip"

    def isColumn(self):
        return self.layoutMode() == "column"

    def headerHeight(self):
        # A column is too narrow for one row of status, five chips and a
        # search field — everything came out truncated. It gets two rows.
        return COLUMN_HEADER_H if self.isColumn() else HEADER_H

    def frameKey(self):
        # A frame per arrangement. Sharing one made switching layouts a
        # fight: a column's tall narrow frame is nonsense for a strip.
        if self.isStrip():
            return DEF_STRIP_FRAME
        if self.isColumn():
            return DEF_COLUMN_FRAME
        return DEF_PANEL_FRAME

    def _build(self):
        strip, column = self.isStrip(), self.isColumn()
        if strip:
            frame = NSMakeRect(0, 0, PANEL_W, STRIP_CONTENT_H)
        elif column:
            frame = NSMakeRect(0, 0, COLUMN_CONTENT_W, PANEL_H)
        else:
            frame = NSMakeRect(0, 0, PANEL_W, PANEL_H)
        style = (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
                 NSWindowStyleMaskResizable | NSWindowStyleMaskUtilityWindow)
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, style, NSBackingStoreBuffered, False)
        panel.setTitle_("Stache")
        decorate_titlebar(panel, compact=column)
        panel.setReleasedWhenClosed_(False)
        panel.setDelegate_(self)
        if strip:
            # min/max are WINDOW sizes, so they need the chrome the panel
            # actually has rather than an assumed title-bar height.
            locked = STRIP_CONTENT_H + self._chrome_(panel)
            panel.setMinSize_(NSMakeSize(CARD_W + 2 * MARGIN + 40, locked))
            panel.setMaxSize_(NSMakeSize(100000, locked))
        elif column:
            # The mirror: the WIDTH is locked to one card, the height is
            # yours to drag.
            panel.setMinSize_(NSMakeSize(COLUMN_CONTENT_W,
                                         CARD_H + 120 + self._chrome_(panel)))
            panel.setMaxSize_(NSMakeSize(COLUMN_CONTENT_W, 100000))
        else:
            panel.setMinSize_(NSMakeSize(2 * CARD_W + 3 * GAP + 40, 320))
        # NSPanel's hidesOnDeactivate is YES by default.  For an accessory
        # app that is fatal: the panel disappears whenever Stache is not the
        # active application, which includes the instant between ordering it
        # front and activating.  The picker looked like it never opened.
        panel.setHidesOnDeactivate_(False)
        # Float above ordinary windows and follow Tim to whichever Space he
        # is on, full-screen apps included.
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces |
            NSWindowCollectionBehaviorFullScreenAuxiliary)
        content = panel.contentView()
        size = content.bounds().size

        header_h = self.headerHeight()
        header = HeaderView.alloc().initWithFrame_(
            NSMakeRect(0, size.height - header_h, size.width, header_h))
        header.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        content.addSubview_(header)
        self.header = header

        self.search = NSSearchField.alloc().initWithFrame_(
            NSMakeRect(size.width - 12 - SEARCH_W, 8, SEARCH_W, 26))
        self.search.setPlaceholderString_("Search clippings")
        self.search.setTarget_(self)
        self.search.setAction_("searchChanged:")
        self.search.setDelegate_(self)
        self.search.setAutoresizingMask_(NSViewMinXMargin)
        header.addSubview_(self.search)

        # Five chips need about 380pt. A column has nowhere near that, so
        # there it becomes one popup carrying the same five choices and the
        # same counts.
        self.compact_filter = column
        if column:
            self.filter = NSPopUpButton.alloc().initWithFrame_pullsDown_(
                NSMakeRect(12, 10, 150, 24), False)
            self.filter.addItemsWithTitles_([n for n, _ in FILTER_KINDS])
            self.filter.selectItemAtIndex_(0)
        else:
            self.filter = NSSegmentedControl.alloc().initWithFrame_(
                NSMakeRect(FILTER_X, 9, 380, 24))
            self.filter.setSegmentCount_(len(FILTER_KINDS))
            for i, (label, _kind) in enumerate(FILTER_KINDS):
                self.filter.setLabel_forSegment_(label, i)
            self.filter.setTrackingMode_(NSSegmentSwitchTrackingSelectOne)
            self.selectKindIndex_(0)
        self.filter.setTarget_(self)
        self.filter.setAction_("filterChanged:")
        header.addSubview_(self.filter)

        self.help_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(size.width - 12 - SEARCH_W - 34, 9, 26, 24))
        self.help_button.setTitle_("?")
        self.help_button.setBezelStyle_(1)
        self.help_button.setTarget_(self)
        self.help_button.setAction_("showHelp:")
        self.help_button.setToolTip_("What Stache does, and how (⌘/)")
        self.help_button.setAutoresizingMask_(NSViewMinXMargin)
        header.addSubview_(self.help_button)

        self.status = NSTextField.alloc().initWithFrame_(
            NSMakeRect(12, 12, FILTER_X - 24, 18))
        self.status.setEditable_(False)
        self.status.setBordered_(False)
        self.status.setDrawsBackground_(False)
        self.status.setFont_(NSFont.systemFontOfSize_(11))
        self.status.setTextColor_(NSColor.secondaryLabelColor())
        header.addSubview_(self.status)
        # In a column the title bar cannot hold the version and copyright
        # beside a centred name — at 230pt they overlapped into a pile — so
        # they are set as ordinary text above the search field instead.
        self.brand = self.copyright = None
        if column:
            self.brand = _plain("Stache %s" % APP_VERSION, 12, 74, 140)
            self.brand.setFont_(NSFont.boldSystemFontOfSize_(11))
            self.brand.setTextColor_(NSColor.labelColor())
            header.addSubview_(self.brand)
            self.copyright = _plain(COPYRIGHT, 12, 74, 140)
            self.copyright.setFont_(NSFont.systemFontOfSize_(10))
            self.copyright.setAlignment_(2)              # right
            header.addSubview_(self.copyright)

        header.controller = self
        self._layoutHeader()

        # The hint bar is one line of text about 700pt wide. A column is
        # roughly 310pt, so it could only ever be shown truncated, which is
        # worse than not showing it: a legend you cannot read is furniture.
        # The keys are all still in the help, and in column layout the space
        # goes to the cards instead.
        hint_h = 0 if column else HINT_H
        if hint_h:
            self.hints = HintView.alloc().initWithFrame_(
                NSMakeRect(0, 0, size.width, hint_h))
            self.hints.setAutoresizingMask_(
                NSViewWidthSizable | 0x20)      # MaxYMargin
            content.addSubview_(self.hints)
        else:
            self.hints = None

        self.scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(0, hint_h, size.width,
                       size.height - header_h - hint_h))
        self.scroll.setHasVerticalScroller_(not strip)
        self.scroll.setHasHorizontalScroller_(strip)
        self.scroll.setAutohidesScrollers_(True)
        # Draw the background rather than leaving it clear: the horizontal
        # scroller's track sits below the cards, and an undrawn scroll view
        # left it as a white band across the bottom of the strip.
        self.scroll.setDrawsBackground_(True)
        self.scroll.setBackgroundColor_(NSColor.windowBackgroundColor())
        self.scroll.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        content.addSubview_(self.scroll)

        self.grid = GridView.alloc().initWithFrame_(
            NSMakeRect(0, 0, size.width, 400))
        self.grid.single_row = strip
        self.grid.single_col = column
        self.grid.delegate = self
        self.scroll.setDocumentView_(self.grid)

        clip = self.scroll.contentView()
        clip.setPostsFrameChangedNotifications_(True)
        from Foundation import NSNotificationCenter
        NSNotificationCenter.defaultCenter().\
            addObserver_selector_name_object_(
                self, "clipResized:", "NSViewFrameDidChangeNotification", clip)

        self.panel = panel

    # -- showing and hiding -----------------------------------------------

    def toggle(self):
        if self.panel.isVisible():
            self.hide()
        else:
            self.show()

    def show(self):
        workspace = NSWorkspace.sharedWorkspace()
        front = workspace.frontmostApplication()
        if front is not None and front.bundleIdentifier() != BUNDLE_ID:
            self.previous_app = front
        self.reload()
        self._restoreFrame()
        # Activate first, then order front: an accessory app that orders a
        # window front before it is active can have that window hidden out
        # from under it before the activation lands.
        NSApp.activateIgnoringOtherApps_(True)
        self.panel.makeKeyAndOrderFront_(None)
        self.panel.makeFirstResponder_(self.grid)
        self._was_key = False

    def reopenAfterRebuild_kind_(self, query, kind):
        """Back on screen with the search and filter that were in force.

        Ordered front rather than made key: the change came from the
        Preferences window, and stealing focus back from what you are still
        adjusting is its own kind of rude.
        """
        if query:
            self.search.setStringValue_(query)
        try:
            if 0 <= int(kind) < len(FILTER_KINDS):
                self.selectKindIndex_(int(kind))
        except (TypeError, ValueError):
            pass
        self.reload()
        self._restoreFrame()
        self.panel.orderFront_(None)

    def _restoreFrame(self):
        """Put the panel back where it was, unless that is not somewhere it
        can actually be seen.

        Saving the frame by hand rather than with setFrameAutosaveName_ is
        deliberate: the autosave name writes the window's frame as soon as it
        is set, so there was always a saved frame - the creation rect at
        (0, 0) - and the centring path could never run.
        """
        saved = defaults().stringForKey_(self.frameKey())
        if saved:
            frame = NSRectFromString(saved)
            if self.isStrip():
                # Height is dictated by the card, the header and the hint
                # bar, never by what was saved: a frame from before the hint
                # bar, or from a different card size, describes a strip that
                # no longer exists.
                frame.size.height = (STRIP_CONTENT_H
                                     + self._chrome_(self.panel))
            elif self.isColumn():
                # The mirror: one card wide, whatever height you dragged.
                frame.size.width = COLUMN_CONTENT_W
            if self._frameIsVisible_(frame):
                self.panel.setFrame_display_(frame, False)
                return
        self.parkAtDefault()

    def parkAtDefault(self):
        """The calculated home for whichever arrangement is in force."""
        if self.isStrip():
            self._parkAboveDock()
        elif self.isColumn():
            self._parkBesideDock()
        else:
            self._centerOnActiveScreen()

    def _frameIsVisible_(self, frame):
        """Most of the panel, and its title bar, must land on a screen that
        exists - otherwise a frame saved on a display that is now unplugged,
        or one nudged off the bottom, would strand the picker off-screen."""
        floor = STRIP_CONTENT_H if self.isStrip() else 200
        if frame.size.width < 200 or frame.size.height < floor - 40:
            return False
        if self.isStrip():
            screen = self._activeScreen()
            visible = screen.visibleFrame()
            left, bottom, right = self._dockReserve_(screen)
            # Anything sitting in the hidden Dock's path is not usable, even
            # though it is technically on the screen.
            if frame.origin.y < visible.origin.y + bottom:
                return False
            if frame.origin.x < visible.origin.x + left:
                return False
            if (frame.origin.x + frame.size.width
                    > visible.origin.x + visible.size.width - right):
                return False
        area = frame.size.width * frame.size.height
        best = 0.0
        for screen in NSScreen.screens():
            visible = screen.visibleFrame()
            overlap_w = max(0.0, min(frame.origin.x + frame.size.width,
                                     visible.origin.x + visible.size.width)
                            - max(frame.origin.x, visible.origin.x))
            overlap_h = max(0.0, min(frame.origin.y + frame.size.height,
                                     visible.origin.y + visible.size.height)
                            - max(frame.origin.y, visible.origin.y))
            best = max(best, overlap_w * overlap_h)
        return best >= 0.85 * area

    def _chrome_(self, panel):
        """How much taller the window is than its content — the title bar."""
        content = panel.contentView().bounds().size.height
        return max(0.0, panel.frame().size.height - content)

    def _dockReserve_(self, screen):
        return dock_reserve(
            defaults().persistentDomainForName_("com.apple.dock"))

    def _activeScreen(self):
        """The screen the pointer is on — where Tim is actually working."""
        mouse = NSEvent.mouseLocation()
        for candidate in NSScreen.screens():
            f = candidate.frame()
            if (f.origin.x <= mouse.x <= f.origin.x + f.size.width and
                    f.origin.y <= mouse.y <= f.origin.y + f.size.height):
                return candidate
        return NSScreen.mainScreen()

    def _parkAboveDock(self):
        """Left edge, just above the Dock, a share of the screen wide.

        visibleFrame already excludes the Dock and the menu bar, so its
        bottom-left corner IS "just above the Dock" — and it stays right when
        the Dock is hidden, moved to a side, or resized.
        """
        screen = self._activeScreen()
        self.panel.setFrame_display_(
            strip_frame(screen.visibleFrame(), self._dockReserve_(screen),
                        pref(DEF_STRIP_PCT),
                        STRIP_CONTENT_H + self._chrome_(self.panel)), False)

    def _parkBesideDock(self):
        """Left edge, up from the Dock, a share of the screen tall."""
        screen = self._activeScreen()
        self.panel.setFrame_display_(
            column_frame(screen.visibleFrame(), self._dockReserve_(screen),
                         pref(DEF_STRIP_PCT), COLUMN_CONTENT_W), False)

    def resetPosition_(self, sender):
        """⌘0 — back to the calculated home, forgetting where it was dragged.

        Dragging and resizing are remembered, which is what makes them
        useful, and also what makes them a trap: a strip dragged half off a
        screen that is no longer attached is remembered just as faithfully.
        """
        defaults().removeObjectForKey_(self.frameKey())
        self.parkAtDefault()
        self.grid.relayout()
        self.status.setTextColor_(NSColor.secondaryLabelColor())
        self.status.setStringValue_("Back to its usual place")
        self.performSelector_withObject_afterDelay_(
            "_clearStatus:", None, 2.0)

    def _clearStatus_(self, ignored):
        self._resetStatus()

    def _centerOnActiveScreen(self):
        visible = self._activeScreen().visibleFrame()
        x = visible.origin.x + (visible.size.width - PANEL_W) / 2.0
        y = visible.origin.y + (visible.size.height - PANEL_H) / 2.0
        self.panel.setFrame_display_(
            NSMakeRect(x, y, PANEL_W, PANEL_H), False)

    def hide(self):
        defaults().setObject_forKey_(
            NSStringFromRect(self.panel.frame()), self.frameKey())
        self.panel.orderOut_(None)
        self._restoreFocus()

    def _restoreFocus(self):
        """Give the keyboard back to whatever was in front.

        Without this the picker's own (invisible, LSUIElement) application
        stays active after the panel closes, and the Cmd-V the user is about
        to press goes nowhere.
        """
        app = self.previous_app
        self.previous_app = None
        if app is not None and not app.isTerminated():
            app.activateWithOptions_(0)
        else:
            NSApp.hide_(None)

    def windowDidBecomeKey_(self, note):
        self._was_key = True

    def windowDidResignKey_(self, note):
        # Click-away dismissal, but only once the panel has genuinely held
        # focus.  A resign that arrives before it ever became key is the
        # activation settling, not the user clicking somewhere else.
        if not (self.panel.isVisible() and getattr(self, "_was_key", False)
                and not getattr(self, "_modal", False)
                and not getattr(self, "_yielding", False)):
            return
        # Losing key to one of OUR OWN windows — Preferences, the help — is
        # not clicking away. Which window is taking over is not known yet at
        # resign time, so the decision waits one turn of the run loop.
        self.performSelector_withObject_afterDelay_("_hideUnlessOurs:",
                                                    None, 0.0)

    def _hideUnlessOurs_(self, ignored):
        if not self.panel.isVisible():
            return
        # _modal is set while one of our own windows is up. Asking
        # NSApp.keyWindow() instead looked obvious and is not reliable: at
        # the moment a resign is delivered the replacement may not be key
        # yet, and it reads as nothing at all.
        if getattr(self, "_modal", False) or getattr(self, "_yielding", False):
            return
        self.hide()

    def holdOpen(self):
        """One of our own windows is taking focus — do not dismiss."""
        self._modal = True

    def releaseHold(self):
        self._modal = False

    def windowWillClose_(self, note):
        self._restoreFocus()

    def cancelOperation_(self, sender):        # Esc
        self.hide()

    def clipResized_(self, note):
        self.grid.relayout()

    # -- content ----------------------------------------------------------

    def hasQuery(self):
        return bool(self.search.stringValue())

    def selectedKindIndex(self):
        return (self.filter.indexOfSelectedItem()
                if getattr(self, "compact_filter", False)
                else self.filter.selectedSegment())

    def selectKindIndex_(self, index):
        index = int(index)
        if not 0 <= index < len(FILTER_KINDS):
            return
        if getattr(self, "compact_filter", False):
            self.filter.selectItemAtIndex_(index)
        else:
            self.filter.setSelectedSegment_(index)

    def currentKind(self):
        index = self.selectedKindIndex()
        if 0 <= index < len(FILTER_KINDS):
            return FILTER_KINDS[index][1]
        return None

    def _layoutHeader(self):
        """Place the header by measurement, not by fixed columns.

        The chips carry counts, so their width changes as clippings come and
        go, and the panel is used both as a wide strip and as an 820pt grid.
        Fixed columns collided in the narrow case: status, five chips, help
        and search want about 950pt and the grid has 820. So the chips are
        sized to their labels, search and help are pinned to the right, and
        the status line takes whatever is left.
        """
        width = self.header.frame().size.width
        if getattr(self, "compact_filter", False):
            # Row one: the search field, full width. Row two: the filter and
            # what is left of the status line, with help on the right.
            if self.brand is not None:
                self.brand.sizeToFit()
                bw = min(self.brand.frame().size.width, width - 24)
                self.brand.setFrame_(NSMakeRect(12, 74, bw, 16))
                self.copyright.setFrame_(
                    NSMakeRect(12 + bw + 6, 74,
                               max(20, width - 24 - bw - 6), 16))
            self.search.setFrame_(NSMakeRect(12, 42, max(80, width - 24), 26))
            # Sized to its own title rather than a guessed 132: at the small
            # card size the column is 230pt wide, and a fixed popup left the
            # status line 40pt, which truncated "2 visible" to "2".
            self.filter.sizeToFit()
            # width-130 rather than width-96: at the small card size a
            # 230pt column left the status 42pt for 43pt of text, which
            # is the same truncation one cap looser.
            menu_w = min(max(78.0, self.filter.frame().size.width),
                         max(78.0, width - 130))
            self.filter.setFrame_(NSMakeRect(12, 8, menu_w, 25))
            self.help_button.setFrame_(NSMakeRect(width - 12 - 26, 9, 26, 24))
            left = 12 + menu_w + 8
            self.status.setFrame_(
                NSMakeRect(left, 12, max(30, width - left - 46), 18))
            return
        self.filter.sizeToFit()
        chips_w = self.filter.frame().size.width
        search_x = width - 12 - SEARCH_W
        help_x = search_x - 34
        chips_x = min(FILTER_X, help_x - 12 - chips_w)
        chips_x = max(12 + 90, chips_x)     # never crowd the status out
        self.search.setFrame_(NSMakeRect(search_x, 8, SEARCH_W, 26))
        self.help_button.setFrame_(NSMakeRect(help_x, 9, 26, 24))
        self.filter.setFrame_(NSMakeRect(chips_x, 9, chips_w, 24))
        self.status.setFrame_(
            NSMakeRect(12, 12, max(60, chips_x - 24), 18))

    def reload(self):
        query = str(self.search.stringValue() or "")
        items = self.app.store.items(query=query, kind=self.currentKind())
        self.grid.setItems_(items)
        self.grid.scrollSelectionIntoView()
        self._refreshChips_(query)
        total = self.app.store.count()
        shown = len(items)
        self._resetStatus(shown, total)

    def _refreshChips_(self, query):
        """Each chip says how many of that kind EXIST.

        They used to answer under the search in force, which made every
        number move as you typed — so a chip could not be used to decide
        where to look, which is the only reason to put a number on it. How
        many the search left is a different fact, and belongs in the status
        line, which says so.
        """
        try:
            counts = self.app.store.counts("")
        except Exception:
            return
        titles = ["%s (%d)" % (label, counts.get(kind or "all", 0))
                  for label, kind in FILTER_KINDS]
        if getattr(self, "compact_filter", False):
            # Rebuilding the menu loses the selection, so it is put back.
            chosen = self.filter.indexOfSelectedItem()
            self.filter.removeAllItems()
            self.filter.addItemsWithTitles_(titles)
            if 0 <= chosen < len(titles):
                self.filter.selectItemAtIndex_(chosen)
        else:
            for i, title in enumerate(titles):
                self.filter.setLabel_forSegment_(title, i)
        self._layoutHeader()

    def _resetStatus(self, shown=None, total=None):
        if total is None:
            total = self.app.store.count()
        if shown is None:
            shown = len(self.grid.items())
        note = "%d visible of %d" % (shown, total) if shown != total else \
            "%d item%s" % (total, "" if total == 1 else "s")
        self.status.setTextColor_(NSColor.secondaryLabelColor())
        full = ("%s  ·  %s  ·  reopen with %s"
                % (note, _human_bytes(self.app.store.disk_bytes()),
                   hotkey_label(pref(DEF_HOTKEY_CODE), pref(DEF_HOTKEY_MODS))))
        # The reopen chord is a first-run nicety that was being paid for on
        # every view: with it the line wants 247pt and even the strip only
        # ever offered 155, so it had been silently truncated since the
        # search field moved right. It lives in the tooltip and in the help.
        if getattr(self, "compact_filter", False):
            # "of N" goes too — the All chip beside it carries the total.
            short = ("%d visible" % shown) if shown != total else note
        else:
            short = "%s  ·  %s" % (note,
                                   _human_bytes(self.app.store.disk_bytes()))
        self.status.setStringValue_(short)
        self.status.setToolTip_(full)

    def showHelp_(self, sender):
        self.app.showHelp()

    def searchChanged_(self, sender):
        self.reload()

    def controlTextDidChange_(self, note):
        self.reload()

    def filterChanged_(self, sender):
        self.reload()
        self.panel.makeFirstResponder_(self.grid)

    # -- grid delegate ----------------------------------------------------

    def gridDidActivate_(self, item):
        """Copy, say so, and KEEP the keyboard.

        This used to hand focus straight back to the application behind, so
        that ⌘V worked without another click — but that meant the panel went
        quiet under the cursor while it was still on screen, and a second
        pick or a search needed a click to wake it.  Focus now stays here
        until the panel is closed, and closing still returns it to whatever
        had it before, so the flow is: pick, Esc, ⌘V.
        """
        self.app.copyToPasteboard_(item)
        self._announceCopied_(item)

    def _announceCopied_(self, item):
        what = ("that image" if item.kind == "image"
                else "“%s”" % _menu_title(item))
        self.status.setTextColor_(NSColor.controlAccentColor())
        self.status.setStringValue_("✓  %s is on the clipboard — ⌘V to paste"
                                    % what)
        if self._flash is not None:
            self._flash.invalidate()
        self._flash = NSTimer.\
            scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                4.0, self, "clearFlash:", None, False)

    def clearFlash_(self, timer):
        """Put the status line back — WITHOUT rebuilding the list.

        reload() re-sorts, and picking a clipping has just bumped it to the
        front, so rebuilding here slid the card out from under the pointer
        seconds after it was clicked.  The new order is correct; it just
        should not arrive as a surprise mid-use.
        """
        self._flash = None
        if self.panel.isVisible():
            self._resetStatus()

    def _yieldFocus(self):
        """Give the keyboard back without closing.

        NOT CALLED as of 1.10.0 — picking a clipping keeps focus here now.
        Kept because the _yielding flag it sets is what stops the resign-key
        handler treating a focus change we caused as a click-away.

        The panel hides itself when it loses key, which is how clicking away
        dismisses it — so a focus change WE cause has to be marked, or the
        strip would vanish the moment it handed the keyboard back.
        """
        app = self.previous_app
        if app is None or app.isTerminated():
            return
        self._yielding = True
        app.activateWithOptions_(0)
        NSTimer.\
            scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.8, self, "endYield:", None, False)

    def endYield_(self, timer):
        self._yielding = False

    def gridDidDelete_(self, chosen):
        """Delete what is selected — except anything pinned.

        A pinned clipping cannot be deleted at all while it is pinned. It
        used to be deletable behind a confirmation, but a confirmation is
        the wrong shape for this: it puts the decision in the same keystroke
        as the mistake. Unpinning is now the deliberate act that makes a
        clipping deletable, and it is one menu item away.
        """
        if not isinstance(chosen, (list, tuple)):
            chosen = [chosen]
        # Ask the STORE whether each one is pinned, not the card. A card
        # carries the pinned flag it was built with, and pinning does not
        # rebuild the list — so a card pinned a moment ago still says it is
        # loose, and deleting through it would destroy exactly what pinning
        # was supposed to protect.
        fresh = []
        for item in chosen:
            current = None
            try:
                current = self.app.store.get(item.id)
            except Exception:
                current = None
            fresh.append(current if current is not None else item)
        pinned = [i for i in fresh if i.pinned]
        loose = [i for i in fresh if not i.pinned]
        if not loose:
            self._refusePinned_(pinned)
            return
        if len(loose) > 1 and not self._confirmMany_(len(loose)):
            return
        self.app.store.delete([i.id for i in loose])
        self.reload()
        if pinned:
            # Say what was left behind, rather than letting the count come
            # out lower than expected with no explanation.
            self.status.setTextColor_(NSColor.secondaryLabelColor())
            self.status.setStringValue_(
                "Deleted %d  ·  kept %d pinned — unpin to delete"
                % (len(loose), len(pinned)))

    def _refusePinned_(self, pinned):
        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(1)                       # informational
        if len(pinned) == 1:
            alert.setMessageText_("“%s” is pinned" % _menu_title(pinned[0]))
            alert.setInformativeText_(
                "A pinned clipping cannot be deleted while it is pinned — "
                "that is what has been keeping it out of the way of the item "
                "limit, the age limit and Clear History.\n\n"
                "Unpin it first (right-click the card, or ⌘-click it and "
                "choose Unpin), then delete it as usual.")
        else:
            alert.setMessageText_("%d pinned clippings" % len(pinned))
            alert.setInformativeText_(
                "Pinned clippings cannot be deleted while they are pinned. "
                "Unpin them first, then delete them as usual.")
        alert.addButtonWithTitle_("OK")
        icon = own_icon()
        if icon is not None:
            alert.setIcon_(icon)
        self._runModal_(alert)

    def _confirmMany_(self, count):
        """Several at once, with nothing to undo it with, is worth asking."""
        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(2)                       # warning
        alert.setMessageText_("Delete %d clippings?" % count)
        alert.setInformativeText_("This cannot be undone.")
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        # Delete is the default, at Tim's request: added first, so it is
        # rightmost, blue, and takes Return.  Cancel keeps Escape, which
        # NSAlert gives it for its title.  The earlier arrangement moved
        # Return onto Cancel so a stray keystroke could not delete a batch —
        # safer, but it put the blue button on the one that does nothing.
        icon = own_icon()
        if icon is not None:
            alert.setIcon_(icon)
        return self._runModal_(alert) == 1000

    def _runModal_(self, alert):
        # A modal alert takes key away from the picker, and the picker hides
        # itself when it loses key — it would vanish behind its own alert.
        self._modal = True
        try:
            NSApp.activateIgnoringOtherApps_(True)
            return alert.runModal()
        finally:
            self._modal = False

    def thumbnailRebuilt_name_(self, item, name):
        self.app.store.set_thumb(item.id, name)

    def gridDidType_(self, event):
        self.panel.makeFirstResponder_(self.search)
        self.search.currentEditor().keyDown_(event)

    def gridDidCancel(self):
        self.hide()

    def gridDidAskToReset(self):
        self.resetPosition_(None)

    def gridDidAskForHelp(self):
        self.app.showHelp()

    def gridDidPreview_(self, item):
        # NOT reached from Space since 1.16.0 — real Quick Look replaced
        # it — but kept, because "Open in Preview" in the context menu is
        # the only path that forces Preview specifically rather than
        # whatever heavyweight editor happens to own PNGs on this Mac.
        if item.kind == "image" and item.blob_path:
            open_in_preview(item.blob_path)
        else:
            self.gridDidActivate_(item)

    def menuForItem_(self, item):
        self._menu_item = item
        menu = NSMenu.alloc().initWithTitle_("Item")
        def add(title, selector, enabled=True):
            mi = menu.addItemWithTitle_action_keyEquivalent_(
                title, selector, "")
            mi.setTarget_(self)
            mi.setEnabled_(enabled)
        add("Quick Look", "menuQuickLook:")
        menu.addItem_(NSMenuItem.separatorItem())
        add("Copy", "menuCopy:")
        if item.kind == "image" and item.body:
            add("Copy Text From This Capture", "menuCopyAlt:")
        menu.addItem_(NSMenuItem.separatorItem())

        # A link opens as a LINK. Writing it to a .txt and opening that
        # showed the browser a file:// page with the URL printed on it,
        # which is not what anyone means by opening a URL.
        link = item.url()
        self._menu_url = link
        path = openable_path(item)
        self._menu_path = path
        # Name the item after the application that will actually open it.
        # "Open in Preview" was wrong for anyone whose default image app is
        # something else, which on this Mac is Pixelmator Pro.
        opener = (_default_browser_name(link) if link
                  else _default_app_name(path))
        add("Open in %s" % opener if opener else "Open", "menuOpen:",
            link is not None or path is not None)
        if item.kind == "image" and opener != "Preview" \
                and _preview_app() is not None:
            add("Open in Preview", "menuPreview:", path is not None)

        candidates = apps_for_url(link) if link else apps_for(path)
        with_item = menu.addItemWithTitle_action_keyEquivalent_(
            "Open With", None, "")
        submenu = NSMenu.alloc().initWithTitle_("Open With")
        self._menu_apps = {}
        for index, (name, url) in enumerate(candidates):
            entry = submenu.addItemWithTitle_action_keyEquivalent_(
                name, "menuOpenWith:", "")
            entry.setTarget_(self)
            entry.setTag_(index)
            self._menu_apps[index] = url
        if candidates:
            submenu.addItem_(NSMenuItem.separatorItem())
        other = submenu.addItemWithTitle_action_keyEquivalent_(
            "Other…", "menuOpenOther:", "")
        other.setTarget_(self)
        menu.setSubmenu_forItem_(submenu, with_item)
        with_item.setEnabled_(link is not None or path is not None)

        add("Reveal in Finder", "menuReveal:", path is not None)
        # Editing in place is offered only for PINNED clippings: an unpinned
        # one is subject to the item cap and the age cap, so the edit would
        # be work the retention sweep deletes later.
        if item.kind == "text":
            add("Edit…" if item.pinned else "Edit… (pin it first)",
                "menuEdit:", bool(item.pinned))
        else:
            add("Update From Clipboard"
                if item.pinned else "Update From Clipboard (pin it first)",
                "menuUpdateImage:", bool(item.pinned))
        menu.addItem_(NSMenuItem.separatorItem())
        add("Unpin" if item.pinned else "Pin", "menuPin:")
        add("Delete", "menuDelete:")
        return menu

    def menuCopy_(self, sender):
        self.gridDidActivate_(self._menu_item)

    def menuCopyAlt_(self, sender):
        self.app.copyStringToPasteboard_(self._menu_item.body or "")
        self._announceCopied_(self._menu_item)

    def menuOpen_(self, sender):
        if getattr(self, "_menu_url", None):
            NSWorkspace.sharedWorkspace().openURL_(
                NSURL.URLWithString_(self._menu_url))
        elif self._menu_path:
            NSWorkspace.sharedWorkspace().openURL_(
                NSURL.fileURLWithPath_(self._menu_path))

    def menuPreview_(self, sender):
        if self._menu_path:
            open_in_preview(self._menu_path)

    def menuOpenWith_(self, sender):
        app = self._menu_apps.get(int(sender.tag()))
        if getattr(self, "_menu_url", None):
            open_url_with(self._menu_url, app)
        elif self._menu_path:
            open_with(self._menu_path, app)

    def menuOpenOther_(self, sender):
        """Pick any application, the way the Finder's Other… does."""
        if not (self._menu_path or getattr(self, "_menu_url", None)):
            return
        path, link = self._menu_path, getattr(self, "_menu_url", None)
        self.hide()
        panel = NSOpenPanel.openPanel()
        panel.setTitle_("Choose an application")
        panel.setPrompt_("Open")
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setTreatsFilePackagesAsDirectories_(False)
        panel.setAllowedFileTypes_(["app"])
        panel.setDirectoryURL_(NSURL.fileURLWithPath_("/Applications"))
        NSApp.activateIgnoringOtherApps_(True)
        if panel.runModal() == 1 and panel.URLs():
            if link:
                open_url_with(link, panel.URLs()[0])
            else:
                open_with(path, panel.URLs()[0])

    def menuReveal_(self, sender):
        if self._menu_path:
            NSWorkspace.sharedWorkspace().\
                activateFileViewerSelectingURLs_(
                    [NSURL.fileURLWithPath_(self._menu_path)])

    def menuQuickLook_(self, sender):
        """Quick Look, on the card the menu was opened on."""
        item = self._menu_item
        if item is None:
            return
        for index, other in enumerate(self.grid.items()):
            if other.id == item.id:
                self.grid._selectOnly_(index)
                self.grid.setNeedsDisplay_(True)
                break
        self.panel.makeFirstResponder_(self.grid)
        self.grid.toggleQuickLook()

    def menuEdit_(self, sender):
        item = self._menu_item
        if item is None or item.kind != "text" or not item.pinned:
            return
        self.holdOpen()
        self._editor = EditorController.alloc().initWithPicker_item_(self, item)
        self._editor.show()

    def menuUpdateImage_(self, sender):
        """Replace a pinned image with whatever is on the clipboard now.

        This is the other half of "Open in Pixelmator": the round trip used
        to end with a SECOND clipping, because copying the edit back is an
        ordinary pasteboard write and the watcher records it like any other.
        Worse, at card size a small change is invisible, so the pinned
        original looked as though it had been updated when it had not.
        """
        item = self._menu_item
        if item is None or item.kind != "image" or not item.pinned:
            return
        png, width, height = png_from_pasteboard(
            NSPasteboard.generalPasteboard())
        if not png:
            self.holdOpen()
            _alert("No image on the clipboard",
                   "Copy the edited picture first — in most editors that is "
                   "⌘C, or ⇧⌘C for the flattened image — then choose Update "
                   "From Clipboard again.")
            self.releaseHold()
            return
        if self.app.store.replace_image(item.id, png, width, height):
            self.reload()
            self.status.setTextColor_(NSColor.secondaryLabelColor())
            self.status.setStringValue_("Updated from the clipboard")
            self.performSelector_withObject_afterDelay_(
                "_clearStatus:", None, 2.5)

    def menuPin_(self, sender):
        """Pin or unpin — and stay with the clipping when it moves.

        Unpinning re-sorts it out of the front, and if the Pinned chip is
        the one in force it leaves the list altogether.  Since unpinning is
        now the step before deleting, losing sight of the card at exactly
        that moment is the worst possible time, so the filter falls back to
        All and the card stays selected and in view.
        """
        unpinning = bool(self._menu_item.pinned)
        self.app.store.set_pinned(self._menu_item.id, not unpinning)
        if unpinning and self.currentKind() == "pinned":
            self.selectKindIndex_(0)                    # All
        self.reload()

    def menuDelete_(self, sender):
        # The context menu acts on the whole selection when the card it
        # was opened on is part of one.
        chosen = self.grid.selectedItems()
        if self._menu_item not in chosen:
            chosen = [self._menu_item]
        self.gridDidDelete_(chosen)


def openable_path(item):
    """A real file for a clipping, so any application can be pointed at it.

    Images already are files.  Text lives in the database, so it is written
    out to exports/ on demand — a stable name per clipping, rewritten each
    time, rather than a litter of temporary files.
    """
    if item.kind == "image":
        return item.blob_path if item.blob_path and \
            os.path.exists(item.blob_path) else None
    text = item.body or item.preview or ""
    path = os.path.join(EXPORT_DIR, "clipping-%d.txt" % item.id)
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError:
        return None
    return path


def apps_for(path):
    """Every application that says it can open this file, best first."""
    if not path:
        return []
    urls = NSWorkspace.sharedWorkspace().URLsForApplicationsToOpenURL_(
        NSURL.fileURLWithPath_(path)) or []
    seen, out = set(), []
    for url in urls:
        name = os.path.splitext(os.path.basename(str(url.path())))[0]
        if name not in seen:
            seen.add(name)
            out.append((name, url))
    return out


def apps_for_url(link):
    """Every application that says it can open this LINK, best first —
    browsers, not text editors. Asking with the file the URL was written to
    produced a list of editors, which is how "Open With" came to offer
    Emacs for a web page."""
    if not link:
        return []
    url = NSURL.URLWithString_(link)
    if url is None:
        return []
    urls = NSWorkspace.sharedWorkspace().URLsForApplicationsToOpenURL_(url) or []
    seen, out = set(), []
    for app in urls:
        name = os.path.splitext(os.path.basename(str(app.path())))[0]
        if name not in seen:
            seen.add(name)
            out.append((name, app))
    return out


def open_url_with(link, app_url):
    """Open a link, optionally in one specific application."""
    url = NSURL.URLWithString_(link)
    if url is None:
        return
    if app_url is None:
        NSWorkspace.sharedWorkspace().openURL_(url)
        return
    NSWorkspace.sharedWorkspace().\
        openURLs_withApplicationAtURL_configuration_completionHandler_(
            [url], app_url, NSWorkspaceOpenConfiguration.configuration(), None)


def _default_browser_name(link):
    """Whatever would open this link if it were clicked."""
    if not link:
        return None
    url = NSURL.URLWithString_(link)
    if url is None:
        return None
    app = NSWorkspace.sharedWorkspace().URLForApplicationToOpenURL_(url)
    if app is None:
        return None
    return os.path.splitext(os.path.basename(str(app.path())))[0]


def open_with(path, app_url):
    """Open a clipping with one specific application."""
    if app_url is None:
        NSWorkspace.sharedWorkspace().openURL_(NSURL.fileURLWithPath_(path))
        return
    NSWorkspace.sharedWorkspace().\
        openURLs_withApplicationAtURL_configuration_completionHandler_(
            [NSURL.fileURLWithPath_(path)], app_url,
            NSWorkspaceOpenConfiguration.configuration(), None)


def _default_app_name(path):
    """The application that would open `path` if it were double-clicked."""
    if not path or not os.path.exists(path):
        return None
    url = NSWorkspace.sharedWorkspace().URLForApplicationToOpenURL_(
        NSURL.fileURLWithPath_(path))
    if url is None:
        return None
    return os.path.splitext(os.path.basename(str(url.path())))[0]


def _preview_app():
    return NSWorkspace.sharedWorkspace().\
        URLForApplicationWithBundleIdentifier_("com.apple.Preview")


def open_in_preview(path):
    """Open a clipping in Preview specifically, whatever the default is."""
    open_with(path, _preview_app())


def _human_bytes(n):
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.0f %s" % (n, unit) if unit == "bytes" \
                else "%.1f %s" % (n, unit)
        n /= 1024.0


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

class EditorController(NSObject):
    """A plain editor for one PINNED text clipping, saving in place.

    Pinned only, and the restriction is the point rather than a limitation:
    a pinned clipping is exempt from the item cap, the age cap and Clear
    History, so it is the only kind where editing is not work the retention
    sweep will quietly delete later.
    """

    def initWithPicker_item_(self, picker, item):
        self = objc.super(EditorController, self).init()
        if self is None:
            return None
        self.picker = picker
        self.item_id = item.id
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 560, 420),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
            NSWindowStyleMaskResizable | NSWindowStyleMaskUtilityWindow,
            NSBackingStoreBuffered, False)
        panel.setTitle_("Edit clipping")
        panel.setReleasedWhenClosed_(False)
        panel.setDelegate_(self)
        panel.setMinSize_(NSMakeSize(360, 240))
        content = panel.contentView()
        size = content.bounds().size

        scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(12, 52, size.width - 24, size.height - 64))
        scroll.setHasVerticalScroller_(True)
        scroll.setBorderType_(2)                       # bezel
        scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        text = NSTextView.alloc().initWithFrame_(scroll.bounds())
        text.setEditable_(True)
        text.setRichText_(False)
        text.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0.0))
        text.setString_(item.body or item.preview or "")
        text.setAutoresizingMask_(NSViewWidthSizable)
        scroll.setDocumentView_(text)
        content.addSubview_(scroll)
        self.text = text

        save = NSButton.alloc().initWithFrame_(
            NSMakeRect(size.width - 12 - 96, 12, 96, 30))
        save.setTitle_("Save")
        save.setBezelStyle_(1)
        save.setKeyEquivalent_("\r")
        save.setTarget_(self)
        save.setAction_("save:")
        save.setAutoresizingMask_(NSViewMinXMargin)
        content.addSubview_(save)

        cancel = NSButton.alloc().initWithFrame_(
            NSMakeRect(size.width - 12 - 96 - 8 - 90, 12, 90, 30))
        cancel.setTitle_("Cancel")
        cancel.setBezelStyle_(1)
        cancel.setKeyEquivalent_("\033")               # esc
        cancel.setTarget_(self)
        cancel.setAction_("cancel:")
        cancel.setAutoresizingMask_(NSViewMinXMargin)
        content.addSubview_(cancel)

        self.panel = panel
        return self

    def show(self):
        self.panel.center()
        self.panel.makeKeyAndOrderFront_(None)
        self.panel.makeFirstResponder_(self.text)
        NSApp.activateIgnoringOtherApps_(True)

    def save_(self, sender):
        self.picker.app.store.set_body(self.item_id,
                                       str(self.text.string() or ""))
        self.panel.orderOut_(None)
        self.picker.releaseHold()
        self.picker.reload()

    def cancel_(self, sender):
        self.panel.orderOut_(None)
        self.picker.releaseHold()

    def windowWillClose_(self, note):
        self.picker.releaseHold()


class HelpTextView(NSTextView):
    """The help text, which answers the zoom keys like a document would.

    NSTextView only scales for a real text system; this is a read-only
    display, so the keys are caught here and the body is rebuilt at the new
    size instead. Rebuilding rather than applying a view-wide scale keeps
    the monospaced key names crisp.
    """

    controller = None

    def keyDown_(self, event):
        if (event.modifierFlags() & NSEventModifierFlagCommand
                and self.controller is not None):
            char = (event.charactersIgnoringModifiers() or "")
            if char in ("+", "="):
                self.controller.zoomIn()
                return
            if char in ("-", "_"):
                self.controller.zoomOut()
                return
            if char == "0":
                self.controller.zoomReset()
                return
        objc.super(HelpTextView, self).keyDown_(event)


HELP_INTRO = (
    "Stache keeps everything you copy — text and pictures alike — with the "
    "time you copied it and the app you copied it from, and hands any of it "
    "back when you press the hotkey.\n\n"
    "The name is the joke. A stache is where you stash things, and the two "
    "words sound identical, so Stache is the place your clipboard gets "
    "stashed and recalled from. The moustaches on the icon are that pun made "
    "visible — and the Olde English S is Tim's own lettering."
)

HELP_SECTIONS = (
    ("Getting it open", (
        ("%s", "open the picker from anywhere"),
        ("menu bar S", "the same thing, plus the ten newest clippings"),
        ("⌘1 – ⌘9", "copy one of those straight from the menu"),
    )),
    ("Choosing a clipping", (
        ("click", "copy it and close — this is the whole point"),
        ("⌥click", "select it without copying, to look without disturbing "
                   "the clipboard"),
        ("↵", "copy the selected clipping and close"),
        ("← → ↑ ↓", "move the selection"),
        ("Space", "Quick Look the selected clipping — text or image. The arrow keys keep working, and the preview follows them"),
        ("⌫", "delete the selected clipping for good"),
        ("right-click", "Quick Look · Copy · Open · Open With ▸ · Reveal in Finder · "
                        "Pin · Delete"),
        ("⌘0", "put the picker back where it calculated it belonged, "
                "forgetting where it was dragged"),
        ("esc", "close, clipboard untouched"),
    )),
    ("Finding one", (
        ("just type", "it goes to the search field"),
        ("safari", "everything copied out of Safari"),
        ("today", "also yesterday, this week, last week, this month"),
        ("aug", "or august, or friday"),
        ("8/28", "or 2026-08-28, or 2026, or 12:55 pm"),
        ("All / Pinned / Images / Text / URL",
         "narrow it by kind; each chip carries its own count"),
    )),
    ("Changing one", (
        ("Open", "a link opens in your browser; anything else opens as a "
                 "file, in whichever application handles it"),
        ("Edit…", "rewrite a PINNED text clipping in place. Only pinned "
                  "ones: an unpinned clipping is subject to the item and "
                  "age limits, so the edit would not last"),
        ("Update From Clipboard",
         "replace a PINNED image with whatever is on the clipboard — the "
         "other half of opening it in an editor. Copying an edit back on "
         "its own makes a NEW clipping instead, leaving the original pinned"),
        ("edited", "appears beside the date once a clipping has been "
                   "changed, so a card never claims to be a verbatim "
                   "capture when it is not"),
    )),
    ("Keeping things", (
        ("kept alive", "the age limit counts from the last time you used a "
                       "clipping, so anything you keep reaching for never "
                       "ages out; a card in the last tenth of its life says "
                       "so in red"),
        ("Pin", "pinned clippings sort first and survive the item limit, "
                "the age limit and Clear History — and cannot be deleted at "
                "all until they are unpinned"),
        ("⇧click / ⌘click", "select a range, or add and remove one card at "
                            "a time; ⌫ then deletes all of them"),
        ("⌘+ / ⌘− / ⌘0", "in this window: bigger text, smaller text, "
                            "back to normal"),
        ("Strip / Column / Grid",
         "a row along the bottom, a column up the left edge, or a window of "
         "rows. Drag any of them anywhere and resize them — the place is "
         "remembered, and ⌘0 undoes it"),
        ("Preferences", "card size, layout, strip width, hotkey, how much "
                        "history to keep, open at login"),
        ("in the shell", "`stache` lists it, `stache copy 3` recalls it"),
    )),
    ("What is never recorded", (
        ("passwords", "anything a password manager copies is flagged and "
                      "skipped"),
        ("paused", "whatever arrives while Pause Capturing is on"),
        ("its own writes", "picking a clipping does not make a copy of it"),
    )),
)


class HelpController(NSObject):
    """A plain window of prose and key bindings.

    Deliberately a window rather than an overlay on the picker: the strip is
    one card tall, and help that has to be scrolled in a letterbox is help
    nobody reads.
    """

    def initWithApp_(self, app):
        self = objc.super(HelpController, self).init()
        if self is None:
            return None
        self.app = app
        self._build()
        return self

    def _build(self):
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 620, 640),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
            NSWindowStyleMaskResizable | NSWindowStyleMaskUtilityWindow,
            NSBackingStoreBuffered, False)
        panel.setTitle_("About Stache")
        panel.setDelegate_(self)
        panel.setReleasedWhenClosed_(False)
        panel.setMinSize_(NSMakeSize(460, 360))

        scroll = NSScrollView.alloc().initWithFrame_(
            panel.contentView().bounds())
        scroll.setHasVerticalScroller_(True)
        scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        scroll.setDrawsBackground_(True)

        text = HelpTextView.alloc().initWithFrame_(scroll.bounds())
        text.controller = self
        text.setEditable_(False)
        text.setSelectable_(True)
        text.setAutoresizingMask_(NSViewWidthSizable)
        text.setTextContainerInset_(NSMakeSize(24, 22))
        text.textStorage().setAttributedString_(self._body())
        scroll.setDocumentView_(text)
        panel.contentView().addSubview_(scroll)
        self.panel = panel
        self.text = text

    def windowWillClose_(self, note):
        picker = getattr(self.app, "picker", None) if self.app else None
        if picker is not None:
            picker.releaseHold()

    def scale(self):
        try:
            return max(0.6, min(2.5, int(pref(DEF_HELP_SCALE)) / 100.0))
        except (TypeError, ValueError):
            return 1.0

    def zoomIn(self):
        self._setScale_(int(pref(DEF_HELP_SCALE)) + 10)

    def zoomOut(self):
        self._setScale_(int(pref(DEF_HELP_SCALE)) - 10)

    def zoomReset(self):
        self._setScale_(100)

    def _setScale_(self, percent):
        percent = max(60, min(250, int(percent)))
        if percent == pref(DEF_HELP_SCALE):
            return
        set_pref(DEF_HELP_SCALE, percent)
        # Rebuilt rather than scaled: every run carries its own font, and a
        # view-wide scale factor would blur the monospaced key names.
        self.text.textStorage().setAttributedString_(self._body())

    def _body(self):
        from Foundation import NSMutableAttributedString
        z = self.scale()
        body = NSMutableAttributedString.alloc().init()

        def add(string, font, colour, space_after=0.0, indent=0.0):
            para = NSMutableParagraphStyle.alloc().init()
            para.setParagraphSpacing_(space_after)
            para.setHeadIndent_(indent)
            para.setFirstLineHeadIndent_(indent)
            para.setLineSpacing_(1.5)
            body.appendAttributedString_(
                NSAttributedString.alloc().initWithString_attributes_(
                    string, {NSFontAttributeName: font,
                             NSForegroundColorAttributeName: colour,
                             NSParagraphStyleAttributeName: para}))

        add("Stache %s\n" % APP_VERSION,
            NSFont.boldSystemFontOfSize_(22 * z), NSColor.labelColor(), 4)
        add("clipboard history for macOS\n\n",
            NSFont.systemFontOfSize_(13 * z), NSColor.secondaryLabelColor(), 10)
        add(HELP_INTRO + "\n\n",
            NSFont.systemFontOfSize_(13 * z), NSColor.labelColor(), 14)

        chord = hotkey_label(pref(DEF_HOTKEY_CODE), pref(DEF_HOTKEY_MODS))
        for heading, rows in HELP_SECTIONS:
            add(heading + "\n",
                NSFont.boldSystemFontOfSize_(14 * z), NSColor.labelColor(), 6)
            for key, meaning in rows:
                add((key % chord if "%s" in key else key) + "\n",
                    NSFont.monospacedSystemFontOfSize_weight_(12 * z, 0.3),
                    NSColor.labelColor(), 0, 0)
                add(meaning + "\n",
                    NSFont.systemFontOfSize_(12.5 * z),
                    NSColor.secondaryLabelColor(), 8, 22)
            add("\n", NSFont.systemFontOfSize_(6 * z), NSColor.labelColor(), 6)

        add("Clippings live in ~/Library/Application Support/Stache — a "
            "SQLite index, and one ordinary PNG per picture. Nothing leaves "
            "this Mac.\n\n"
            "© 2026 Tim McCoy.",
            NSFont.systemFontOfSize_(11.5 * z), NSColor.tertiaryLabelColor())
        return body

    def show(self):
        self.text.textStorage().setAttributedString_(self._body())
        self.panel.center()
        self.panel.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class PrefsController(NSObject):
    """Hotkey, retention and login item, in one small panel."""

    def initWithApp_(self, app):
        self = objc.super(PrefsController, self).init()
        if self is None:
            return None
        self.app = app
        self._monitor = None
        self._build()
        return self

    def _build(self):
        """One column of rows, laid out from the top down.

        The measurements are derived rather than typed: adding a row used to
        mean nudging every number under it, and the Clear button ended up at
        y = -8, below the bottom edge of the panel.
        """
        rows = 9
        height = TOP_PAD + rows * ROW_H + BOTTOM_PAD
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, PREFS_W, height),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
            NSWindowStyleMaskUtilityWindow,
            NSBackingStoreBuffered, False)
        panel.setTitle_("Stache Preferences")
        panel.setDelegate_(self)
        panel.setReleasedWhenClosed_(False)
        view = panel.contentView()

        def row(n):
            """The baseline of row n, counting from the top."""
            return height - TOP_PAD - (n + 1) * ROW_H

        view.addSubview_(_right_label("Card size:", row(0) + 5))
        self.card_menu = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(FIELD_X, row(0), 160, 26), False)
        self.card_menu.addItemsWithTitles_(["Large", "Medium", "Small"])
        self.card_menu.setTarget_(self)
        self.card_menu.setAction_("cardSizeChanged:")
        view.addSubview_(self.card_menu)
        view.addSubview_(_plain("bigger thumbnails", FIELD_X + 168,
                                row(0) + 5, 180))

        view.addSubview_(_right_label("Layout:", row(1) + 5))
        self.layout_menu = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(FIELD_X, row(1), 160, 26), False)
        self.layout_menu.addItemsWithTitles_(["Strip", "Column", "Grid"])
        self.layout_menu.setTarget_(self)
        self.layout_menu.setAction_("layoutChanged:")
        view.addSubview_(self.layout_menu)
        view.addSubview_(_plain("one row, above the Dock", FIELD_X + 168,
                                row(1) + 5, 180))

        view.addSubview_(_right_label("Strip size:", row(2) + 4))
        self.strip_pct = NSTextField.alloc().initWithFrame_(
            NSMakeRect(FIELD_X, row(2) + 2, 70, 22))
        self.strip_pct.setTarget_(self)
        self.strip_pct.setAction_("stripWidthChanged:")
        view.addSubview_(self.strip_pct)
        view.addSubview_(_plain("% of the screen (wide, or tall in a column)",
                                FIELD_X + 78,
                                row(2) + 4, 190))

        view.addSubview_(_right_label("Hotkey:", row(3) + 5))
        self.hotkey_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(FIELD_X, row(3), 160, 28))
        self.hotkey_button.setBezelStyle_(1)
        self.hotkey_button.setTarget_(self)
        self.hotkey_button.setAction_("recordHotkey:")
        view.addSubview_(self.hotkey_button)
        view.addSubview_(_plain("click, then press the chord",
                                FIELD_X + 168, row(3) + 5, 180))

        view.addSubview_(_right_label("Keep at most:", row(4) + 4))
        self.max_items = NSTextField.alloc().initWithFrame_(
            NSMakeRect(FIELD_X, row(4) + 2, 70, 22))
        self.max_items.setTarget_(self)
        self.max_items.setAction_("retentionChanged:")
        view.addSubview_(self.max_items)
        view.addSubview_(_plain("items  (0 = no limit)", FIELD_X + 78,
                                row(4) + 4, 190))

        view.addSubview_(_right_label("Delete after:", row(5) + 4))
        self.max_days = NSTextField.alloc().initWithFrame_(
            NSMakeRect(FIELD_X, row(5) + 2, 70, 22))
        self.max_days.setTarget_(self)
        self.max_days.setAction_("retentionChanged:")
        view.addSubview_(self.max_days)
        view.addSubview_(_plain("days  (0 = never)", FIELD_X + 78,
                                row(5) + 4, 190))

        self.capture_images = _switch(
            "Capture images as well as text", row(6) + 4,
            self, "captureImagesChanged:")
        view.addSubview_(self.capture_images)


        self.login_item = _switch(
            "Open Stache at login", row(7) + 4, self, "loginItemChanged:")
        view.addSubview_(self.login_item)

        clear = NSButton.alloc().initWithFrame_(
            NSMakeRect(FIELD_X, BOTTOM_PAD - 8, 150, 30))
        clear.setTitle_("Clear History…")
        clear.setBezelStyle_(1)
        clear.setTarget_(self)
        clear.setAction_("clearHistory:")
        view.addSubview_(clear)

        version = _plain("Stache %s" % APP_VERSION, PREFS_W - 130,
                         BOTTOM_PAD - 2, 110)
        version.setAlignment_(1)
        version.setTextColor_(NSColor.tertiaryLabelColor())
        view.addSubview_(version)

        self.panel = panel

    def show(self):
        self.refresh()
        self.panel.center()
        self.panel.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    def refresh(self):
        self.hotkey_button.setTitle_(
            hotkey_label(pref(DEF_HOTKEY_CODE), pref(DEF_HOTKEY_MODS)))
        self.max_items.setStringValue_(str(pref(DEF_MAX_ITEMS)))
        self.max_days.setStringValue_(str(pref(DEF_MAX_DAYS)))
        self.capture_images.setState_(1 if pref(DEF_CAPTURE_IMAGES) else 0)
        self.login_item.setState_(1 if os.path.exists(AGENT_PLIST) else 0)
        self.layout_menu.selectItemAtIndex_(
            {"strip": 0, "column": 1, "grid": 2}.get(pref(DEF_LAYOUT), 0))
        self.card_menu.selectItemAtIndex_(
            {"large": 0, "medium": 1, "small": 2}.get(
                str(pref(DEF_CARD_SIZE)), 0))
        self.strip_pct.setStringValue_(str(pref(DEF_STRIP_PCT)))
        self.strip_pct.setEnabled_(pref(DEF_LAYOUT) != "grid")

    # -- actions ----------------------------------------------------------

    def recordHotkey_(self, sender):
        if self._monitor is not None:
            return
        self.hotkey_button.setTitle_("Press a chord…")

        def handler(event):
            mods = carbon_mods(event.modifierFlags())
            code = int(event.keyCode())
            if event.keyCode() in (54, 55, 56, 57, 58, 59, 60, 61, 62, 63):
                return None                       # a modifier on its own
            NSEvent.removeMonitor_(self._monitor)
            self._monitor = None
            if mods == 0:
                # A bare key would be claimed system-wide and swallowed from
                # every app on the Mac.  Refuse rather than break the keyboard.
                self.refresh()
                _alert("That chord needs a modifier",
                       "Hold at least one of ⌃ ⌥ ⇧ ⌘ along with the key. "
                       "A hotkey with no modifier would be taken away from "
                       "every other app.")
                return None
            set_pref(DEF_HOTKEY_CODE, code)
            set_pref(DEF_HOTKEY_MODS, mods)
            self.app.applyHotkey()
            self.refresh()
            return None

        self._monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown, handler)

    def retentionChanged_(self, sender):
        try:
            items = max(0, int(self.max_items.stringValue()))
            days = max(0, int(self.max_days.stringValue()))
        except ValueError:
            self.refresh()
            return
        set_pref(DEF_MAX_ITEMS, items)
        set_pref(DEF_MAX_DAYS, days)
        self.app.store.prune(items, days)
        self.refresh()

    def layoutChanged_(self, sender):
        chosen = ("strip", "column", "grid")[
            max(0, min(2, sender.indexOfSelectedItem()))]
        if chosen == pref(DEF_LAYOUT):
            return
        set_pref(DEF_LAYOUT, chosen)
        # Each arrangement is a different panel — different style limits,
        # scrollers and row logic — so the picker is rebuilt rather than
        # reconfigured in place.
        self.app.rebuildPicker()
        self.refresh()

    def windowWillClose_(self, note):
        picker = getattr(self.app, "picker", None) if self.app else None
        if picker is not None:
            picker.releaseHold()

    def cardSizeChanged_(self, sender):
        chosen = ("large", "medium", "small")[sender.indexOfSelectedItem()]
        if chosen == pref(DEF_CARD_SIZE):
            return
        set_pref(DEF_CARD_SIZE, chosen)
        apply_card_size()
        # The strip's height is a function of the card height, so the frame
        # saved at the old size no longer describes this panel.
        defaults().removeObjectForKey_(DEF_STRIP_FRAME)
        self.app.rebuildPicker()
        self.refresh()

    def stripWidthChanged_(self, sender):
        try:
            percent = max(20, min(100, int(sender.stringValue())))
        except ValueError:
            self.refresh()
            return
        set_pref(DEF_STRIP_PCT, percent)
        # Forget the remembered frame so the new width is actually used.
        defaults().removeObjectForKey_(DEF_STRIP_FRAME)
        self.refresh()

    def captureImagesChanged_(self, sender):
        set_pref(DEF_CAPTURE_IMAGES, bool(sender.state()))

    def loginItemChanged_(self, sender):
        if sender.state():
            install_login_item()
        else:
            remove_login_item()
        self.refresh()

    def clearHistory_(self, sender):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Clear the clipboard history?")
        alert.setInformativeText_(
            "Every unpinned clipping and its image file is deleted. "
            "This cannot be undone.")
        icon = own_icon()
        if icon is not None:
            alert.setIcon_(icon)
        alert.addButtonWithTitle_("Clear")
        alert.addButtonWithTitle_("Cancel")
        if alert.runModal() == 1000:
            self.app.store.clear(keep_pinned=True)
            self.app.picker.reload()


PREFS_W = 520
FIELD_X = 148
ROW_H = 32
TOP_PAD = 18
BOTTOM_PAD = 54          # room for Clear History under the last row


def _switch(title, y, target, action):
    box = NSButton.alloc().initWithFrame_(NSMakeRect(FIELD_X, y, 300, 20))
    box.setButtonType_(3)
    box.setTitle_(title)
    box.setTarget_(target)
    box.setAction_(action)
    return box


def _right_label(text, y, width=118):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, width, 18))
    f.setStringValue_(text)
    f.setEditable_(False)
    f.setBordered_(False)
    f.setDrawsBackground_(False)
    f.setAlignment_(1)                                      # right
    return f


def _plain(text, x, y, width):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 18))
    f.setStringValue_(text)
    f.setEditable_(False)
    f.setBordered_(False)
    f.setDrawsBackground_(False)
    f.setFont_(NSFont.systemFontOfSize_(11))
    f.setTextColor_(NSColor.secondaryLabelColor())
    return f


def _bar_label(text, align):
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 240, 16))
    field.setStringValue_(text)
    field.setBezeled_(False)
    field.setDrawsBackground_(False)
    field.setEditable_(False)
    field.setSelectable_(False)
    field.setFont_(NSFont.systemFontOfSize_(11))
    field.setTextColor_(NSColor.secondaryLabelColor())
    field.setAlignment_(align)
    field.sizeToFit()
    return field


def decorate_titlebar(window, compact=False):
    """Version on the left, name then icon in the centre, copyright right.

    Left and right are ordinary titlebar accessories.  The centre is NOT:
    an accessory can only be laid out left or right, and a represented URL
    would put the icon BEFORE the name.  Tim wants it after, so the centred
    piece is a plain view dropped into the titlebar's own container — the
    superview of the close button — kept centred by its margins rather than
    by a constraint.
    """
    # In a column the window is about 312pt wide. The traffic lights, the
    # version, the centred name and the copyright need well over that, and
    # they overlapped into an unreadable pile. The identity — name and icon
    # — is what earns the space; the version is in the help.
    accessories = () if compact else (
        ("v" + APP_VERSION, NSLayoutAttributeLeft, 0),
        (COPYRIGHT, NSLayoutAttributeRight, 2))
    for text, attribute, align in accessories:
        label = _bar_label(text, align)
        holder = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, label.frame().size.width + 16, 22))
        label.setFrameOrigin_(NSMakePoint(8, 3))
        holder.addSubview_(label)
        controller = NSTitlebarAccessoryViewController.alloc().init()
        controller.setView_(holder)
        controller.setLayoutAttribute_(attribute)
        window.addTitlebarAccessoryViewController_(controller)

    button = window.standardWindowButton_(NSWindowCloseButton)
    bar = button.superview() if button is not None else None
    if bar is None:
        return
    window.setTitleVisibility_(NSWindowTitleHidden)
    name = _bar_label(window.title(), 2)
    name.setFont_(NSFont.boldSystemFontOfSize_(13))
    name.setTextColor_(NSColor.labelColor())
    # Re-measure. _bar_label sized the field to fit 11pt regular; the text
    # is now 13pt BOLD and no longer fits the frame it was given, so the
    # name came out clipped.
    name.sizeToFit()
    icon = own_icon()
    icon_w = 16 if icon is not None else 0
    piece = NSView.alloc().initWithFrame_(
        NSMakeRect(0, 0, name.frame().size.width + icon_w + 6, 20))
    name.setFrameOrigin_(NSMakePoint(0, 2))
    piece.addSubview_(name)
    if icon is not None:
        well = NSImageView.alloc().initWithFrame_(
            NSMakeRect(name.frame().size.width + 6, 2, 16, 16))
        well.setImage_(icon)
        well.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        piece.addSubview_(well)
    size = bar.frame().size
    piece.setFrameOrigin_(NSMakePoint(
        round((size.width - piece.frame().size.width) / 2.0),
        round((size.height - piece.frame().size.height) / 2.0)))
    piece.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin)
    bar.addSubview_(piece)


_APP_ICONS = {}


def app_icon(name):
    """The icon of the application a clipping came from, cached by name.

    Only the application's NAME is recorded with a clipping, so the icon is
    looked up from that.  A name that no longer resolves — the app moved or
    was removed — caches None and is not asked about again.
    """
    if not name:
        return None
    if name in _APP_ICONS:
        return _APP_ICONS[name]
    icon = None
    try:
        workspace = NSWorkspace.sharedWorkspace()
        path = workspace.fullPathForApplication_(name)
        if path:
            icon = workspace.iconForFile_(path)
    except Exception:
        icon = None
    _APP_ICONS[name] = icon
    return icon


_OWN_ICON = []


def own_icon():
    """This app's icon, read from its own bundle.

    Not NSApp.applicationIconImage: a bundle launchd starts by running
    Contents/MacOS/Stache directly, rather than opening the bundle through
    LaunchServices, does not reliably inherit its own icon — the alerts came
    up wearing a mark that is nowhere in this bundle. Reading the icns is the
    one route that cannot pick up somebody else's.
    """
    if _OWN_ICON:
        return _OWN_ICON[0]
    path = NSBundle.mainBundle().pathForResource_ofType_("Stache", "icns")
    if path is None:                          # running from source
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "icon", "Stache.icns")
        path = local if os.path.exists(local) else None
    icon = NSImage.alloc().initWithContentsOfFile_(path) if path else None
    _OWN_ICON.append(icon)
    return icon


def _alert(title, body):
    alert = NSAlert.alloc().init()
    alert.setMessageText_(title)
    alert.setInformativeText_(body)
    icon = own_icon()
    if icon is not None:
        alert.setIcon_(icon)
    alert.addButtonWithTitle_("OK")
    alert.runModal()


# ---------------------------------------------------------------------------
# Login item
# ---------------------------------------------------------------------------

def _executable_path():
    return os.path.join(
        os.path.abspath(os.path.join(sys.argv[0], "..")), APP_NAME)


def install_login_item():
    """A LaunchAgent rather than a Login Item.

    launchd relaunches the agent if it ever dies, which a Login Item does
    not, and a background clipboard watcher that silently stops watching is
    worse than one that never started.
    """
    import plistlib
    os.makedirs(os.path.dirname(AGENT_PLIST), exist_ok=True)
    plist = {
        "Label": BUNDLE_ID,
        "ProgramArguments": [_executable_path()],
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ProcessType": "Interactive",
    }
    with open(AGENT_PLIST, "wb") as fh:
        plistlib.dump(plist, fh)
    target = "gui/%d" % os.getuid()
    subprocess.run(["/bin/launchctl", "bootout", target + "/" + BUNDLE_ID],
                   capture_output=True)
    subprocess.run(["/bin/launchctl", "bootstrap", target, AGENT_PLIST],
                   capture_output=True)


def remove_login_item():
    subprocess.run(["/bin/launchctl", "bootout",
                    "gui/%d/%s" % (os.getuid(), BUNDLE_ID)],
                   capture_output=True)
    _unlink(AGENT_PLIST)


# ---------------------------------------------------------------------------
# The application
# ---------------------------------------------------------------------------

class StacheApp(NSObject):

    def applicationDidFinishLaunching_(self, note):
        apply_card_size()
        self._adoptOwnIcon()
        self.store = Store()
        self.paused = False
        self.last_change = int(NSPasteboard.generalPasteboard().changeCount())
        self.store.prune(pref(DEF_MAX_ITEMS), pref(DEF_MAX_DAYS))

        self.picker = PickerController.alloc().initWithApp_(self)
        self.prefs = PrefsController.alloc().initWithApp_(self)
        self.help = HelpController.alloc().initWithApp_(self)

        self._buildStatusItem()

        self.hotkey = HotKey(self.hotkeyPressed)
        if not self.applyHotkey():
            self._hotkeyFailed()

        # The run loop keeps polling while menus are tracking and while a
        # window is being resized, which is why the timer goes in as a common
        # mode: a copy made during either would otherwise be missed.
        self.timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            POLL_SECONDS, self, "pollPasteboard:", None, True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.timer, NSRunLoopCommonModes)

    def _adoptOwnIcon(self):
        icon = own_icon()
        if icon is not None:
            NSApp.setApplicationIconImage_(icon)

    def applicationShouldTerminate_(self, sender):
        self.store.close()
        return 1

    # -- status item ------------------------------------------------------

    def _buildStatusItem(self):
        bar = NSStatusBar.systemStatusBar()
        self.status_item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        button = self.status_item.button()
        image = _menu_bar_glyph()
        if image is None:
            for symbol in ("mustache.fill", "list.clipboard"):
                image = NSImage.\
                    imageWithSystemSymbolName_accessibilityDescription_(
                        symbol, "Stache")
                if image is not None:
                    break
        if image is None:
            button.setTitle_("S")
        else:
            # A template image is tinted by macOS, so it stays right in a
            # light menu bar, a dark one, and while the menu is open.
            image.setTemplate_(True)
            button.setImage_(image)

        menu = NSMenu.alloc().initWithTitle_(APP_NAME)
        menu.setDelegate_(self)
        self._dynamic_count = 0
        self.open_item = menu.addItemWithTitle_action_keyEquivalent_(
            "Open Stache", "menuOpen:", "")
        self.open_item.setTarget_(self)
        menu.addItem_(NSMenuItem.separatorItem())
        self.pause_item = menu.addItemWithTitle_action_keyEquivalent_(
            "Pause Capturing", "menuPause:", "")
        self.pause_item.setTarget_(self)
        clear = menu.addItemWithTitle_action_keyEquivalent_(
            "Clear History…", "menuClear:", "")
        clear.setTarget_(self)
        menu.addItem_(NSMenuItem.separatorItem())
        prefs = menu.addItemWithTitle_action_keyEquivalent_(
            "Preferences…", "menuPrefs:", ",")
        prefs.setTarget_(self)
        about = menu.addItemWithTitle_action_keyEquivalent_(
            "About Stache & Help…", "menuHelp:", "/")
        about.setTarget_(self)
        menu.addItem_(NSMenuItem.separatorItem())
        quit_item = menu.addItemWithTitle_action_keyEquivalent_(
            "Quit Stache", "menuQuit:", "q")
        quit_item.setTarget_(self)
        self.status_item.setMenu_(menu)
        self.refreshMenu()

    def menuNeedsUpdate_(self, menu):
        """Rebuild the list of recent clippings at the top of the menu.

        The newest few are worth reaching without opening the picker at all -
        that is most recalls - so they are rebuilt every time the menu is
        pulled down rather than kept in sync as clippings arrive.
        """
        for _ in range(self._dynamic_count):
            menu.removeItemAtIndex_(0)
        self._dynamic_count = 0
        items = self.store.items(limit=RECENT_IN_MENU)
        if not items:
            return
        for index, item in enumerate(items):
            entry = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                _menu_title(item), "menuRecent:",
                str(index + 1) if index < 9 else "")
            entry.setKeyEquivalentModifierMask_(NSEventModifierFlagCommand)
            entry.setTarget_(self)
            entry.setTag_(item.id)
            thumb = _menu_thumb(item)
            if thumb is not None:
                entry.setImage_(thumb)
            menu.insertItem_atIndex_(entry, index)
        menu.insertItem_atIndex_(NSMenuItem.separatorItem(), len(items))
        self._dynamic_count = len(items) + 1

    def menuRecent_(self, sender):
        item = self.store.get(int(sender.tag()))
        if item is not None:
            self.copyToPasteboard_(item)

    def refreshMenu(self):
        self.open_item.setTitle_(
            "Open Stache    %s"
            % hotkey_label(pref(DEF_HOTKEY_CODE), pref(DEF_HOTKEY_MODS)))
        self.pause_item.setTitle_(
            "Resume Capturing" if self.paused else "Pause Capturing")

    # -- hotkey -----------------------------------------------------------

    def applyHotkey(self):
        ok = self.hotkey.register(pref(DEF_HOTKEY_CODE), pref(DEF_HOTKEY_MODS))
        self.refreshMenu()
        return ok

    def hotkeyPressed(self):
        self.picker.toggle()

    def _hotkeyFailed(self):
        _alert(
            "Stache could not claim %s"
            % hotkey_label(pref(DEF_HOTKEY_CODE), pref(DEF_HOTKEY_MODS)),
            "Another application already has that chord. Pick a different "
            "one in Preferences — Stache still opens from its menu bar item "
            "in the meantime.")

    # -- capture ----------------------------------------------------------

    def pollPasteboard_(self, timer):
        if self.paused:
            return
        pb = NSPasteboard.generalPasteboard()
        count = int(pb.changeCount())
        if count == self.last_change:
            return
        self.last_change = count

        types = [str(t) for t in (pb.types() or [])]
        if any(t in types for t in PRIVATE_TYPES):
            return                       # a password manager's write

        front = NSWorkspace.sharedWorkspace().frontmostApplication()
        app_name = str(front.localizedName() or "") if front else ""

        string = pb.stringForType_(NSPasteboardTypeString)
        string = str(string) if string else ""

        if pref(DEF_CAPTURE_IMAGES) and \
                pb.availableTypeFromArray_(list(IMAGE_TYPES)) is not None:
            png, width, height = png_from_pasteboard(pb)
            if png:
                self.store.add_image(png, width, height, app_name,
                                     string or None)
                self._afterCapture()
                return

        if not string.strip():
            string = _file_paths(pb)
        if string.strip():
            self.store.add_text(string, app_name)
            self._afterCapture()

    def _afterCapture(self):
        self.store.prune(pref(DEF_MAX_ITEMS), pref(DEF_MAX_DAYS))
        if self.picker.panel.isVisible():
            self.picker.reload()

    # -- recall -----------------------------------------------------------

    def copyToPasteboard_(self, item):
        """Put an item back so the next Cmd-V (or `pbpaste`) yields it."""
        pb = NSPasteboard.generalPasteboard()
        if item.kind == "image" and item.blob_path and \
                os.path.exists(item.blob_path):
            data = NSData.dataWithContentsOfFile_(item.blob_path)
            rep = NSBitmapImageRep.imageRepWithData_(data)
            types = [NSPasteboardTypePNG]
            tiff = rep.TIFFRepresentation() if rep is not None else None
            if tiff is not None:
                types.append(NSPasteboardTypeTIFF)
            pb.declareTypes_owner_(types, None)
            pb.setData_forType_(data, NSPasteboardTypePNG)
            if tiff is not None:
                pb.setData_forType_(tiff, NSPasteboardTypeTIFF)
        else:
            pb.declareTypes_owner_([NSPasteboardTypeString], None)
            pb.setString_forType_(item.body or item.preview,
                                  NSPasteboardTypeString)
        # Our own write must not be recorded as a new capture; bumping the
        # item's timestamp instead is what moves it back to the front.
        self.last_change = int(pb.changeCount())
        self.store.touch(item.id)

    def copyStringToPasteboard_(self, text):
        pb = NSPasteboard.generalPasteboard()
        pb.declareTypes_owner_([NSPasteboardTypeString], None)
        pb.setString_forType_(text, NSPasteboardTypeString)
        self.last_change = int(pb.changeCount())

    # -- menu actions -----------------------------------------------------

    def rebuildPicker(self):
        """Swap the picker for one built to the new preferences — and if it
        was on screen, put it straight back, showing the change.

        It used to just vanish: every preference change ordered the panel
        out and built a replacement that nobody showed. In strip layout that
        was survivable, since the strip sits out of the way; in a column it
        looked exactly like a crash.

        The old panel is NOT hidden through hide(), which would save its
        frame — by this point the layout preference has already changed, so
        the frame key has too, and a strip's geometry would be written into
        the column's slot.
        """
        old = self.picker
        was_visible = old is not None and old.panel.isVisible()
        query, kind = "", 0
        if old is not None:
            query = str(old.search.stringValue() or "")
            kind = old.selectedKindIndex()
            # Retired properly, not merely hidden. orderOut_ alone leaves the
            # old controller as the panel's delegate and leaves the window
            # alive, so anything still holding that controller — a pending
            # performSelector, a timer — can put it back on screen, and two
            # pickers end up visible at once.
            old.panel.setDelegate_(None)
            old.panel.orderOut_(None)
            old.panel.close()
        self.picker = PickerController.alloc().initWithApp_(self)
        if was_visible:
            self.picker.reopenAfterRebuild_kind_(query, kind)

    def menuOpen_(self, sender):
        self.picker.show()

    def menuPause_(self, sender):
        self.paused = not self.paused
        if not self.paused:
            self.last_change = int(
                NSPasteboard.generalPasteboard().changeCount())
        self.refreshMenu()

    def menuClear_(self, sender):
        NSApp.activateIgnoringOtherApps_(True)
        self.prefs.clearHistory_(sender)

    def menuPrefs_(self, sender):
        # Opening Preferences takes key from the picker, and the picker
        # dismisses itself when it loses key. Losing it to one of our own
        # windows is not clicking away.
        if self.picker is not None:
            self.picker.holdOpen()
        self.prefs.show()

    def showHelp(self):
        if self.picker is not None:
            self.picker.holdOpen()
        self.help.show()

    def menuHelp_(self, sender):
        self.showHelp()

    def menuAbout_(self, sender):
        NSApp.activateIgnoringOtherApps_(True)
        _alert(
            "Stache %s" % APP_VERSION,
            "Clipboard history for macOS.\n\n"
            "%d clipping%s, %s on disk.\n%s\n\n"
            "© 2026 Tim McCoy."
            % (self.store.count(), "" if self.store.count() == 1 else "s",
               _human_bytes(self.store.disk_bytes()), SUPPORT_DIR))

    def menuQuit_(self, sender):
        NSApp.terminate_(None)


MENU_TITLE_CHARS = 46


MENU_BAR_HEIGHT = 18.0           # points; the PNG is rendered at 2x


def _menu_bar_glyph():
    """The Old English S from the app icon, as a menu bar template image.

    Shipped as a PNG rather than drawn from the font at runtime, so the app
    does not depend on "Old English Five" being installed.
    """
    path = NSBundle.mainBundle().pathForResource_ofType_("Stache_glyph", "png")
    if path is None:                       # running from source
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "icon", "Stache_glyph.png")
        path = local if os.path.exists(local) else None
    if path is None:
        return None
    image = NSImage.alloc().initWithContentsOfFile_(path)
    if image is None:
        return None
    size = image.size()
    if size.height > 0:
        image.setSize_(NSMakeSize(
            round(size.width * MENU_BAR_HEIGHT / size.height),
            MENU_BAR_HEIGHT))
    return image


def _menu_title(item):
    if item.kind == "image":
        return "Image  %d × %d" % (item.width, item.height)
    text = " ".join((item.body or item.preview or "").split())
    if len(text) > MENU_TITLE_CHARS:
        text = text[:MENU_TITLE_CHARS - 1] + "…"
    return text or "(empty)"


def _menu_thumb(item):
    """A postage-stamp of an image clipping, beside its menu entry."""
    if item.kind != "image" or not item.thumb_path:
        return None
    if not os.path.exists(item.thumb_path):
        return None
    image = NSImage.alloc().initWithContentsOfFile_(item.thumb_path)
    if image is None:
        return None
    size = image.size()
    if size.width <= 0 or size.height <= 0:
        return None
    scale = min(28.0 / size.width, 18.0 / size.height)
    image.setSize_(NSMakeSize(round(size.width * scale),
                              round(size.height * scale)))
    return image


def _file_paths(pb):
    """Copying files in the Finder puts no string on the pasteboard, only
    URLs.  Recording their paths makes those copies recallable as text."""
    try:
        objects = pb.readObjectsForClasses_options_([NSURL], None) or []
    except Exception:
        return ""
    paths = [str(u.path()) for u in objects if u.isFileURL()]
    return "\n".join(paths)


# ---------------------------------------------------------------------------

def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(1)                 # accessory: no Dock icon
    delegate = StacheApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
