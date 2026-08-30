# Stache

Clipboard history for macOS.

The name is the joke: a *stache* is where you *stash* things, the two words
sound identical, and this is where the clipboard gets stashed and recalled
from. The moustaches on the icon are that pun made visible. A background agent records everything you copy —
text and images alike — with the time it was captured and the app it came
from. A global hotkey raises a grid of what it has kept; picking one puts it
back on the clipboard so the next ⌘V (or `pbpaste`) hands it over.

![the picker, open as a strip above the Dock](docs/screenshot.png)

    ⌃⌥⌘Space        open the picker

## Using it

Stache has no Dock icon and no window of its own. It lives in the menu bar
(the clipboard glyph) and shows itself when the hotkey is pressed.

**The menu bar item lists the ten newest clippings** — images with a
postage-stamp of themselves — so the common recalls need no picker at all.
Choose one and it goes on the clipboard. ⌘1–⌘9 pick them while the menu is
open.

The picker opens in one of two layouts:

* **Strip** (the default) — a single row of clippings across the bottom of
  the screen, sitting just above the Dock, anchored to the left edge and as
  wide a share of the screen as you set. It scrolls sideways.

  It keeps clear of a **hidden** Dock too. `visibleFrame` only excludes the
  Dock while the Dock is on screen; with autohide on it runs to the very edge
  of the display, so Stache works the reserve out from `com.apple.dock`
  itself — orientation, tile size, and magnification (a magnified Dock is
  taller, and the pointer is over it precisely when it is reaching for
  something sitting just above it). The reserve applies on whichever edge the
  Dock lives on.
* **Grid** — a centred window of rows and columns, for looking through the
  whole history rather than the last few.

Both are set under Preferences; each remembers its own size and position, and
either can be dragged anywhere you like.

Each card is a picture with a caption top and bottom: the date and time of
the capture above the thumbnail, the source app and size below it, and the
thumbnail itself taking every point neither caption needs.

A hint bar runs along the bottom of the picker the whole time it is open, so
the keys are there without being remembered. **?** in the header — or ⌘/ —
opens the full usage, including where the name comes from.

In the picker:

| | |
|---|---|
| click a card | copy it — the picker stays up and says so |
| ⌥-click | select without copying — look without disturbing the clipboard |
| ⇧-click | extend the selection from the last card clicked |
| ⌘-click | add or remove one card from the selection |
| right-click | Copy · Open · Open With ▸ (any app, or Other…) · Reveal in Finder · Pin · Delete |
| arrows | move the selection (in the strip, all four step along the row) |
| Return | copy the selected card |
| Space | quick look — opens an image in Preview (text cards just copy) |
| Delete | remove the selected clipping(s) for good — asks once for more than one |
| type anything | jumps into the search field |
| ⌘/ | the full help |
| Esc | close, clipboard untouched |
| All / Pinned / Images / Text / URL | filter by kind; each chip carries its own count |

Picking a clipping does **not** close the picker, and it **keeps** the
keyboard. It says what it did — a line on the left of the header naming what
went on the clipboard — and stays ready for the next pick or a search without
needing a click.

That means ⌘V does not land in the app behind while the picker is still up.
The sequence is **pick, Esc, ⌘V**: closing returns focus to whatever had it
before. Earlier versions handed focus back on every pick so that ⌘V worked
immediately, but the panel then went quiet under the cursor while still on
screen.

Close it with the hotkey, with esc, or by clicking away.

Neither ⇧-click nor ⌘-click copies. Building a selection is not choosing from
it — the point of selecting several is to delete them together.

The search field is at the far right of the header; the filter chips sit
between it and the status line. Search covers the text of a clipping, the name
of the app it came from, and the date it was captured — `safari` finds
everything copied out of Safari. The chip counts follow the search, so they
describe the list in front of you rather than the whole library.

A **URL** is a text clipping whose entire body is one link. It is worked out
from the text rather than stored, so nothing had to be migrated, and a URL is
*not* also counted as text — the four kinds add up to the total.

## Pinning

Pinning means keep this. A pinned clipping sorts first, and is exempt from the
item limit, the age limit and Clear History.

**A pinned clipping cannot be deleted at all while it is pinned.** Unpin it
first — right-click the card, Unpin — and then delete it like any other. That
is deliberate: a confirmation dialog puts the decision in the same keystroke as
the mistake, whereas unpinning is a separate, deliberate act. Deleting a mixed
selection deletes the unpinned ones and tells you how many pinned ones it kept.

Unpinning re-sorts the card out of the front of the list immediately. If the
**Pinned** chip is the filter in force at the time, the card would leave the
list altogether, so unpinning there switches the filter back to **All** and
keeps the card selected and scrolled into view.

Each card carries the icon of the application it came from, at its bottom
right.

Dates can be typed the way you'd say them:

| you type | you get |
|---|---|
| `today`, `yesterday` | that day |
| `this week`, `last week`, `this month` | that range |
| `aug`, `august`, `thursday` | that month or weekday |
| `2026-08-28`, `08/28/2026`, `8/28` | that date |
| `2026` | that year |
| `12:55`, `12:55 pm` | that minute |

A query only counts as a date if it looks like one — it needs a digit, or to
be the start of a month or weekday name — so searching for `report` still
searches your clippings rather than every Thursday.

Each card carries two dates: when the clipping was **captured**, and — in a
dimmer colour beside it — when it was last **used**, if it has been recalled
since. Capture time is written once and never changes.

