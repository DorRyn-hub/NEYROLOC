#!/usr/bin/env bash
# Build a self-contained macOS application with Nuitka, the deployment backend
# used by Qt's official pyside6-deploy tool. Unlike build_app.sh, this output
# does not depend on the checkout path or an external Python.framework.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_VENV="$PROJECT_DIR/packaging/.venv"
PYTHON="${NEYROLOC_BUILD_PYTHON:-$BUILD_VENV/bin/python}"
MACOS_DEPLOYMENT_TARGET="15.0"
DEPLOYMENT_DIR="$PROJECT_DIR/deployment"
FRPC_BINARY="$PROJECT_DIR/NEYROLOCK_5/resources/bin/frpc"
ICON_SOURCE="$PROJECT_DIR/NEYROLOCK_5/resources/icon-512.png"
ICONSET_DIR="$DEPLOYMENT_DIR/NEYROLOC_NEW.iconset"
ICON_FILE="$DEPLOYMENT_DIR/NEYROLOC_NEW.icns"

verify_macos_target() {
    local binary="$1"
    local minos
    minos="$(otool -l "$binary" | awk '
        /LC_BUILD_VERSION/{modern=1; next}
        modern && /minos/{print $2; exit}
        /LC_VERSION_MIN_MACOSX/{legacy=1; next}
        legacy && /version/{print $2; exit}
    ')"
    if [[ -z "$minos" ]]; then
        echo "Cannot determine macOS deployment target: $binary" >&2
        exit 1
    fi
    if ! awk -v version="$minos" -v maximum="$MACOS_DEPLOYMENT_TARGET" 'BEGIN {
        split(version, current, "."); split(maximum, allowed, ".");
        exit !((current[1] + 0 < allowed[1] + 0) ||
               (current[1] + 0 == allowed[1] + 0 && current[2] + 0 <= allowed[2] + 0));
    }'; then
        echo "Deployment target $minos exceeds $MACOS_DEPLOYMENT_TARGET: $binary" >&2
        exit 1
    fi
}

MODE="build"
case "${1:-}" in
    "") ;;
    --dry-run) MODE="dry-run" ;;
    -h|--help)
        echo "Usage: packaging/build_standalone_macos.sh [--dry-run]"
        exit 0
        ;;
    *)
        echo "Unknown option: $1" >&2
        exit 2
        ;;
esac

