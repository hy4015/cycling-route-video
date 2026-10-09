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
    except Exception:
        font_kodak = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_num = ImageFont.load_default()
    return font_kodak, font_sub, font_num

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

def render_filmstrip_frame(t, y_scroll, windows, window_frames, fps, v_actual, masks, fonts, film_style='portra400'):
    """
    Renders a single 960x1080 filmstrip frame at time t.
    """
    mask_a, mask_b = masks
    font_kodak, font_sub, font_num = fonts
    
    canvas = Image.new('RGB', (W_HALF, H), DARK_BG)
    draw = ImageDraw.Draw(canvas)
    num_windows = len(windows)
    
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
            
    # 2. Draw sprocket film border tracks & holes (luminous light perforations)
    draw.rectangle([(0, 0), (38, H)], fill=(20, 24, 36))
    draw.rectangle([(W_HALF - 38, 0), (W_HALF, H)], fill=(20, 24, 36))

    for x_sprocket in [8, 930]:
        y_sp = -(int(y_scroll) % 80)
        while y_sp < H + 80:
            draw.rounded_rectangle((x_sprocket, y_sp + 10, x_sprocket + 22, y_sp + 50),
                                   radius=5, fill=(248, 250, 252), outline=(148, 163, 184), width=1)
            y_sp += 80
            
    # 3. 35mm Film Stock Gap Typography (strictly in the 44px gap)
    cfg = FILM_CONFIGS.get(film_style, FILM_CONFIGS['portra400'])
    accent_col = cfg['accent']
    brand_text = cfg['brand']
    mid_text = cfg['mid']

    for k in range(-1, num_windows + 1):
        wy = int(round(k * STRIDE - y_scroll + 298))
        gap_y = wy + WIN_H + 13
        if -30 <= gap_y <= H + 30:
            curr_fnum = max(0, k + 1)
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
            
    # 4. Vertical Separation Guide Lines
    draw.line([(38, 0), (38, H)], fill=(45, 55, 72), width=2)
    draw.line([(922, 0), (922, H)], fill=(45, 55, 72), width=2)
    
    return canvas
