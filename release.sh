#!/bin/zsh
# Notarize Stache.app and wrap it in a distributable DMG — v1.0.0
#
# Run ./build.sh first; this takes dist/Stache.app as it finds it.
#
# Notarization uses the same keychain profile as the PixPro apps and KBD, so
# no password lives here or gets typed. If the profile is ever lost:
#   xcrun notarytool store-credentials "PixProNotary" \
#       --apple-id <appleid> --team-id RUDN8D7ZN9
#
# Both the app and the DMG are notarized and stapled. Stapling the app
# matters because that is what gets dragged out of the DMG; stapling the DMG
# matters because that is what gets downloaded. Notarizing only one of the
# two leaves a Gatekeeper warning on the other.
set -e
cd "${0:A:h}"

SIGN_ID="4208ABA3EC12F24C1F09C7BB624EFF68B44259DB"
PROFILE="PixProNotary"
APP="dist/Stache.app"
VOLNAME="Stache"

# Stache now runs under a LaunchAgent, and KeepAlive treats a pkill as a
# crash — launchd would relaunch the OLD binary in the middle of the copy.
# Unload it around the install and load it again afterwards.
STACHE_AGENT="$HOME/Library/LaunchAgents/com.timmccoy.stache.plist"
# Both are idempotent and never fail the script. `launchctl bootout` returns
# non-zero for a service it cannot find, and under `set -e` that is fatal —
# which is exactly what silently killed the 1.1.0 install after build.sh had
# already unloaded the agent and release.sh tried to unload it again.
agent_stop() {
    if [[ -f "$STACHE_AGENT" ]]; then
        launchctl bootout "gui/$(id -u)/com.timmccoy.stache" 2>/dev/null || true
    fi
    pkill -x Stache 2>/dev/null || true
    sleep 1
    return 0
}
agent_start() {
    if [[ -f "$STACHE_AGENT" ]]; then
        launchctl bootstrap "gui/$(id -u)" "$STACHE_AGENT" 2>/dev/null || true
    fi
    return 0
}

[[ -d "$APP" ]] || { echo "error: $APP not found — run ./build.sh first" >&2; exit 1; }

VERSION=$(plutil -extract CFBundleShortVersionString raw "$APP/Contents/Info.plist")
DMG="dist/Stache-${VERSION}.dmg"

xcrun notarytool history --keychain-profile "$PROFILE" >/dev/null 2>&1 \
    || { echo "error: no notary profile '$PROFILE' in keychain" >&2; exit 1; }

echo "==> notarizing the app (Stache $VERSION)"
rm -f dist/Stache_notarize.zip
ditto -c -k --keepParent "$APP" dist/Stache_notarize.zip
xcrun notarytool submit dist/Stache_notarize.zip --keychain-profile "$PROFILE" --wait
xcrun stapler staple "$APP"

echo "==> building the disk image"
rm -rf dist/dmg "$DMG"
mkdir -p dist/dmg
cp -R "$APP" dist/dmg/
ln -s /Applications dist/dmg/Applications
# hdiutil intermittently returns "Resource busy" on a folder that was
# written seconds earlier — something (Spotlight, on-access AV) still has it
# open. It clears on its own, so retry rather than abandoning a build whose
# app is already notarized and stapled. This failed 1.0.2 the first time and
# succeeded on the very next attempt.
for attempt in 1 2 3 4 5; do
    if hdiutil create -volname "$VOLNAME" -srcfolder dist/dmg -ov \
            -format UDZO "$DMG" >/dev/null 2>/tmp/stache_hdiutil.err; then
        break
    fi
    echo "    hdiutil attempt $attempt failed: $(tr -d '\n' < /tmp/stache_hdiutil.err)"
    if [[ $attempt == 5 ]]; then
        echo "error: could not build the disk image" >&2
        exit 1
    fi
    sleep 5
done
rm -rf dist/dmg

echo "==> signing and notarizing the disk image"
codesign --force --timestamp --sign "$SIGN_ID" "$DMG"
xcrun notarytool submit "$DMG" --keychain-profile "$PROFILE" --wait
xcrun stapler staple "$DMG"

echo "==> installing the stapled app to /Applications"
agent_stop
rm -rf /Applications/Stache.app
cp -R "$APP" /Applications/
xattr -dr com.apple.quarantine /Applications/Stache.app 2>/dev/null || true
agent_start

echo "==> results"
echo "    dmg:      $DMG  ($(du -h "$DMG" | cut -f1))"
echo "    stapled:  app $(xcrun stapler validate "$APP" >/dev/null 2>&1 && echo YES || echo no), dmg $(xcrun stapler validate "$DMG" >/dev/null 2>&1 && echo YES || echo no)"
spctl -a -t open --context context:primary-signature -v "$DMG" 2>&1 | sed 's/^/    gatekeeper: /'
echo "    running instances: $(pgrep -x Stache | wc -l | tr -d ' ')"
