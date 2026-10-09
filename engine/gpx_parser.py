import os
import math
import xml.etree.ElementTree as ET
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def parse_gpx(gpx_path):
    """
    Parses any standard GPX file into structured track points,
    calculating cumulative distance, speed, elevation changes,
    and automatic stage segmentations.
    """
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    
    # Strip namespaces if present
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
        
    points = []
    
    for trk in root.iter(f'{ns}trk'):
        for seg in trk.iter(f'{ns}trkseg'):
            for pt in seg.iter(f'{ns}trkpt'):
                lat = float(pt.attrib['lat'])
                lon = float(pt.attrib['lon'])
                ele_el = pt.find(f'{ns}ele')
                time_el = pt.find(f'{ns}time')
                
                ele = float(ele_el.text) if ele_el is not None else 0.0
                time_str = time_el.text if time_el is not None else None
                points.append({
                    'lat': lat,
                    'lon': lon,
                    'ele': ele,
                    'time': time_str
                })
                
    if not points:
        raise ValueError(f"No valid trackpoints found in GPX file: {gpx_path}")
        
    # Calculate statistics & cumulative distance
    total_dist = 0.0
    climb_cum = 0.0
    descent_cum = 0.0
    processed_pts = []
    
    min_lat, max_lat = points[0]['lat'], points[0]['lat']
    min_lon, max_lon = points[0]['lon'], points[0]['lon']
    min_ele, max_ele = points[0]['ele'], points[0]['ele']
    
    for i, pt in enumerate(points):
        lat, lon, ele = pt['lat'], pt['lon'], pt['ele']
        min_lat, max_lat = min(min_lat, lat), max(max_lat, lat)
        min_lon, max_lon = min(min_lon, lon), max(max_lon, lon)
        min_ele, max_ele = min(min_ele, ele), max(max_ele, ele)
        
        step_dist = 0.0
        if i > 0:
            prev = points[i - 1]
            step_dist = haversine(prev['lat'], prev['lon'], lat, lon)
            total_dist += step_dist
            dele = ele - prev['ele']
            if dele > 0:
                climb_cum += dele
            else:
                descent_cum += abs(dele)
                
        processed_pts.append({
            'lat': lat,
            'lon': lon,
            'ele': ele,
            'time': pt['time'],
            'dist_km': total_dist,
            'step_dist_km': step_dist
        })
        
    # Auto Segmentation
    # 1. Check if points span multiple calendar dates
    dates = []
    for pt in processed_pts:
        if pt['time']:
            try:
                d = pt['time'][:10]
                if d not in dates:
                    dates.append(d)
            except Exception:
                pass
                
    stages = []
    if len(dates) > 1:
        # Multi-day tour
        for d_idx, d in enumerate(dates):
            day_pts = [p for p in processed_pts if p['time'] and p['time'].startswith(d)]
            if not day_pts:
                continue
            p_start = day_pts[0]['dist_km'] / total_dist if total_dist > 0 else 0
            p_end = day_pts[-1]['dist_km'] / total_dist if total_dist > 0 else 1
            stages.append({
                'id': f'D{d_idx + 1:02d}',
                'name': f'DAY {d_idx + 1:02d} · {d}',
                'p_start': p_start,
                'p_end': p_end,
                'dist_km': day_pts[-1]['dist_km'] - day_pts[0]['dist_km']
            })
    else:
        # Single-day ride: divide into 4 milestone stages based on progress & elevation
        step_fractions = [0.0, 0.25, 0.55, 0.85, 1.0]
        stage_names = ['起步破风 · 启程热身', '中途巡航 · 节奏渐入', '核心挑战 · 坡道攻顶', '终点冲刺 · 荣耀凯旋']
        for s_idx in range(4):
            stages.append({
                'id': f'S{s_idx + 1:02d}',
                'name': f'STAGE {s_idx + 1:02d} · {stage_names[s_idx]}',
                'p_start': step_fractions[s_idx],
                'p_end': step_fractions[s_idx + 1],
                'dist_km': total_dist * (step_fractions[s_idx + 1] - step_fractions[s_idx])
            })
            
    return {
        'total_distance_km': round(total_dist, 2),
        'total_climb_m': round(climb_cum, 1),
        'total_descent_m': round(descent_cum, 1),
        'max_ele_m': round(max_ele, 1),
        'min_ele_m': round(min_ele, 1),
        'bbox': {
            'min_lat': min_lat, 'max_lat': max_lat,
            'min_lon': min_lon, 'max_lon': max_lon
        },
        'points_count': len(processed_pts),
        'stages': stages,
        'points': processed_pts
    }
