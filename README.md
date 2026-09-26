# Stache

Clipboard history for macOS.

### [⬇︎ Download the latest release](https://github.com/spurious-cox/stache/releases/latest)

Notarized and stapled by Apple — open the DMG and drag Stache to
Applications. No Gatekeeper warning, no permissions to grant.

**Updating: quit Stache first** (menu bar S → Quit). Force-quitting counts as
a crash, and the LaunchAgent will bring the old copy straight back.

A background agent records everything you copy, text and images alike, with
the time and the app it came from. A global hotkey raises a grid of what it
has kept; picking one puts it back on the clipboard.

The name is the joke: a *stache* is where you *stash* things.

![the picker, open as a strip above the Dock](docs/screenshot.png)

    ⌃⌥⌘Space        open the picker

## New in 2

* **Share a clipping to anywhere macOS can send it** (2.11.2). A Share
  submenu on the clipping's menu, carrying whatever the system offers for
  that content — AirDrop, Mail, Messages, Notes, Freeform, Journal,
  Reminders, and Add to Reading List when the clipping is a link. AirDrop
  gets a named file rather than raw text, so it arrives with its name
  intact. A hidden clipping asks for Touch ID first: sealing one out of
  every list would mean little if sending it off the Mac did not ask.
* **The Help button says "Help"** instead of "?", and the help text has a
  section on sending a clipping somewhere.

* **⌘V, ⌘C, ⌘X and ⌘A now work in every text field** (2.5.1). A background app
  owns no menu bar, and without a main menu there was nothing for macOS to
  match those keystrokes against — so a note could be typed into but not
  pasted into.
* **⌘Z undoes an edit in a note or clipping** (2.5.2), and ⌘⇧Z redoes it.
  The single-line fields — the search box, the Preferences fields — have no
  undo: they are edited by a text view the window lends them, and switching
  undo on for that view is not enough to make it register anything.

* **Notes** — reference text you type, kept as a clipping (⌘N).
* **Filters made on the fly** — a search you like becomes a filter of its
  own, appended after the built-in ones (⌘⇧F).
* **Hidden clippings** — sealed out of every list, behind Touch ID (⌘H).
* **Newest first, everywhere.** Pinned clippings no longer jump the queue, so
  the picker opens on what you just copied. Pinning or hiding one counts as
  activity, so it goes to the front of its own list.
* **The menu bar menu no longer lists clippings.** It opens with one click and
  no authentication, which is the wrong place for the history now that
  clippings can be hidden.
* **The pointer crossing another window no longer closes the picker** — only a
  real click does.
* The **column** layout hangs from the top of the screen instead of standing
  on the Dock.
* Preferences, Help and the editor no longer vanish when Stache stops being
  the active application.

## Using it

No Dock icon and no window of its own — Stache lives in the menu bar. That
menu holds **no clippings**: it opens with one click and no authentication,
which is the wrong place for the history when hidden clippings exist. It is
About, Preferences, Help, Check for Updates, Open, Pause Capturing, Clear
History and Quit.

Three layouts, set in Preferences, each remembering its own size and place:

* **Strip** — one row above the Dock, scrolling sideways. The default.
* **Column** — one column up the left edge, scrolling vertically.
* **Grid** — a centred window, for looking through the whole history.

| | |
|---|---|
| click a card | copy it — the picker stays up and says so |
| ⌥-click | select without copying |
| ⇧-click | extend the selection |
| ⌘-click | add or remove one card |
| right-click | Quick Look · Copy · Open · Open With ▸ · Reveal in Finder · Pin · Delete |
| arrows | move the selection |
| Return | copy the selected card |
| Space | Quick Look — text or image, follows the arrow keys |
| ⌫ | delete for good — refused while pinned; asks once for more than one |
| type anything | jumps into the search field |
| ⌘0 | put the panel back where it belongs |
| ⌘N | write a note |
| ⌘H | hide the selection — or reveal it, under the Hidden filter |
| ⌘⇧F | keep the current search as a filter, or remove the filter you are on |
| ⌘/ | the full help |
| Esc | close, clipboard untouched |
| [ ALL ] / Pinned / Notes / Images / Text / URL / Hidden | the seven built-in filters; each count is exact, and [ ALL ] shows none |

Picking does not close the picker and does not hand back the keyboard, so the
sequence is **pick, Esc, ⌘V**.

Clicking away closes it; the pointer merely crossing another window does not.
That distinction matters if you use Terminal's *FocusFollowsMouse*, which
makes a window key on hover — the picker stays put until you actually click.

Closing the picker leaves you on the Space you are on. The keyboard goes back
to the app that had it if that app has a window here, otherwise to the
frontmost app on this Space.

Drag the panel anywhere and resize it; the frame is saved per layout. One
dimension is fixed by the card — a strip's height, a column's width. ⌘0
forgets a dragged position, which matters if it was dragged to a display you
no longer have.

Search covers the text, the source app and the capture date. Dates can be
typed the way you say them: `today`, `last week`, `august`, `thursday`,
`8/28`, `2026`, `12:55 pm`. A **URL** is a text clipping whose whole body is
one link, and is not also counted as text.

## Opening and changing a clipping

A link opens in your browser; anything else is written to a real file and
opened by whatever handles it.

**Edit…** rewrites a pinned text clipping in place, and **Update From
Clipboard** replaces a pinned image. Both are pinned-only: an unpinned
clipping is subject to the retention limits, so the edit would not last.
A changed card shows **edited** beside its date.

## Pinning

