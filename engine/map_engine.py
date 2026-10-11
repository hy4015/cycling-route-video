import math
from PIL import Image, ImageDraw, ImageFont

W_HALF, H = 960, 1080

def compute_track_projection(points, canvas_w=960, canvas_h=1080, padding=120):
    """
    Projects geographic lat/lon points to pixel coordinates on canvas with uniform aspect ratio.
    """
    lats = [p['lat'] for p in points]
    lons = [p['lon'] for p in points]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Avoid zero division
    dlat = max(0.0001, max_lat - min_lat)
    dlon = max(0.0001, max_lon - min_lon)
    
    # Cosine correction for longitude
    mid_lat = (min_lat + max_lat) / 2.0
    lon_scale = math.cos(math.radians(mid_lat))
    
    geo_w = dlon * lon_scale
    geo_h = dlat
    
    draw_w = canvas_w - 2 * padding
    draw_h = canvas_h - 2 * padding
    
    scale = min(draw_w / max(0.0001, geo_w), draw_h / max(0.0001, geo_h))
    
    cx_geo = (min_lon + max_lon) / 2.0
    cy_geo = (min_lat + max_lat) / 2.0
    cx_pix = canvas_w / 2.0 + 50.0 # Shift right to leave room for left HUD telemetry card
    cy_pix = canvas_h / 2.0
    
    projected = []
    for p in points:
        x = cx_pix + (p['lon'] - cx_geo) * lon_scale * scale
        y = cy_pix - (p['lat'] - cy_geo) * scale # Invert Y for screen coords
        projected.append({
            'x': int(round(x)),
            'y': int(round(y)),
            'ele': p['ele'],
            'dist_km': p['dist_km']
        })
        
    return projected

def create_base_canvas(projected_pts):
    """
    Creates a dark tactical styled canvas with the start marker.
    Full route is revealed progressively with cursor rather than shown upfront.
    """
    canvas = Image.new('RGB', (W_HALF, H), (11, 15, 25))
    draw = ImageDraw.Draw(canvas)
    
    # Start point marker pin
    pts = [(p['x'], p['y']) for p in projected_pts]
    if len(pts) >= 1:
        sx, sy = pts[0]
        draw.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), fill=(16, 185, 129), outline=(255, 255, 255), width=2)
        
    return canvas

