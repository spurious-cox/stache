# Stache

Clipboard history for macOS.

### [⬇︎ Download the latest release](https://github.com/spurious-cox/stache/releases/latest)

Notarized and stapled by Apple — open the DMG and drag Stache to
Applications. No Gatekeeper warning, and no special permissions needed.

**Updating: quit Stache first** — menu bar S → Quit. If it is running with
*Open Stache at login* enabled, a LaunchAgent is watching it, and replacing a
live app bundle is unreliable: the old version can survive the copy and keep
running, so the new one never appears to install. Quitting properly is enough
— the agent does not relaunch after a clean quit, only after a crash. Killing
the process instead (`pkill`, Force Quit) *does* count as a crash and will
bring the old copy straight back.

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

The picker opens in one of three layouts:

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
* **Column** — the strip stood on end: a single column of clippings up the
  left edge of the screen, clear of the Dock, as tall a share of the screen
  as you set. It scrolls vertically. One card wide, so the width is fixed
  and the height is yours.

  Too narrow for the strip's single header row, so it gets three: the name
  and copyright, then the search field, then the five kinds as a popup with
  the item count and help beside it. The title bar carries only the name and
  icon — at 230pt the version and copyright overlapped it into a pile.

* **Grid** — a centred window of rows and columns, for looking through the
  whole history rather than the last few.

All three are set under Preferences, and each remembers its own size and
position — see [Moving and sizing it](#moving-and-sizing-it).

Each card is a picture with a caption top and bottom: the date and time of
the capture above the thumbnail, the source app and size below it, and the
thumbnail itself taking every point neither caption needs.

A hint bar runs along the bottom of the strip and the grid the whole time
they are open, so the keys are there without being remembered. A **column**
has no room for it — the line is about 700pt wide and a column is around 270,
so it could only ever appear truncated — and the keys live in the help
instead. **?** in the header, or ⌘/, opens the full usage, including where
the name comes from.

In the picker:

| | |
|---|---|
| click a card | copy it — the picker stays up and says so |
| ⌥-click | select without copying — look without disturbing the clipboard |
| ⇧-click | extend the selection from the last card clicked |
| ⌘-click | add or remove one card from the selection |
| right-click | Copy · Open · Open With ▸ (any app, or Other…) · Reveal in Finder · Pin · Delete |
| arrows | move the selection (in a strip or column, all four step by one) |
| ⌘0 | put the panel back where it calculated it belonged |
| Return | copy the selected card |
| Space | Quick Look the selected clipping — text or image |
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

## Moving and sizing it

**Drag the panel anywhere, resize it, and it stays there.** The frame is
saved when the picker closes and restored the next time it opens, so the
place and size you chose survive quitting, logging out and rebooting.

One dimension is not yours to set, and which one depends on the layout. A
**strip**'s height is dictated by the card, the header and the hint bar — a
saved height from before the hint bar existed, or from a different card size,
describes a strip that no longer exists — so only its width is remembered. A
**column** is the mirror: its width is one card, and only its height is
remembered. A **grid** remembers both.

Each layout keeps its **own** saved frame, so switching between them does not
drag one arrangement's shape onto another.

**⌘0 puts it back** where it calculated it belonged — along the bottom above
the Dock for a strip, up the left edge for a column, centred for a grid — and
forgets where it had been dragged. Remembering the position is what makes
dragging useful, and also what makes it a trap: a panel dragged onto a second
display that is no longer attached is remembered just as faithfully as one
dragged somewhere sensible. A frame that would land off-screen is ignored on
open, but ⌘0 is the deliberate way back.

Neither ⇧-click nor ⌘-click copies. Building a selection is not choosing from
it — the point of selecting several is to delete them together.

The search field is at the far right of the header; the filter chips sit
between it and the status line. Search covers the text of a clipping, the name
of the app it came from, and the date it was captured — `safari` finds
everything copied out of Safari.

The chip counts say how many of each kind **exist**, and do not move as you
type. A number that changed while you searched could not be used to decide
where to look, which is the only reason to put one on a chip. How many the
search left is a separate fact and the status line reports it — `2 visible of
8`. In a column that shortens to `2 visible`, since the All chip beside it
already carries the total, and the size on disk and the reopen chord move
into its tooltip.

A **URL** is a text clipping whose entire body is one link. It is worked out
from the text rather than stored, so nothing had to be migrated, and a URL is
*not* also counted as text — the four kinds add up to the total.

## Opening and changing a clipping

Right-click a card for **Quick Look**, **Copy**, **Open**, **Open With ▸**,
**Reveal in Finder**, and — for a pinned clipping — **Edit…** or **Update
From Clipboard**.

**Quick Look** previews the selected clipping, text or image alike, on Space
or from the top of the menu. It shows one clipping — the selected one — and
follows the arrow keys, exactly as it does in the Finder.

**A link opens as a link.** A clipping whose whole body is one http(s) URL is
handed to your browser. Everything else is written out to a real file and
opened with whatever handles that file, which is why Open With offers
browsers for a URL and text editors for prose.

**Editing is for pinned clippings only**, and the restriction is the point
rather than a limitation. Pinning is what exempts a clipping from the item
cap, the age cap and Clear History — so a pinned clipping is the only kind
where an edit is not work the retention sweep quietly deletes later. Unpinned
cards say **Edit… (pin it first)**.

* **Edit…** opens a plain editor on a text clipping. Save replaces the body
  in place, along with everything derived from it — the preview the card
  draws, the byte count, and the digest used to spot duplicates.
* **Update From Clipboard** replaces a pinned *image* with whatever is on the
  clipboard now. This is the other half of opening one in an editor: copying
  your edit back is an ordinary pasteboard write, so on its own it creates a
  **new** clipping and leaves the pinned original untouched. That is easy to
  miss, because at card size a small change — a crop of a few pixels — looks
  identical.

Once a clipping has been changed the card shows **edited** beside its date. A
card describes something that was copied, with a capture time and a source
application; once you have rewritten it that is no longer strictly true, and
the card says so rather than pretending.

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
* **Layout** — Strip, Column or Grid.
* **Strip size** — a percentage of the screen: how *wide* a strip is, how
  *tall* a column is. 60% by default.
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
