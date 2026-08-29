import os
import sys

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b" />
      <stop offset="50%" stop-color="#2e1065" />
      <stop offset="100%" stop-color="#581c87" />
    </linearGradient>
    <linearGradient id="camGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#3b82f6" />
    </linearGradient>
    <linearGradient id="recGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ef4444" />
      <stop offset="100%" stop-color="#dc2626" />
    </linearGradient>
    <linearGradient id="noteGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#6d28d9" />
    </linearGradient>
  </defs>

  <!-- Rounded Background -->
  <rect x="16" y="16" width="480" height="480" rx="108" ry="108" fill="url(#bgGrad)" stroke="#7c3aed" stroke-width="6" />

  <!-- Outer Cyan Aperture Ring -->
  <circle cx="256" cy="240" r="140" fill="none" stroke="url(#camGrad)" stroke-width="12" stroke-dasharray="28 14" opacity="0.9" />

  <!-- Document / Study Notes Page -->
  <rect x="166" y="120" width="180" height="230" rx="18" ry="18" fill="#ffffff" fill-opacity="0.96" />
  <rect x="196" y="155" width="120" height="12" rx="6" fill="#475569" />
  <rect x="196" y="180" width="100" height="10" rx="5" fill="#64748b" />
  <rect x="196" y="202" width="115" height="10" rx="5" fill="#64748b" />
  <rect x="196" y="224" width="75" height="10" rx="5" fill="#0284c7" />

  <!-- Video Camera Body -->
  <rect x="125" y="260" width="175" height="125" rx="26" ry="26" fill="url(#noteGrad)" stroke="#a855f7" stroke-width="3" />
  <!-- Lens Cone -->
  <path d="M 300 295 L 380 255 A 4 4 0 0 1 386 259 L 386 386 A 4 4 0 0 1 300 350 Z" fill="url(#noteGrad)" stroke="#a855f7" stroke-width="3" />

  <!-- Glowing REC Indicator -->
  <circle cx="165" cy="298" r="16" fill="url(#recGrad)" />
  <circle cx="165" cy="298" r="8" fill="#ffffff" opacity="0.9" />

  <!-- Microphone Icon on Camera -->
  <rect x="215" y="290" width="22" height="36" rx="11" fill="#ffffff" opacity="0.95" />
  <path d="M 209 310 A 17 17 0 0 0 243 310" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" />
  <line x1="226" y1="327" x2="226" y2="337" stroke="#ffffff" stroke-width="4" stroke-linecap="round" />

  <!-- AI Sparkles -->
  <path d="M 390 110 Q 390 140 420 140 Q 390 140 390 170 Q 390 140 360 140 Q 390 140 390 110 Z" fill="#fbbf24" />
  <path d="M 115 110 Q 115 130 135 130 Q 115 130 115 150 Q 115 130 95 130 Q 115 130 115 110 Z" fill="#38bdf8" />
</svg>
"""

def generate_icons():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assets_dir = os.path.join(project_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    svg_path = os.path.join(assets_dir, "icon.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_CONTENT)
    print(f"Saved SVG icon: {svg_path}")

    sizes = [512, 256, 128, 64, 48, 32]
    for sz in sizes:
        png_path = os.path.join(assets_dir, f"icon_{sz}.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(svg_path, sz, sz, True)
        pixbuf.savev(png_path, "png", [], [])
        print(f"Generated PNG icon ({sz}x{sz}): {png_path}")

if __name__ == "__main__":
    generate_icons()
