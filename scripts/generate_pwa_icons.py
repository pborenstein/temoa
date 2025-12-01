#!/usr/bin/env python3
"""Generate PWA icons from the emoji favicon"""

from pathlib import Path

# Create simple PNG icons with footprints emoji
# These are placeholder icons - in production you might want proper icon design

# For now, we'll create a simple approach: convert the SVG to PNG at different sizes
# This script requires cairosvg or similar. For simplicity, we'll create a note
# about generating these icons manually or using an online tool.

def main():
    ui_dir = Path(__file__).parent.parent / "src" / "temoa" / "ui"
    favicon_svg = ui_dir / "favicon.svg"

    print("PWA Icon Generation Script")
    print("=" * 50)
    print()
    print("To generate PWA icons, you can:")
    print()
    print("1. Use an online tool:")
    print("   - Visit: https://realfavicongenerator.net/")
    print("   - Upload: src/temoa/ui/favicon.svg")
    print("   - Download the generated icon-192.png and icon-512.png")
    print("   - Place them in: src/temoa/ui/")
    print()
    print("2. Use ImageMagick (if installed):")
    print(f"   cd {ui_dir}")
    print("   convert favicon.svg -resize 192x192 icon-192.png")
    print("   convert favicon.svg -resize 512x512 icon-512.png")
    print()
    print("3. Use Python with cairosvg (if installed):")
    print("   pip install cairosvg")
    print("   Then run this script with --generate flag")
    print()

    # Try to generate if cairosvg is available
    try:
        import cairosvg

        print("✓ cairosvg found! Generating icons...")

        # Generate 192x192
        icon_192 = ui_dir / "icon-192.png"
        cairosvg.svg2png(
            url=str(favicon_svg),
            write_to=str(icon_192),
            output_width=192,
            output_height=192
        )
        print(f"  ✓ Created: {icon_192}")

        # Generate 512x512
        icon_512 = ui_dir / "icon-512.png"
        cairosvg.svg2png(
            url=str(favicon_svg),
            write_to=str(icon_512),
            output_width=512,
            output_height=512
        )
        print(f"  ✓ Created: {icon_512}")

        print()
        print("✓ Icons generated successfully!")

    except ImportError:
        print("Note: cairosvg not installed. Use one of the methods above.")
        print("      Or install: pip install cairosvg")

if __name__ == "__main__":
    main()
