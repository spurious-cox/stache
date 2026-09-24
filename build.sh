#!/bin/zsh
# Build, sign and install Stache.app — v1.0.0
#
# Signing follows the same rules the other apps here learned the hard way:
#
#   * `codesign --deep` is NOT enough for a py2app bundle. It skips the .so
#     files under Resources/lib and the extension-less Mach-O at
#     Contents/MacOS/python, and notarization rejects exactly those. `file`
#     is the only reliable test for what is a Mach-O; filenames are not.
#   * `--options runtime` (hardened runtime) is mandatory for notarization
#     and is not on by default.
#   * The identity is selected by SHA-1 HASH, not by name: expired
#     certificates with similar names are still in the keychain and signing
#     by name can pick a dead one.
#   * --timestamp is not optional; a timestamped signature stays valid after
#     the certificate expires.
#
#   ./build.sh              build and sign into dist/
#   ./build.sh --install    also install to /Applications
set -e
cd "${0:A:h}"

SIGN_ID="4208ABA3EC12F24C1F09C7BB624EFF68B44259DB"

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

if ! security find-identity -p codesigning | grep -q "$SIGN_ID"; then
    echo "error: signing identity $SIGN_ID not in keychain — see header of this script" >&2
    exit 1
fi

echo "==> stopping any running instance (and its LaunchAgent)"
agent_stop

echo "==> building the icon"
./venv/bin/python make_icon.py

echo "==> building"
rm -rf build dist
./venv/bin/python setup.py py2app >/dev/null

echo "==> signing inner binaries with the hardened runtime"
find dist/Stache.app -type f -print0 2>/dev/null | while IFS= read -r -d $'\0' f; do
    if file -b "$f" 2>/dev/null | grep -q 'Mach-O'; then
        codesign --force --timestamp --options runtime --sign "$SIGN_ID" "$f" 2>/dev/null || true
    fi
done

echo "==> sealing nested frameworks, then the app"
find dist/Stache.app -name '*.framework' -print0 2>/dev/null \
    | xargs -0 -n1 -I{} codesign --force --timestamp --options runtime --sign "$SIGN_ID" {} 2>/dev/null || true
codesign --force --timestamp --options runtime \
    --entitlements stache.entitlements --sign "$SIGN_ID" dist/Stache.app
codesign --verify --deep --strict dist/Stache.app

# Installing is the DEFAULT. It used to need --install, and the failure
# that caused is silent: the build succeeds, /Applications keeps the old
# version, and everything downstream looks like it worked. Pass --no-install
# to build without touching /Applications.
if [[ "$1" != "--no-install" ]]; then
    echo "==> installing to /Applications"
    rm -rf /Applications/Stache.app
    cp -R dist/Stache.app /Applications/
    xattr -dr com.apple.quarantine /Applications/Stache.app 2>/dev/null || true
    agent_start
    codesign -dv /Applications/Stache.app 2>&1 | grep -E "Identifier=|Authority="
    plutil -extract CFBundleShortVersionString raw /Applications/Stache.app/Contents/Info.plist
fi

echo "==> running instances: $(pgrep -x Stache | wc -l | tr -d ' ')"
