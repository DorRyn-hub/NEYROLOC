#!/usr/bin/env python3
"""
Create placeholder icon for NEYROLOCK
This creates a simple icon with the letter "N" if no icon exists
"""

import os
from pathlib import Path

def create_placeholder_icon():
    """
    Create a placeholder SVG icon that can be converted to PNG/ICO/ICNS
    """
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    icon_svg = assets_dir / "icon.svg"

    if icon_svg.exists():
        print(f"Icon already exists: {icon_svg}")
        print("Skipping creation. Delete existing icon to recreate.")
        return

    # Create a simple SVG icon with "N" letter
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- Background gradient -->
  <defs>
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="letter-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#e0e7ff;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Background rounded rectangle -->
  <rect width="512" height="512" rx="100" fill="url(#bg-gradient)"/>

  <!-- Letter N -->
  <text
    x="256"
    y="380"
    font-family="Arial, Helvetica, sans-serif"
    font-size="380"
    font-weight="bold"
    text-anchor="middle"
    fill="url(#letter-gradient)"
    stroke="#4c1d95"
    stroke-width="8">N</text>

  <!-- Small brain icon (neural network symbol) -->
  <circle cx="410" cy="120" r="50" fill="#f59e0b" opacity="0.9"/>
  <circle cx="390" cy="110" r="15" fill="#ffffff"/>
  <circle cx="415" cy="115" r="12" fill="#ffffff"/>
  <circle cx="420" cy="135" r="10" fill="#ffffff"/>

  <!-- Lock icon (security symbol) -->
  <rect x="85" y="420" width="70" height="60" rx="10" fill="#10b981" opacity="0.9"/>
  <rect x="95" y="430" width="50" height="40" rx="5" fill="#065f46"/>
  <circle cx="120" cy="405" r="20" fill="none" stroke="#10b981" stroke-width="8"/>
</svg>'''

    with open(icon_svg, 'w') as f:
        f.write(svg_content)

    print(f"✅ Created placeholder icon: {icon_svg}")
    print("\nNext steps:")
    print("1. Convert SVG to PNG (512x512):")
    print("   - Use an online converter: https://cloudconvert.com/svg-to-png")
    print("   - Or use ImageMagick: convert icon.svg -resize 512x512 icon.png")
    print("\n2. Create Windows icon (.ico):")
    print("   - Use: https://icoconvert.com/")
    print("   - Or ImageMagick: convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico")
    print("\n3. Create macOS icon (.icns):")
    print("   - Use: https://cloudconvert.com/png-to-icns")
    print("   - Or on macOS: see assets/README.md for instructions")
    print("\n4. Or use your own custom icon instead!")

def check_icons():
    """
    Check which icon files exist
    """
    assets_dir = Path(__file__).parent / "assets"

    icons = {
        "SVG": assets_dir / "icon.svg",
        "PNG": assets_dir / "icon.png",
        "ICO": assets_dir / "icon.ico",
        "ICNS": assets_dir / "icon.icns",
    }

    print("\n📊 Icon Status:")
    print("-" * 40)

    for name, path in icons.items():
        status = "✅ Exists" if path.exists() else "❌ Missing"
        print(f"{name:6} (.{path.suffix[1:]}): {status}")

    print("-" * 40)

    all_exist = all(path.exists() for name, path in icons.items() if name != "SVG")

    if all_exist:
        print("\n🎉 All required icons exist!")
        print("You're ready to build installers!")
    else:
        print("\n⚠️  Some icons are missing")
        print("Installers will work but may use default icons")
        print("\nRun this script to create placeholder icons:")
        print("  python create_placeholder_icon.py")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_icons()
    else:
        print("=" * 50)
        print("NEYROLOCK Placeholder Icon Creator")
        print("=" * 50)
        print()

        create_placeholder_icon()
        check_icons()

        print("\n💡 Tip: For a professional icon, consider:")
        print("   - Hiring a designer on Fiverr (~$10-50)")
        print("   - Using free icon resources (see assets/README.md)")
        print("   - Creating your own in Inkscape or Illustrator")
