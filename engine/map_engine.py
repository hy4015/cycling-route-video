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
    cx_pix = canvas_w / 2.0
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
    Creates a dark tactical styled canvas with the ghost route silhouette.
    """
    canvas = Image.new('RGB', (W_HALF, H), (11, 15, 25))
    draw = ImageDraw.Draw(canvas)
    
    # Draw faint route backdrop
    pts = [(p['x'], p['y']) for p in projected_pts]
    if len(pts) >= 2:
        draw.line(pts, fill=(30, 41, 59), width=8)
        draw.line(pts, fill=(51, 65, 85), width=3)
        
    # Start and End markers
    sx, sy = pts[0]
    ex, ey = pts[-1]
    draw.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=(16, 185, 129), outline=(255, 255, 255), width=2)
    draw.ellipse((ex - 7, ey - 7, ex + 7, ey + 7), fill=(239, 68, 68), outline=(255, 255, 255), width=2)
    
    return canvas

def render_map_frame(base_img, projected_pts, progress, f_idx, stage_info, gpx_summary, fonts, hud_title='CYCLING ROUTE RECAP'):
    """
    Renders left-half map frame with dynamic telemetry HUD, live glowing route, and rider pulse.
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
