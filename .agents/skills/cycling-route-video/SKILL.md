---
name: cycling-route-video
description: >-
  Universal generator for turning any cycling GPX roadbook, photos, and short videos into a
  professional dual-screen recap video with animated route telemetry and vintage Kodak Portra 400 filmstrip.
  Use when the user wants to generate, edit, or customize a cycling recap video from a GPX file and media assets.
---

# Universal Cycling Route Video Skill

This skill provides an automated, end-to-end pipeline to transform any cycling GPX roadbook track and trip media (photos and videos) into a synchronized 1080P recap video.

## Pipeline Highlights

1. **Left Screen (Map & Telemetry HUD, 960x1080)**:
   - Dynamic track projection auto-scaled to route bounding box.
   - Real-time glowing route progression with pulsating cyan rider marker.
   - Live telemetry card (real-time speed, cumulative climb, current elevation, total distance).
   - Golden trophy plaque upon completion (`★ XX.X km 骑行达成！`).

2. **Right Screen (Vintage Kodak Portra 400 Filmstrip, 960x1080)**:
   - Authentic sprocket hole borders on margins.
   - **Kodak 400 Gap Typography**:
     - `KODAK PORTRA 400` in golden yellow.
     - `SAFETY FILM` in subtle gray.
     - `• xxA • ►` frame counter and polygon arrow.
     - Strictly located inside the 44px gap between media items (100% clean media content).
   - Dual magazine collage for vertical media (428x484 each) & full bleed for horizontal media (872x484).
   - 100% upright EXIF rotation guarantee.

3. **Audio Master**:
   - Built-in highway acoustic guitar, coastal beat, or epic mountain tracks.
   - Video clips play ambient audio at 80% volume with 0.3s fade-in and fade-out.

---

## Quick Usage

### 1. Command-Line Rendering (Local CPU/GPU Accelerated)

```bash
# Basic usage
python3 -m engine.pipeline \
  --gpx "/path/to/my_route.gpx" \
  --media "/path/to/photos_and_videos" \
  --output "./cycling_recap.mp4"

# Custom BGM and Duration
python3 -m engine.pipeline \
  --gpx "/path/to/my_route.gpx" \
  --media "/path/to/photos_and_videos" \
  --output "./cycling_recap.mp4" \
  --bgm coastal \
  --duration 60.0
```

### 2. Cloudflare Pages Web UI (Browser-based, Zero Install)

Deploy the `web/` directory to **Cloudflare Pages**:
- **Build command**: None (pure static modern ESM / Tailwind)
- **Output directory**: `web`
- **Upload protection limits**:
  - Images: $\le 10\text{MB}$ each
  - Videos: $\le 100\text{MB}$ and $\le 10\text{s}$ duration

### 3. macOS Desktop App (.dmg)

```bash
cd desktop
npm install
npm run dist
# Output DMG will be generated in desktop/dist/
```
