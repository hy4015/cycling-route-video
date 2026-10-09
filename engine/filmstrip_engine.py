import os
import math
from PIL import Image, ImageDraw, ImageFont

W_HALF, H = 960, 1080
STRIDE = 528
WIN_W, WIN_H = 872, 484
WIN_R_A = 22
WIN_R_B = 16
W_SUB = 428
GAP_MID = 16

KODAK_YELLOW = (235, 180, 40)
FILM_GRAY = (148, 163, 184)
DARK_BG = (14, 17, 23)

def load_fonts():
    try:
        font_kodak = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 14, index=1)
        font_sub = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 11, index=0)
        font_num = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 15, index=1)
        font_leader_badge = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 13, index=1)
        font_leader_title = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 30, index=2)
        font_leader_sub = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 15, index=0)
        font_leader_mono = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 11, index=0)
    except Exception:
        font_kodak = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_num = ImageFont.load_default()
        font_leader_badge = ImageFont.load_default()
        font_leader_title = ImageFont.load_default()
        font_leader_sub = ImageFont.load_default()
        font_leader_mono = ImageFont.load_default()
    return font_kodak, font_sub, font_num, font_leader_badge, font_leader_title, font_leader_sub, font_leader_mono

FILM_CONFIGS = {
    'portra400': {
        'brand': 'KODAK PORTRA 400',
        'mid': 'SAFETY FILM',
        'accent': (235, 180, 40),
        'num_format': lambda f: f'• {f:02d}A •'
    },
    'gold200': {
        'brand': 'KODAK GOLD 200',
        'mid': 'GB 200',
        'accent': (245, 158, 11),
        'num_format': lambda f: f'200-4 • {f:02d}A'
    },
    'fuji400': {
        'brand': 'FUJIFILM SUPERIA 400',
        'mid': 'COLOR PRINT FILM',
        'accent': (16, 185, 129),
        'num_format': lambda f: f'S-400 • {f:02d}A'
    },
    'ilford400': {
        'brand': 'ILFORD HP5 PLUS',
        'mid': 'PAN 400',
        'accent': (241, 245, 249),
        'num_format': lambda f: f'HP5 • {f:02d}A'
    }
}

