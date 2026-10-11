#!/bin/bash
# Сборка NEYROLOC.apk без Gradle: aapt2 -> javac -> d8 -> zip -> zipalign -> apksigner.
# Требует: JDK, Android SDK в ~/android-sdk (build-tools;34.0.0 + platforms;android-34).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
BT="$SDK/build-tools/36.0.0"
PLATFORM="$SDK/platforms/android-34/android.jar"
OUT="$HERE/build"
PROJECT_DIR="$(cd "$HERE/../.." && pwd)"
FONT_SOURCE="$PROJECT_DIR/NEYROLOCK_5/resources/fonts"
FONT_ASSETS="$OUT/assets/fonts"

rm -rf "$OUT"
mkdir -p "$OUT/compiled" "$OUT/gen" "$OUT/classes"

for font_file in Onest-Regular.ttf Onest-Bold.ttf OFL.txt; do
    [ -f "$FONT_SOURCE/$font_file" ] || {
        echo "Не найден обязательный font asset: $FONT_SOURCE/$font_file" >&2
        exit 1
    }
done
mkdir -p "$FONT_ASSETS"
cp "$FONT_SOURCE/Onest-Regular.ttf" "$FONT_ASSETS/Onest-Regular.ttf"
cp "$FONT_SOURCE/Onest-Bold.ttf" "$FONT_ASSETS/Onest-Bold.ttf"
cp "$FONT_SOURCE/OFL.txt" "$FONT_ASSETS/OFL.txt"

echo "[1/6] aapt2 compile+link (ресурсы, манифест, R.java)"
"$BT/aapt2" compile --dir "$HERE/res" -o "$OUT/compiled/res.zip"
"$BT/aapt2" link \
    -I "$PLATFORM" \
    --manifest "$HERE/AndroidManifest.xml" \
    -o "$OUT/base.apk" \
    --java "$OUT/gen" \
    -A "$OUT/assets" \
    "$OUT/compiled/res.zip"

echo "[2/6] javac"
javac --release 8 -classpath "$PLATFORM" -d "$OUT/classes" \
    "$OUT/gen/ru/dorryn/neyroloc/R.java" \
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

echo "[6/6] подпись (debug-ключ)"
KEYSTORE="$HERE/debug.keystore"
if [ ! -f "$KEYSTORE" ]; then
    keytool -genkeypair -keystore "$KEYSTORE" -storepass android -keypass android \
        -alias androiddebugkey -dname "CN=NEYROLOC Debug" \
        -keyalg RSA -keysize 2048 -validity 10000
fi
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android \
    --out "$HERE/NEYROLOC.apk" "$OUT/aligned.apk"

echo "Готово: $HERE/NEYROLOC.apk"