A pinned clipping is exempt from the item limit, the age
limit and Clear History. **It cannot be deleted while pinned** — unpin it
first. Deleting a mixed selection deletes the unpinned ones and says how many
it kept.

## Notes

⌘N writes one. A note is an ordinary clipping you typed rather than copied, so
it searches, pins, filters and previews like any other — and it is editable
without pinning first.

Notes are exempt from the item limit and the age limit, and never show an
expiry countdown.

## Filters made on the fly

Seven filters are built in and always present, in this order:

    [ ALL ] · Pinned · Notes · Images · Text · URL · Hidden

⌘⇧F keeps whatever is in the search field as a filter of its own, under a name
you choose. **It is appended after those seven**, and so is every filter you
add after it, in the order you made them — the built-in filters never move.
Selecting your filter and typing searches **within** it. To remove one: empty
the field, select the filter, ⌘⇧F again — the clippings stay.

Every filter but **[ ALL ]** carries a count of what it holds, exact and
unaffected by what you type — how many the search left is in the status line
instead. **[ ALL ] shows no number**: counting the hidden clippings would
contradict the list under it, and leaving them out would not be all.

Saved filters live in preferences, not the database. When the filters no longer
fit the width of the panel, the whole row becomes a popup menu carrying the
same choices and counts — the room decides, not the number, so a wide strip
holds far more of them than a column.

## Hidden clippings

⌘H seals the selection. Hidden clippings leave every list, every count and
every search — absent, not greyed out. The **Hidden** filter shows them after
Touch ID, and locks again when the picker closes. ⌘H there puts them back.

Sealed means the body, the preview and any image are encrypted (AES-256-CBC
with an HMAC over the ciphertext), the thumbnail is deleted, the source app is
cleared and the digest randomised. Copying the database gets an attacker
nothing.

**What it does not do:** the key is a 0600 file in Application Support, so
Touch ID guards the window and not the key — anything already running as you
could read it. The keychain that can hold a key behind biometry needs an
entitlement this app cannot have.

Unlock falls back to your login password, so a Mac without Touch ID works too.

## Preferences

From the menu bar item, or ⌘, while Stache is frontmost.

* **Card size** — Large, Medium or Small. Thumbnails are rebuilt as needed.
* **Layout** — Strip, Column or Grid.
* **Strip size** — a percentage of the screen: a strip's width, a column's
  height.
* **Hotkey** — click the button and press the chord. At least one modifier.
* **Keep at most** *n* items (0 = no limit).
* **Delete after** *n* days (0 = never), counted from the last time you used
  a clipping. A card in the last tenth of its life says so in red.
* **Capture images as well as text.**
* **Open Stache at login** — installs a LaunchAgent, which launchd restarts
  if it dies.
* **Clear History…** — deletes every unpinned clipping and its image file.

Defaults: large cards, strip at 60%, ⌃⌥⌘Space, 500 items, 30 days, images on.

## Where the data lives

    ~/Library/Application Support/Stache/
        stache.sqlite3     the index and the text of every clipping
        blobs/             one PNG per image clipping
        thumbs/            its thumbnail

    exports/           text written out so other apps can open it

Image clippings are ordinary PNGs, so Open and Reveal in Finder work straight
from the picker. Nothing leaves the Mac, and — apart from hidden clippings —
nothing is encrypted: the database is readable by anything running as you.

**Deleting a clipping deletes what it left on disk**: its PNG, its thumbnail
and any exported copy of its text, and the database is vacuumed so the row's
bytes are not left in a freed page. Hiding one deletes its export too, since
that copy is the plaintext. Exports with no clipping behind them are cleared
at launch.

## What is not recorded

* Anything a password manager copies (the `org.nspasteboard.ConcealedType`
  marker, along with `TransientType` and `AutoGeneratedType`).
* Whatever arrives while **Pause Capturing** is on.
* Stache's own writes when you pick something.

Copying the same thing twice moves the existing entry back to the top rather
than making a second one.

## Permissions

None. The hotkey is a Carbon hot key, and writing to the pasteboard is
unprivileged. That is why picking a clipping copies rather than pressing ⌘V
for you — synthesising a keystroke would have required Accessibility.

## From the shell

`~/bin/stache` reads the same history:

    stache                 the 20 newest clippings, numbered
    stache list -n 50      more of them
    stache list safari     only clippings matching "safari"
    stache 3               print clipping 3
    stache copy 3          put clipping 3 on the clipboard
    stache path 3          the PNG behind an image clipping
    stache rm 3            delete clipping 3 (asks; --force skips)
    stache stats           how much history there is

Numbers match the app. The database is opened read-only except for `rm`, so
it is safe to run while the app is running. It cannot see hidden clippings —
the key belongs to the app.

## Building

    ./venv/bin/python test_stache.py      headless checks + test_render*.png
    ./build.sh                            build and sign into dist/
    ./build.sh --install                  also install to /Applications
    STACHE2_PUBLISH=yes ./release.sh      notarize + DMG (refuses without it)

The version lives in one place — `APP_VERSION` in `stache.py`.

## Files

    stache.py           the whole app
    test_stache.py      headless checks and the panel render
    make_icon.py        builds icon/Stache.icns from the artwork
    icon/stache.pxd     the icon artwork (Pixelmator Pro master)
    setup.py            py2app bundle
    build.sh            build, sign, install
    release.sh          notarize and staple app + DMG
    stache.entitlements hardened-runtime entitlements

© 2026 Tim McCoy.

## Problems or suggestions

Open an issue: https://github.com/spurious-cox/stache/issues