**Pinned** clippings sort to the front and are exempt from both retention
limits and Clear History. They never show an expiry warning, because they
never expire. Deleting one asks first — pinning is how you say
"keep this", so ⌫ should not be able to undo that in a single keystroke. The
alert carries a *Don't ask again* switch, and Preferences has the same switch
to turn it back on. From the shell, `stache rm` asks too, and takes
`--force`.

## Preferences

From the menu bar item, or ⌘, while Stache is frontmost.

* **Card size** — Large (272×220, a 260×175 thumbnail), Medium, or Small
  (190×158, the original). The strip grows and shrinks to match. A thumbnail
  that is too small for the card it now has to fill is quietly rebuilt from
  the full-resolution PNG the first time it is drawn, so older clippings look
  right at any size.
* **Layout** — Strip or Grid.
* **Strip width** — a percentage of the screen, from the left edge. 60% by
  default.
* **Hotkey** — click the button, press the chord you want. At least one
  modifier is required: a bare key would be claimed system-wide and taken
  away from every other app.
* **Keep at most** *n* items (0 = no limit).
* **Delete after** *n* days (0 = never) — counted from the last time you
  *used* a clipping, not from when it was captured, so anything you keep
  reaching for never ages out. A clipping inside the last tenth of its life
  (three days on a thirty-day limit, never less than one) says so in red on
  its card: *3 days left*, *expires today*, *expiring*.
* **Capture images as well as text** — off makes Stache text-only, and image
  copies are ignored rather than stored.
* **Open Stache at login** — installs a LaunchAgent at
  `~/Library/LaunchAgents/com.timmccoy.stache.plist`. launchd relaunches the
  agent if it ever dies, which a Login Item does not, and a clipboard
  watcher that has silently stopped watching is worse than one that never
  started.
* **Clear History…** — deletes every unpinned clipping and its image file.

Defaults: large cards, strip at 60% width, ⌃⌥⌘Space, 500 items, 30 days,
images on.

## Where the data lives

    ~/Library/Application Support/Stache/
        stache.sqlite3     the index and the text of every clipping
        blobs/            one PNG per image clipping
        thumbs/           its thumbnail

Image clippings are ordinary PNG files on purpose, so *Open* and *Reveal in
Finder* work straight from the picker.

The open item is named after the application that will actually open it —
whatever owns PNGs on this Mac — rather than assuming Preview. When Preview
is not the default, it is offered as a second item, so a quick look does not
have to wake an image editor.

**Open With** lists every application that says it can handle the clipping,
and *Other…* picks one from anywhere. Text clippings work here too: they are
written out to `exports/clipping-<n>.txt` first, so any editor can open one.

Nothing leaves the Mac and nothing is encrypted — the database is readable by
anything running as you. If you copy something you would not want sitting in
a file, delete that clipping (or use Clear History).

## What is not recorded

* Anything a password manager copies. 1Password, LastPass, Keychain Access
  and the rest flag their pasteboard writes with the community
  `org.nspasteboard.ConcealedType` marker; Stache skips those, along with the
  `TransientType` and `AutoGeneratedType` markers.
* Whatever arrives while **Pause Capturing** is on.
* Stache's own writes when you pick something — the clipping's timestamp is
  moved to the front instead, so it does not accumulate duplicates of itself.

Copying the same thing twice does not make a second entry either; the
existing one moves back to the top.

## Permissions

None. The hotkey is a Carbon hot key, which the window server delivers
without the Accessibility grant, and putting data on the pasteboard is
unprivileged.

That is why picking a clipping *copies* rather than pressing ⌘V for you:
synthesising a keystroke is the one thing here that would have demanded
Accessibility, and this app does not need it.

## From the shell

`~/bin/stache` reads the same history, so a clipping can be recalled without
touching the picker:

    stache                 the 20 newest clippings, numbered
    stache list -n 50      more of them
    stache list safari     only clippings matching "safari"
    stache 3               print clipping 3 (an image prints its path)
    stache copy 3          put clipping 3 on the clipboard
    stache path 3          the PNG file behind an image clipping
    stache rm 3            delete clipping 3
    stache stats           how much history there is

Numbers match the app: 1 is the newest, pinned first, the same order as the
menu and the picker. The database is opened read-only for everything except
`rm`, so it is safe to run while the app is running.

`stache copy` goes through `pbcopy` for text and AppleScript for images —
`pbcopy` can only ever set a path as text, never the image data itself. The
running app notices the write and moves that clipping back to the top of the
history, the same as if it had been picked from the grid.

## Building

    ./venv/bin/python test_stache.py       headless checks + test_render*.png
    ./build.sh                            build and sign into dist/
    ./build.sh --install                  also install to /Applications
    ./release.sh                          notarize app + DMG, staple, install

`test_stache.py` runs the store against a scratch database and renders the
picker to PNG in both light and dark appearance, so the layout can be checked
without leaving a GUI instance of the app running.

The version number lives in one place — `APP_VERSION` in `stache.py` —
and `setup.py` reads it from there.

## Files

    stache.py           the whole app
    test_stache.py      headless checks and the panel render
    make_icon.py       builds icon/Stache.icns from the artwork
    icon/stache.pxd    the icon artwork (Pixelmator Pro master)
    setup.py           py2app bundle
    build.sh           build, sign, install
    release.sh         notarize and staple app + DMG
    ~/bin/stache       the command-line client (stdlib only, no venv)
    stache.entitlements hardened-runtime entitlements

© 2026 Tim McCoy.