NUITKA_ARGS=(
    "$PROJECT_DIR/main.py"
    --standalone
    --macos-create-app-bundle
    --enable-plugin=pyside6
    --include-package=backends
    --include-package=core
    --include-package=ui
    --output-dir="$DEPLOYMENT_DIR"
    --output-filename=NEYROLOC_NEW
    --company-name=RDEV
    --product-name="NEYROLOC NEW"
    --file-version=1.2.0
    --product-version=1.2.0
    --macos-app-version=1.2.0
    --macos-app-name="NEYROLOC NEW"
    --macos-signed-app-name=ru.dorryn.neyrolocnew
    --macos-app-icon="$ICON_FILE"
    --include-data-dir="$PROJECT_DIR/NEYROLOCK_5/resources=resources"
    --include-data-files="$PROJECT_DIR/packaging/android/NEYROLOC.apk=packaging/android/NEYROLOC.apk"
    --noinclude-data-files=resources/bin/**
    --nofollow-import-to=tests
    --nofollow-import-to=NEYROLOC_2
    --nofollow-import-to=NEYROLOC
    --noinclude-qt-translations
    --assume-yes-for-downloads
)

cd "$PROJECT_DIR"
if [[ "$MODE" == "dry-run" ]]; then
    printf 'Nuitka command:'
    printf ' %q' "$PYTHON" -m nuitka "${NUITKA_ARGS[@]}"
    printf '\n'
    if [[ -x "$FRPC_BINARY" ]]; then
        echo "Bundled tunnel helper: $FRPC_BINARY"
    else
        echo "Tunnel helper is absent; LAN access will still work."
    fi
    exit 0
fi

if [[ -z "${NEYROLOC_BUILD_PYTHON:-}" && ! -x "$PYTHON" ]]; then
    BOOTSTRAP_PYTHON="${NEYROLOC_BUILD_BOOTSTRAP_PYTHON:-python3}"
    if ! command -v "$BOOTSTRAP_PYTHON" >/dev/null 2>&1; then
        echo "Missing build Python: $BOOTSTRAP_PYTHON" >&2
        exit 1
    fi
    BOOTSTRAP_VERSION="$($BOOTSTRAP_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    case "$BOOTSTRAP_VERSION" in
        3.10|3.11|3.12|3.13) ;;
        *)
            echo "Standalone build requires stable Python 3.10-3.13; found $BOOTSTRAP_VERSION." >&2
            echo "Set NEYROLOC_BUILD_BOOTSTRAP_PYTHON to a compatible interpreter." >&2
            exit 1
            ;;
    esac
    "$BOOTSTRAP_PYTHON" -m venv "$BUILD_VENV"
    "$PYTHON" -m pip install --upgrade pip
    MACOSX_DEPLOYMENT_TARGET="$MACOS_DEPLOYMENT_TARGET" \
        CMAKE_ARGS="${CMAKE_ARGS:--DLLAMA_METAL=on -DCMAKE_OSX_DEPLOYMENT_TARGET=$MACOS_DEPLOYMENT_TARGET}" \
        "$PYTHON" -m pip install -r "$PROJECT_DIR/packaging/requirements-macos-build.txt"
fi

if [[ ! -x "$PYTHON" ]]; then
    echo "Missing build Python: $PYTHON" >&2
    exit 1
fi

PYTHON_VERSION="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$PYTHON_VERSION" in
    3.10|3.11|3.12|3.13) ;;
    *)
        echo "Standalone build requires stable Python 3.10-3.13; found $PYTHON_VERSION." >&2
        exit 1
        ;;
esac

if ! "$PYTHON" -c 'import PySide6, huggingface_hub, llama_cpp, nuitka, openai, pygments, requests, segno' >/dev/null 2>&1; then
    echo "Build dependencies are incomplete in $PYTHON." >&2
    echo "Install packaging/requirements-macos-build.txt or remove packaging/.venv to recreate it." >&2
    exit 1
fi

for tool in codesign file find iconutil otool sips; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Missing required macOS tool: $tool" >&2
        exit 1
    fi
done

mkdir -p "$ICONSET_DIR"
for icon_spec in \
    "16 icon_16x16.png" \
    "32 icon_16x16@2x.png" \
    "32 icon_32x32.png" \
    "64 icon_32x32@2x.png" \
    "128 icon_128x128.png" \
    "256 icon_128x128@2x.png" \
    "256 icon_256x256.png" \
    "512 icon_256x256@2x.png" \
    "512 icon_512x512.png" \
    "1024 icon_512x512@2x.png"; do
    read -r icon_size icon_name <<<"$icon_spec"
    sips -z "$icon_size" "$icon_size" "$ICON_SOURCE" \
        --out "$ICONSET_DIR/$icon_name" >/dev/null
done
iconutil -c icns "$ICONSET_DIR" -o "$ICON_FILE"

MACOSX_DEPLOYMENT_TARGET="$MACOS_DEPLOYMENT_TARGET" \
PYTHONPATH="$PROJECT_DIR/NEYROLOCK_5${PYTHONPATH:+:$PYTHONPATH}" \
    "$PYTHON" -m nuitka "${NUITKA_ARGS[@]}"

APP_PATH="$(find "$DEPLOYMENT_DIR" -maxdepth 2 -type d -name '*.app' -print -quit)"
if [[ -z "$APP_PATH" ]]; then
    echo "Standalone .app was not produced under $DEPLOYMENT_DIR" >&2
    exit 1
fi

# frpc is a separately downloaded, gitignored executable. Include it when the
# builder has installed it, then refresh the ad-hoc signature of the bundle.
if [[ -x "$FRPC_BINARY" ]]; then
    MOBILE_HTML="$(find "$APP_PATH/Contents" -type f -path '*/resources/mobile.html' -print -quit)"
    if [[ -z "$MOBILE_HTML" ]]; then
        echo "Bundled mobile.html was not found." >&2
        exit 1
    fi
    RUNTIME_ROOT="${MOBILE_HTML%/resources/mobile.html}"
    mkdir -p "$RUNTIME_ROOT/resources/bin"
    cp "$FRPC_BINARY" "$RUNTIME_ROOT/resources/bin/frpc"
    chmod 0755 "$RUNTIME_ROOT/resources/bin/frpc"
fi

APP_EXECUTABLE="$APP_PATH/Contents/MacOS/NEYROLOC_NEW"
BUNDLED_LLAMA="$(find "$APP_PATH/Contents" -type f -name 'libllama.dylib' -print -quit)"
test -x "$APP_EXECUTABLE"
test -n "$BUNDLED_LLAMA"
while IFS= read -r -d '' bundled_file; do
    if file "$bundled_file" | grep -q 'Mach-O'; then
        verify_macos_target "$bundled_file"
    fi
done < <(find "$APP_PATH/Contents" -type f -print0)

codesign --force --deep --sign - "$APP_PATH"
codesign --verify --deep --strict "$APP_PATH"
test -f "$(find "$APP_PATH/Contents" -type f -path '*/resources/mobile.html' -print -quit)"
test -f "$(find "$APP_PATH/Contents" -type f -path '*/packaging/android/NEYROLOC.apk' -print -quit)"
echo "Standalone app: $APP_PATH"
