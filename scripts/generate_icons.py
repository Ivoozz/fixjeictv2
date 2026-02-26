#!/usr/bin/env python3
"""Generate PWA icons for FixJeICT"""

import base64

# Simple 1x1 transparent PNG (minimal valid PNG)
TRANSPARENT_PNG_1x1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
)

def create_icon(size, color='#667eea'):
    """Create a simple colored square icon"""
    # For now, we'll create a minimal PNG
    # In production, these should be replaced with proper icons
    filename = f'/home/engine/project/fixjeict_app/static/images/icon-{size}.png'
    with open(filename, 'wb') as f:
        f.write(TRANSPARENT_PNG_1x1)
    print(f"Created placeholder icon: {filename}")

if __name__ == '__main__':
    create_icon(192)
    create_icon(512)
    print("\nNote: These are placeholder icons. Replace them with proper PWA icons.")
    print("Recommended: Use a service like https://realfavicongenerator.net/")