# Curated Minimalist Geographic Landmarks Database (Core Cities & Key Cycling Nodes)
GEOGRAPHIC_LANDMARKS = [
    # === TAIWAN TIER 1 CITIES ===
    {"name": "台北", "tier": 1, "lat": 25.0330, "lon": 121.5654},
    {"name": "基隆", "tier": 1, "lat": 25.1350, "lon": 121.7450},
    {"name": "桃园", "tier": 1, "lat": 25.0600, "lon": 121.1200},
    {"name": "新竹", "tier": 1, "lat": 24.8150, "lon": 120.9350},
    {"name": "苗栗", "tier": 1, "lat": 24.5650, "lon": 120.7250},
    {"name": "台中", "tier": 1, "lat": 24.2650, "lon": 120.5550},
    {"name": "彰化", "tier": 1, "lat": 24.0600, "lon": 120.4400},
    {"name": "云林", "tier": 1, "lat": 23.7600, "lon": 120.3500},
    {"name": "嘉义", "tier": 1, "lat": 23.4700, "lon": 120.3200},
    {"name": "台南", "tier": 1, "lat": 22.9997, "lon": 120.1950},
    {"name": "高雄", "tier": 1, "lat": 22.6273, "lon": 120.2850},
    {"name": "台东", "tier": 1, "lat": 22.7583, "lon": 121.1500},
    {"name": "花莲", "tier": 1, "lat": 23.9872, "lon": 121.6100},
    {"name": "宜兰", "tier": 1, "lat": 24.7570, "lon": 121.7650},
    # === TAIWAN TIER 2 ICONIC NODES ===
    {"name": "恒春", "tier": 2, "lat": 22.0042, "lon": 120.7444},
    {"name": "寿卡", "tier": 2, "lat": 22.2478, "lon": 120.8647},
    {"name": "池上", "tier": 2, "lat": 23.1239, "lon": 121.2200},
    {"name": "瑞穗", "tier": 2, "lat": 23.4975, "lon": 121.3850},
    {"name": "苏澳", "tier": 2, "lat": 24.5956, "lon": 121.8519},
    {"name": "淡水", "tier": 2, "lat": 25.1850, "lon": 121.4400},
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def compute_route_landmarks(points, projected_pts):
    lats = [p['lat'] for p in points]
    lons = [p['lon'] for p in points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    dlat = max(0.0001, max_lat - min_lat)
    dlon = max(0.0001, max_lon - min_lon)
    mid_lat = (min_lat + max_lat) / 2.0
    lon_scale = math.cos(math.radians(mid_lat))
    geo_w, geo_h = dlon * lon_scale, dlat
    draw_w, draw_h = W_HALF - 240, H - 240
    scale = min(draw_w / max(0.0001, geo_w), draw_h / max(0.0001, geo_h))
    cx_geo, cy_geo = (min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0
    cx_pix, cy_pix = W_HALF / 2.0 + 50.0, H / 2.0 # Shift right to leave room for left HUD telemetry card
    
    matched = []
    for lm in GEOGRAPHIC_LANDMARKS:
        min_d = 99999
        best_i = 0
        band_min_lon = 999.0
        band_max_lon = -999.0
        step = max(1, len(points) // 2000)
        for i in range(0, len(points), step):
            d = haversine(lm["lat"], lm["lon"], points[i]['lat'], points[i]['lon'])
            if d < min_d:
                min_d = d
                best_i = i
            if abs(points[i]['lat'] - lm["lat"]) <= 0.18:
                if points[i]['lon'] < band_min_lon:
                    band_min_lon = points[i]['lon']
                if points[i]['lon'] > band_max_lon:
                    band_max_lon = points[i]['lon']
        mid_lon = (band_min_lon + band_max_lon) / 2.0 if band_min_lon < 900 else (min_lon + max_lon) / 2.0
        x = cx_pix + (lm['lon'] - cx_geo) * lon_scale * scale
        y = cy_pix - (lm['lat'] - cy_geo) * scale
        if 15 <= x <= W_HALF - 15 and 15 <= y <= H - 15:
            matched.append({
                "name": lm["name"],
                "tier": lm["tier"],
                "dist_km": min_d,
                "prefer_left": lm["lon"] <= mid_lon,
                "is_on_route": min_d <= 22.0,
                "idx": best_i,
                "x": int(round(x)),
                "y": int(round(y))
            })
    return matched

def draw_city_landmarks(draw, landmarks, curr_idx, total_pts, f_idx, fonts):
    if not landmarks:
        return
    f_hud_title, f_hud_sub, f_hud_lbl, f_hud_val, f_trophy_title, f_trophy_sub = fonts
    pass_window = max(14, int(total_pts * 0.011))
    occupied = [{"x": 18, "y": 30, "w": 250, "h": 305}]
    draw_list = []
    placed_dots = []
    MIN_DOT_DIST = 36

    # Single-focus active detection: at most ONE city highlighted at any moment
    best_active_lm = None
    best_active_diff = 999999
    for lm in landmarks:
        if lm.get("is_on_route", True):
            diff = abs(curr_idx - lm["idx"])
            if diff <= pass_window and diff < best_active_diff:
                best_active_diff = diff
                best_active_lm = lm

    sorted_lms = sorted(landmarks, key=lambda lm: (
        0 if (lm is best_active_lm) else (1 if lm["tier"] == 1 else 2),
        lm["dist_km"]
    ))
    
    for lm in sorted_lms:
        is_active = (lm is best_active_lm)
        is_on_route = lm.get("is_on_route", True)
        is_passed = is_on_route and (curr_idx > (lm["idx"] + pass_window))

        if not is_active:
            too_close = False
            for px, py in placed_dots:
                if math.hypot(lm["x"] - px, lm["y"] - py) < MIN_DOT_DIST:
                    too_close = True
                    break
            if too_close:
                continue

        label = lm["name"]
        font = f_hud_sub if is_active else f_hud_lbl
        try:
            bbox = font.getbbox(label)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = len(label) * 11, 13
        pad_x = 7 if is_active else 3
        w, h = tw + pad_x * 2, max(18, th + (8 if is_active else 4))
        
        cand_r = {"x": lm["x"] + 8, "y": lm["y"] - h // 2, "w": w, "h": h, "pos": "R"}
        cand_l = {"x": lm["x"] - 8 - w, "y": lm["y"] - h // 2, "w": w, "h": h, "pos": "L"}
        cand_t = {"x": lm["x"] - w // 2, "y": lm["y"] - 9 - h, "w": w, "h": h, "pos": "T"}
        cand_b = {"x": lm["x"] - w // 2, "y": lm["y"] + 9, "w": w, "h": h, "pos": "B"}

        prefer_left = lm.get("prefer_left", lm["x"] < 520)
        candidates = [cand_l, cand_r, cand_t, cand_b] if prefer_left else [cand_r, cand_l, cand_t, cand_b]

        chosen = None
        for cand in candidates:
            if cand["x"] < 12 or cand["x"] + cand["w"] > W_HALF - 12 or cand["y"] < 12 or cand["y"] + cand["h"] > H - 12:
                continue
            coll = False
            for occ in occupied:
                if not (cand["x"] + cand["w"] < occ["x"] or cand["x"] > occ["x"] + occ["w"] or cand["y"] + cand["h"] < occ["y"] or cand["y"] > occ["y"] + occ["h"]):
                    coll = True
                    break
            if not coll:
                chosen = cand
                break
        if not chosen and is_active:
            chosen = cand_l if prefer_left else cand_r
        if chosen:
            placed_dots.append((lm["x"], lm["y"]))
            occupied.append({"x": chosen["x"] - 10, "y": chosen["y"] - 6, "w": chosen["w"] + 20, "h": chosen["h"] + 12})
            draw_list.append((lm, label, font, chosen, is_active, is_passed))
            
    for lm, label, font, box, is_active, is_passed in draw_list:
        lx, ly = lm["x"], lm["y"]
        bx, by, bw, bh = box["x"], box["y"], box["w"], box["h"]
        if is_active:
            pulse = math.sin(f_idx * 0.3)
            r1 = max(4, int(8 + 3.5 * pulse))
            draw.ellipse((lx - r1, ly - r1, lx + r1, ly + r1), outline=(56, 189, 248), width=2)
            draw.ellipse((lx - 4, ly - 4, lx + 4, ly + 4), fill=(56, 189, 248), outline=(255, 255, 255), width=1)
            draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=5, fill=(15, 23, 42), outline=(56, 189, 248), width=1)
            draw.text((bx + 7, by + 3), label, fill=(125, 211, 252), font=font)
        else:
            r = 2 if lm["tier"] == 1 else 2
            dot_col = (186, 230, 253) if is_passed else ((241, 245, 249) if lm["tier"] == 1 else (148, 163, 184))
            draw.ellipse((lx - r, ly - r, lx + r, ly + r), fill=dot_col, outline=(15, 23, 42), width=1)
            txt_col = (224, 242, 254) if is_passed else ((241, 245, 249) if lm["tier"] == 1 else (148, 163, 184))
            # Soft dark text halo without boxy borders
            tx, ty = bx + 3, by + 2
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                draw.text((tx + dx, ty + dy), label, fill=(11, 15, 25), font=font)
            draw.text((tx, ty), label, fill=txt_col, font=font)

def render_map_frame(base_img, projected_pts, progress, f_idx, stage_info, gpx_summary, fonts, hud_title='CYCLING ROUTE RECAP', landmarks=None):
    """
    Renders left-half map frame with dynamic telemetry HUD, live glowing route, rider pulse, and city landmarks.
    """
    frame = base_img.copy()
    draw = ImageDraw.Draw(frame)
    f_hud_title, f_hud_sub, f_hud_lbl, f_hud_val, f_trophy_title, f_trophy_sub = fonts
    
    total_pts = len(projected_pts)
    curr_pt_idx = min(total_pts - 1, int(progress * (total_pts - 1)))
    
    # 1. Glowing active trajectory line
    pts_sub = [(projected_pts[i]['x'], projected_pts[i]['y']) for i in range(curr_pt_idx + 1)]
    if len(pts_sub) >= 2:
        draw.line(pts_sub, fill=(244, 63, 94, 90), width=9)
        draw.line(pts_sub, fill=(255, 100, 130), width=5)
        draw.line(pts_sub, fill=(255, 255, 255), width=2)
        
    # 2. Pulsating cyan rider head
    hx, hy = projected_pts[curr_pt_idx]['x'], projected_pts[curr_pt_idx]['y']
    pulse = 1.0 + 0.3 * math.sin(f_idx * 0.25)
    r_outer = int(14 * pulse)
    draw.ellipse((hx - r_outer, hy - r_outer, hx + r_outer, hy + r_outer), fill=(6, 182, 212, 100), outline=(56, 189, 248), width=2)
    draw.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), fill=(255, 255, 255), outline=(14, 165, 233), width=2)

    # 2.5 City and town landmarks
    if landmarks:
        draw_city_landmarks(draw, landmarks, curr_pt_idx, total_pts, f_idx, fonts)
    
    # 3. HUD Telemetry Card (top left)
    hud_x, hud_y = 36, 44
    hud_w, hud_h = 248, 230
    draw.rounded_rectangle((hud_x, hud_y, hud_x + hud_w, hud_y + hud_h), radius=12, fill=(15, 23, 42, 220), outline=(51, 65, 85), width=1)
    
    # Top title tag with custom hud_title support
    tag_str = (hud_title or 'CYCLING ROUTE RECAP').strip()
    tb = f_hud_title.getbbox(tag_str)
    tw = tb[2] - tb[0]
    tag_pill_w = max(120, min(hud_w - 20, tw + 24))
    draw.rounded_rectangle((hud_x + 10, hud_y + 10, hud_x + 10 + tag_pill_w, hud_y + 36), radius=6, fill=(225, 29, 72))
    draw.text((hud_x + 10 + (tag_pill_w - tw) // 2, hud_y + 16), tag_str, fill=(255, 255, 255), font=f_hud_title)
    
    # Stage name
    s_name = stage_info.get('name', 'ROAD TRIP')
    draw.text((hud_x + 14, hud_y + 44), s_name, fill=(56, 189, 248), font=f_hud_sub)
    
    # Metrics
    curr_ele = projected_pts[curr_pt_idx]['ele']
    dist_cum = progress * gpx_summary['total_distance_km']
    climb_cum = int(progress * gpx_summary['total_climb_m'])
    curr_spd = 24.5 + 4.0 * math.sin(f_idx * 0.1)
    
    metrics = [
        ('实时速度', f'{curr_spd:.1f} km/h', (56, 189, 248)),
        ('累计爬升', f'{climb_cum} m', (52, 211, 153)),
        ('实时海拔', f'{curr_ele:.1f} m', (248, 250, 252)),
        ('总里程', f'{dist_cum:.2f} km', (255, 255, 255))
    ]
    
    my = hud_y + 72
    for lbl, val, col in metrics:
        draw.text((hud_x + 14, my), lbl, fill=(148, 163, 184), font=f_hud_lbl)
        vb = f_hud_val.getbbox(val)
        vw = vb[2] - vb[0]
        draw.text((hud_x + hud_w - 14 - vw, my - 2), val, fill=col, font=f_hud_val)
        my += 28
        
    # 4. Victory Plaque at bottom left for completion (progress >= 0.96)
    if progress >= 0.96:
        p_w, p_h = 428, 72
        px1, py1 = 36, H - 120
        px2, py2 = px1 + p_w, py1 + p_h
        draw.rounded_rectangle((px1, py1, px2, py2), radius=16, fill=(15, 23, 42), outline=(245, 158, 11), width=3)
        title_str = f"★ {gpx_summary['total_distance_km']:.1f} km 骑行达成！"
        tb = f_trophy_title.getbbox(title_str)
        tw = tb[2] - tb[0]
        sub_str = f"爬升 {gpx_summary['total_climb_m']}m · 最高海拔 {gpx_summary['max_ele_m']}m · 完赛率 100%"
        sb = f_trophy_sub.getbbox(sub_str)
        sw = sb[2] - sb[0]
        draw.text((px1 + (p_w - tw) // 2, py1 + 13), title_str, fill=(251, 191, 36), font=f_trophy_title)
        draw.text((px1 + (p_w - sw) // 2, py1 + 45), sub_str, fill=(226, 232, 240), font=f_trophy_sub)
        
    return frame