def render_filmstrip_frame(t, y_scroll, windows, window_frames, fps, v_actual, masks, fonts, film_style='portra400', hud_title='CYCLING ROUTE RECAP', intro_title='MEMORIES ON THE ROAD · 沿途风光与光影纪实'):
    """
    Renders a single 960x1080 filmstrip frame at time t with film leader intro card.
    """
    mask_a, mask_b = masks
    font_kodak, font_sub, font_num, font_leader_badge, font_leader_title, font_leader_sub, font_leader_mono = fonts
    
    canvas = Image.new('RGB', (W_HALF, H), DARK_BG)
    draw = ImageDraw.Draw(canvas)
    num_windows = len(windows)
    
    wy0 = int(round(0 * STRIDE - y_scroll + 298))
    
    # 0. Leader Slate Background (strictly above photo 0)
    if wy0 > 0:
        leader_h = min(H, wy0)
        for y in range(0, leader_h):
            ratio = y / max(1, wy0)
            r = int(10 + ratio * 4)
            g = int(13 + ratio * 5)
            b = int(20 + ratio * 9)
            draw.line([(0, y), (W_HALF, y)], fill=(r, g, b))
            
    # 1. Render visible media windows
    for k in range(num_windows):
        wy = int(round(k * STRIDE - y_scroll + 298))
        if wy + WIN_H <= 0 or wy >= H:
            continue
            
        win = windows[k]
        w_type = win['type']
        
        t_enter = max(0.0, (k * STRIDE - 782) / v_actual) if k > 0 else 0.0
        t_elapsed = max(0.0, t - t_enter)
        flocal = int(t_elapsed * fps)
        
        if w_type == 'A':
            flist = window_frames[k][0]
            cnt = len(flist)
            im = Image.open(flist[flocal % cnt])
            canvas.paste(im, (44, wy), mask_a)
        else:
            flist_L = window_frames[k][0]
            im_L = Image.open(flist_L[flocal % len(flist_L)])
            canvas.paste(im_L, (44, wy), mask_b)
            
            flist_R = window_frames[k][1]
            im_R = Image.open(flist_R[flocal % len(flist_R)])
            canvas.paste(im_R, (44 + W_SUB + GAP_MID, wy), mask_b)
            
    # 2. Draw sprocket film border tracks & holes (strictly below wy0!)
    if wy0 < H:
        track_top = max(0, wy0)
        draw.rectangle([(0, track_top), (38, H)], fill=(20, 24, 36))
        draw.rectangle([(W_HALF - 38, track_top), (W_HALF, H)], fill=(20, 24, 36))

    for x_sprocket in [8, 930]:
        y_sp = -(int(y_scroll) % 80)
        while y_sp < H + 80:
            if y_sp + 10 >= wy0 - 15:
                draw.rounded_rectangle((x_sprocket, y_sp + 10, x_sprocket + 22, y_sp + 50),
                                       radius=5, fill=(248, 250, 252), outline=(148, 163, 184), width=1)
            y_sp += 80
            
    # 3. 35mm Film Stock Gap Typography (strictly below photo 0, starting from k = 0)
    cfg = FILM_CONFIGS.get(film_style, FILM_CONFIGS['portra400'])
    accent_col = cfg['accent']
    brand_text = cfg['brand']
    mid_text = cfg['mid']

    for k in range(0, num_windows + 1):
        wy = int(round(k * STRIDE - y_scroll + 298))
        gap_y = wy + WIN_H + 13
        if -30 <= gap_y <= H + 30:
            curr_fnum = max(1, k + 1)
            # Left brand
            draw.text((54, gap_y), brand_text, fill=accent_col, font=font_kodak)
            
            # Center label
            mb = font_sub.getbbox(mid_text)
            mw = mb[2] - mb[0]
            draw.text(((W_HALF - mw) // 2, gap_y + 2), mid_text, fill=FILM_GRAY, font=font_sub)
            
            # Right frame number & arrow
            num_str = cfg['num_format'](curr_fnum)
            nb = font_num.getbbox(num_str)
            nw = nb[2] - nb[0]
            draw.text((880 - nw, gap_y), num_str, fill=accent_col, font=font_num)
            arrow_x, arrow_y = 890, gap_y + 8
            draw.polygon([(arrow_x, arrow_y - 5), (arrow_x + 6, arrow_y), (arrow_x, arrow_y + 5)], fill=accent_col)
            
    # 4. Vertical Separation Guide Lines (strictly below wy0)
    if wy0 < H:
        line_top = max(0, wy0)
        draw.line([(38, line_top), (38, H)], fill=(45, 55, 72), width=2)
        draw.line([(922, line_top), (922, H)], fill=(45, 55, 72), width=2)
        
    # 5. Film Leader Intro Title Card (rendered directly above Photo 0)
    if wy0 > -50:
        cx = W_HALF // 2
        
        # A. Top Film Stock Pill Badge
        badge_y = wy0 - 180
        if badge_y > -40:
            badge_txt = f"{brand_text} · LEADER NO. 01"
            tb = font_leader_badge.getbbox(badge_txt)
            text_w = tb[2] - tb[0]
            dot_r = 3
            dot_gap = 8
            pad_x = 14
            pill_h = 26
            content_w = (dot_r * 2) + dot_gap + text_w
            pill_w = content_w + pad_x * 2
            pill_x = int(round(cx - pill_w / 2))
            pill_y = int(round(badge_y - pill_h / 2))

            draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                                   radius=pill_h // 2, fill=(15, 20, 30), outline=accent_col, width=1)
            draw.ellipse((pill_x + pad_x, pill_y + pill_h//2 - dot_r, pill_x + pad_x + dot_r*2, pill_y + pill_h//2 + dot_r), fill=accent_col)
            draw.text((pill_x + pad_x + dot_r*2 + dot_gap, pill_y + 6), badge_txt, fill=accent_col, font=font_leader_badge)
            
        # B. Main Route Title (包含线路左上角抬头文字)
        title_y = wy0 - 125
        if title_y > -40:
            main_title_str = (hud_title or 'CYCLING ROUTE RECAP').strip()
            tb = font_leader_title.getbbox(main_title_str)
            tw = tb[2] - tb[0]
            draw.text((cx - tw//2, title_y), main_title_str, fill=(255, 255, 255), font=font_leader_title)
            
        # C. Intro Subtitle (默认片头文字，支持自定义修改)
        sub_y = wy0 - 72
        if sub_y > -40:
            intro_sub_str = (intro_title or 'MEMORIES ON THE ROAD · 沿途风光与光影纪实').strip()
            sb = font_leader_sub.getbbox(intro_sub_str)
            sw = sb[2] - sb[0]
            draw.text((cx - sw//2, sub_y), intro_sub_str, fill=(148, 163, 184), font=font_leader_sub)
            
        # D. Bottom Divider & Roll Transition Notch
        div_y = wy0 - 24
        if div_y > -20:
            draw.line([(cx - 260, div_y), (cx + 260, div_y)], fill=(51, 65, 85), width=1)
            marker_str = '— START OF ROLL · FRAME 01 ▶ —'
            mb = font_leader_mono.getbbox(marker_str)
            mw = mb[2] - mb[0]
            draw.rectangle([(cx - mw//2 - 8, div_y - 8), (cx + mw//2 + 8, div_y + 8)], fill=(14, 18, 29))
            draw.text((cx - mw//2, div_y - 6), marker_str, fill=(100, 116, 139), font=font_leader_mono)
    
    return canvas
