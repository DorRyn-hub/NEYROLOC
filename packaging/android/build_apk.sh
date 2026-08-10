#!/bin/bash
# Сборка NEYROLOC.apk без Gradle: aapt2 -> javac -> d8 -> zip -> zipalign -> apksigner.
# Требует: JDK и Android SDK (build-tools;36.0.0 + platforms;android-36).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
BUILD_TOOLS_VERSION="${NEYROLOC_BUILD_TOOLS_VERSION:-36.0.0}"
PLATFORM_API="${NEYROLOC_ANDROID_API:-36}"
BT="$SDK/build-tools/$BUILD_TOOLS_VERSION"
PLATFORM="$SDK/platforms/android-$PLATFORM_API/android.jar"
OUT="$HERE/build"

for tool in aapt2 d8 zipalign apksigner; do
    [ -x "$BT/$tool" ] || { echo "Не найден $BT/$tool" >&2; exit 1; }
done
[ -f "$PLATFORM" ] || { echo "Не найден Android SDK Platform $PLATFORM_API: $PLATFORM" >&2; exit 1; }

rm -rf "$OUT"
mkdir -p "$OUT/compiled" "$OUT/gen" "$OUT/classes"

echo "[1/6] aapt2 compile+link (ресурсы, манифест, R.java)"
"$BT/aapt2" compile --dir "$HERE/res" -o "$OUT/compiled/res.zip"
"$BT/aapt2" link \
    -I "$PLATFORM" \
    --manifest "$HERE/AndroidManifest.xml" \
    -o "$OUT/base.apk" \
    --java "$OUT/gen" \
    "$OUT/compiled/res.zip"

echo "[2/6] javac"
javac --release 8 -classpath "$PLATFORM" -d "$OUT/classes" \
    "$OUT/gen/ru/dorryn/neyroloc/R.java" \
    "$HERE/src/ru/dorryn/neyroloc/ServerUrl.java" \
    "$HERE/src/ru/dorryn/neyroloc/MainActivity.java"

echo "[3/6] d8 (dex)"
# d8 из build-tools 34 падает с NPE на отдельных .class-файлах под новыми JDK —
# кормим его jar'ом, это стабильный путь.
(cd "$OUT/classes" && jar cf ../classes.jar .)
"$BT/d8" --release --lib "$PLATFORM" --output "$OUT" "$OUT/classes.jar"

echo "[4/6] упаковка classes.dex в apk"
(cd "$OUT" && zip -q -j base.apk classes.dex)

echo "[5/6] zipalign"
"$BT/zipalign" -f 4 "$OUT/base.apk" "$OUT/aligned.apk"

echo "[6/6] подпись"
if [ -n "${NEYROLOC_KEYSTORE:-}" ]; then
    : "${NEYROLOC_KEY_ALIAS:?Задайте NEYROLOC_KEY_ALIAS}"
    : "${NEYROLOC_KEYSTORE_PASS:?Задайте NEYROLOC_KEYSTORE_PASS}"
    : "${NEYROLOC_KEY_PASS:?Задайте NEYROLOC_KEY_PASS}"
    [ -f "$NEYROLOC_KEYSTORE" ] || { echo "Keystore не найден: $NEYROLOC_KEYSTORE" >&2; exit 1; }
    "$BT/apksigner" sign \
        --ks "$NEYROLOC_KEYSTORE" \
        --ks-key-alias "$NEYROLOC_KEY_ALIAS" \
        --ks-pass env:NEYROLOC_KEYSTORE_PASS \
        --key-pass env:NEYROLOC_KEY_PASS \
        --v4-signing-enabled false \
        --out "$HERE/NEYROLOC.apk" "$OUT/aligned.apk"
    echo "Подпись: release keystore"
else
    KEYSTORE="$HERE/debug.keystore"
    if [ ! -f "$KEYSTORE" ]; then
        keytool -genkeypair -keystore "$KEYSTORE" -storepass android -keypass android \
            -alias androiddebugkey -dname "CN=NEYROLOC Debug" \
            -keyalg RSA -keysize 2048 -validity 10000
    fi
    "$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android \
        --v4-signing-enabled false \
        --out "$HERE/NEYROLOC.apk" "$OUT/aligned.apk"
    echo "ВНИМАНИЕ: debug-подпись; для публикации задайте NEYROLOC_KEYSTORE и переменные ключа." >&2
fi
"$BT/apksigner" verify --verbose "$HERE/NEYROLOC.apk" >/dev/null

echo "Готово: $HERE/NEYROLOC.apk"
