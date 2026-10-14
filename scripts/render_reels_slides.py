import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('assets/slides', exist_ok=True)

FONT_BOLD = r'C:\Windows\Fonts\msjhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msjh.ttc'

def get_font(size, bold=True):
    path = FONT_BOLD if bold else FONT_REG
    return ImageFont.truetype(path, size)

W, H = 1080, 1920

def create_gradient_bg(c_top, c_bot):
    bg = Image.new('RGB', (W, H), c_top)
    draw = ImageDraw.Draw(bg)
    for y in range(H):
        r = int(c_top[0] + (c_bot[0] - c_top[0]) * (y / H))
        g = int(c_top[1] + (c_bot[1] - c_top[1]) * (y / H))
        b = int(c_top[2] + (c_bot[2] - c_top[2]) * (y / H))
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return bg

def draw_text_with_shadow(draw, pos, text, font, fill=(255, 255, 255), outline_color=(0, 0, 0), stroke_width=3, align='center'):
    x, y = pos
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    if align == 'center':
        draw_x = x - tw // 2
    elif align == 'right':
        draw_x = x - tw
    else:
        draw_x = x
        
    for ox in range(-stroke_width, stroke_width + 1):
        for oy in range(-stroke_width, stroke_width + 1):
            if ox != 0 or oy != 0:
                draw.text((draw_x + ox, y + oy), text, font=font, fill=outline_color)
    draw.text((draw_x, y), text, font=font, fill=fill)
    return tw, th

def draw_pill_badge(img, center_x, top_y, text, font, bg_color=(255, 107, 0), text_color=(255, 255, 255), pad_x=28, pad_y=14, radius=22, border_color=None):
    draw = ImageDraw.Draw(img)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    w = tw + pad_x * 2
    h = th + pad_y * 2
    left = center_x - w // 2
    top = top_y
    right = left + w
    bottom = top + h
    
    draw.rounded_rectangle([left+3, top+4, right+3, bottom+4], radius=radius, fill=(0, 0, 0, 140))
    draw.rounded_rectangle([left, top, right, bottom], radius=radius, fill=bg_color)
    if border_color:
        draw.rounded_rectangle([left, top, right, bottom], radius=radius, outline=border_color, width=2)
    draw.text((center_x - tw // 2, top + pad_y - 2), text, font=font, fill=text_color)
    return bottom

# Load base product images
jar_img = Image.open('assets/jar_cropped.png').convert('RGBA') # 540x600
table_jar = Image.open('assets/slice_info.png').convert('RGB')
full_poster = Image.open('assets/paoguo_product.png').convert('RGB')
elders_photo = Image.open('assets/paoguo_extracted/docx/word/media/image36.jpeg').convert('RGB')

# =========================================================================
# SLIDE 1: Hook (00-05s) - 你敢信？這酸爽的一口，居然是「鹹」的！
# =========================================================================
def render_slide1():
    bg = create_gradient_bg((16, 32, 22), (38, 24, 10))
    ambient = jar_img.resize((1200, 1330)).filter(ImageFilter.GaussianBlur(35))
    bg.paste(ambient, (-60, 250), ambient)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 110))
    bg.paste(overlay, (0, 0), overlay)
    
    macro_jar = jar_img.resize((820, 910), Image.Resampling.LANCZOS)
    macro_crop = macro_jar.crop((70, 110, 750, 860)) # 680 x 750
    mask = Image.new('L', macro_crop.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, macro_crop.size[0], macro_crop.size[1]], radius=45, fill=255)
    
    food_x = (W - macro_crop.size[0]) // 2
    food_y = 500
    shadow = Image.new('RGBA', (macro_crop.size[0]+20, macro_crop.size[1]+20), (0, 0, 0, 160))
    bg.paste(shadow, (food_x-10, food_y-6))
    bg.paste(macro_crop, (food_x, food_y), mask)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 170, "【 顛覆想像的味覺震撼 】", get_font(36, bold=True), bg_color=(234, 88, 12))
    draw_text_with_shadow(draw, (W//2, 255), "你敢信？！這一口...", get_font(64, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 355), "居然是『鹹』的！", get_font(88, bold=True), fill=(255, 230, 0))
    
    draw_text_with_shadow(draw, (W//2, 1340), "◆ 黎明村手作「芒果青」新登場 ◆", get_font(50, bold=True), fill=(255, 240, 180))
    draw_text_with_shadow(draw, (W//2, 1425), "不是普通的甜芒果！酸爽鹹香超脆口", get_font(38, bold=False), fill=(225, 225, 225))
    
    draw_pill_badge(bg, W//2 - 210, 1540, "★ 咔嚓極致爽脆", get_font(36, bold=True), bg_color=(34, 197, 94))
    draw_pill_badge(bg, W//2 + 210, 1540, "★ 鹹香越吃越上癮", get_font(36, bold=True), bg_color=(234, 88, 12))
    draw_text_with_shadow(draw, (W//2, 1750), "屏東縣內埔鄉黎明社區 ✕ 在地青果手作", get_font(28, bold=False), fill=(180, 180, 180))
    bg.save('assets/slides/slide1.png')
    print("slide1.png done")

# =========================================================================
# SLIDE 2: Product Intro (05-13s) - 台灣在地鮮果！不是熟芒果！
# =========================================================================
def render_slide2():
    bg = create_gradient_bg((18, 36, 24), (12, 22, 16))
    
    # Scale table jar into a well-proportioned card
    table_resized = table_jar.resize((920, 1040), Image.Resampling.LANCZOS)
    card_mask = Image.new('L', table_resized.size, 0)
    ImageDraw.Draw(card_mask).rounded_rectangle([0, 0, table_resized.size[0], table_resized.size[1]], radius=45, fill=255)
    
    cx = (W - table_resized.size[0]) // 2
    cy = 440
    shadow = Image.new('RGBA', (table_resized.size[0]+24, table_resized.size[1]+24), (0, 0, 0, 150))
    bg.paste(shadow, (cx-12, cy-8))
    bg.paste(table_resized, (cx, cy), card_mask)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 160, "【 台灣在地鮮果 正式上市 】", get_font(36, bold=True), bg_color=(16, 185, 129))
    draw_text_with_shadow(draw, (W//2, 245), "用的是真正的「青芒果」！", get_font(64, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 345), "不是熟芒果喔！", get_font(80, bold=True), fill=(255, 220, 0))
    
    # Bottom information section
    draw_pill_badge(bg, W//2, 1490, "★ 產地鮮採直送 ＆ 完整保留天然果酸 ★", get_font(38, bold=True), bg_color=(0, 0, 0, 210), text_color=(255, 235, 120), border_color=(255, 200, 50))
    
    draw_text_with_shadow(draw, (W//2, 1580), "嚴選台灣在地青果・果肉厚實緊緻", get_font(42, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 1650), "每一片都吃得到最道地的台灣鮮活果酸", get_font(34, bold=False), fill=(220, 220, 220))
    
    draw_pill_badge(bg, W//2 - 220, 1720, "● 產地在欉鮮採", get_font(32, bold=True), bg_color=(5, 150, 105))
    draw_pill_badge(bg, W//2 + 220, 1720, "● 堅持古法製作", get_font(32, bold=True), bg_color=(217, 119, 6))
    
    draw_text_with_shadow(draw, (W//2, 1820), "黎明村手作醋溜泡果・台灣在地好滋味", get_font(26, bold=False), fill=(170, 170, 170))
    bg.save('assets/slides/slide2.png')
    print("slide2.png done")

# =========================================================================
# SLIDE 3: Craft & Pickling (13-20s) - 天然果酸搭配在地醋醃製
# =========================================================================
def render_slide3():
    bg = create_gradient_bg((35, 28, 14), (20, 16, 8))
    
    macro_slice = jar_img.crop((40, 150, 500, 580))
    macro_scaled = macro_slice.resize((960, 880), Image.Resampling.LANCZOS)
    
    mask = Image.new('L', macro_scaled.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, macro_scaled.size[0], macro_scaled.size[1]], radius=45, fill=255)
    
    cx = (W - macro_scaled.size[0]) // 2
    cy = 470
    shadow = Image.new('RGBA', (macro_scaled.size[0]+20, macro_scaled.size[1]+20), (0, 0, 0, 160))
    bg.paste(shadow, (cx-10, cy-6))
    bg.paste(macro_scaled, (cx, cy), mask)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 160, "【 屏東內埔・在地釀造工藝 】", get_font(36, bold=True), bg_color=(217, 119, 6))
    draw_text_with_shadow(draw, (W//2, 245), "天然果酸 ✕ 在地醋醃製", get_font(66, bold=True), fill=(255, 235, 120))
    draw_text_with_shadow(draw, (W//2, 345), "酸香清爽・完全不會膩！", get_font(74, bold=True), fill=(255, 255, 255))
    
    draw_text_with_shadow(draw, (W//2, 1430), "保留青芒果特有脆口與多層次琥珀醬汁", get_font(42, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 1510), "微鹹、微辣、透亮果酸，越吃越開胃！", get_font(36, bold=False), fill=(225, 225, 225))
    
    draw_pill_badge(bg, W//2 - 230, 1610, "★ 琥珀醋溜秘醬", get_font(34, bold=True), bg_color=(180, 83, 9))
    draw_pill_badge(bg, W//2 + 230, 1610, "★ 保留天然脆口", get_font(34, bold=True), bg_color=(16, 185, 129))
    
    draw_text_with_shadow(draw, (W//2, 1760), "手作泡果・結合內埔純釀造醋文化", get_font(28, bold=False), fill=(180, 180, 180))
    bg.save('assets/slides/slide3.png')
    print("slide3.png done")

# =========================================================================
# SLIDE 4: Emotional Core (20-30s) - 黎明村銀髮長者親手削皮切片
# =========================================================================
def render_slide4():
    bg = create_gradient_bg((32, 22, 18), (18, 14, 12))
    
    elders_scaled = elders_photo.resize((960, 680), Image.Resampling.LANCZOS)
    mask1 = Image.new('L', elders_scaled.size, 0)
    ImageDraw.Draw(mask1).rounded_rectangle([0, 0, elders_scaled.size[0], elders_scaled.size[1]], radius=40, fill=255)
    
    cx = (W - elders_scaled.size[0]) // 2
    cy = 440
    shadow = Image.new('RGBA', (elders_scaled.size[0]+20, elders_scaled.size[1]+20), (0, 0, 0, 150))
    bg.paste(shadow, (cx-10, cy-6))
    bg.paste(elders_scaled, (cx, cy), mask1)
    
    mini_jar = jar_img.resize((260, 290), Image.Resampling.LANCZOS)
    bg.paste(mini_jar, (W - 360, 930), mini_jar)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 150, "【 來自屏東黎明村的滋味 】", get_font(36, bold=True), bg_color=(220, 38, 38))
    draw_text_with_shadow(draw, (W//2, 235), "社區銀髮長者 親手削皮切片", get_font(60, bold=True), fill=(255, 230, 80))
    draw_text_with_shadow(draw, (W//2, 335), "每一口・都有手作的溫度！", get_font(72, bold=True), fill=(255, 255, 255))
    
    draw_text_with_shadow(draw, (W//2, 1200), "將疏果變身為永續美味", get_font(52, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 1285), "「社區銀髮加工站」高齡賦能與在地溫暖", get_font(38, bold=False), fill=(240, 240, 240))
    draw_text_with_shadow(draw, (W//2, 1355), "落實 SDGs 12 責任生產・青銀共創共好", get_font(34, bold=False), fill=(200, 230, 200))
    
    draw_pill_badge(bg, W//2 - 240, 1470, "★ 銀髮長者傳承經驗", get_font(34, bold=True), bg_color=(194, 65, 12))
    draw_pill_badge(bg, W//2 + 240, 1470, "★ 循環農業落地生根", get_font(34, bold=True), bg_color=(22, 163, 74))
    
    draw_pill_badge(bg, W//2, 1600, "【 屏東縣內埔鄉黎明社區發展協會 】", get_font(36, bold=True), bg_color=(0, 0, 0, 180), text_color=(255, 220, 100), border_color=(255, 200, 50))
    draw_text_with_shadow(draw, (W//2, 1780), "讓農村常民智慧・化為餐桌上的永續好滋味", get_font(28, bold=False), fill=(180, 180, 180))
    bg.save('assets/slides/slide4.png')
    print("slide4.png done")

# =========================================================================
# SLIDE 5: Taste & Scenario (25-35s) - 酸甜開胃，越吃越涮嘴！
# =========================================================================
def render_slide5():
    bg = create_gradient_bg((18, 30, 20), (32, 20, 12))
    
    macro_jar = table_jar.resize((920, 960), Image.Resampling.LANCZOS)
    mask = Image.new('L', macro_jar.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, macro_jar.size[0], macro_jar.size[1]], radius=45, fill=255)
    
    cx = (W - macro_jar.size[0]) // 2
    cy = 440
    shadow = Image.new('RGBA', (macro_jar.size[0]+24, macro_jar.size[1]+24), (0, 0, 0, 160))
    bg.paste(shadow, (cx-12, cy-8))
    bg.paste(macro_jar, (cx, cy), mask)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 160, "【 極致開胃・解膩神器 】", get_font(36, bold=True), bg_color=(234, 88, 12))
    draw_text_with_shadow(draw, (W//2, 245), "酸甜開胃・越吃越涮嘴！", get_font(68, bold=True), fill=(255, 230, 0))
    draw_text_with_shadow(draw, (W//2, 345), "佐餐聖品 ✕ 追劇零嘴", get_font(72, bold=True), fill=(255, 255, 255))
    
    draw_pill_badge(bg, W//2, 1460, "★ 隨開即享・餐桌不可或缺的解膩良伴 ★", get_font(38, bold=True), bg_color=(0, 0, 0, 200), text_color=(255, 230, 100), border_color=(255, 180, 0))
    
    draw_pill_badge(bg, W//2 - 320, 1560, "● 配飯超開胃", get_font(34, bold=True), bg_color=(16, 185, 129))
    draw_pill_badge(bg, W//2, 1560, "● 下酒解油膩", get_font(34, bold=True), bg_color=(217, 119, 6))
    draw_pill_badge(bg, W//2 + 320, 1560, "● 追劇停不下", get_font(34, bold=True), bg_color=(147, 51, 234))
    
    draw_text_with_shadow(draw, (W//2, 1680), "鹹、酸、甜、辣多層次口感・全家人都愛！", get_font(40, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 1780), "屏東黎明村手作醋溜泡果・冰箱必備", get_font(28, bold=False), fill=(170, 170, 170))
    bg.save('assets/slides/slide5.png')
    print("slide5.png done")

# =========================================================================
# SLIDE 6: Pricing & Trust (35-42s) - 400G / 250元，無防腐劑
# =========================================================================
def render_slide6():
    bg = create_gradient_bg((18, 28, 20), (32, 16, 10))
    
    jar_large = jar_img.resize((580, 645), Image.Resampling.LANCZOS)
    bg.paste(jar_large, ((W - 580)//2, 470), jar_large)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 150, "【 不加防腐劑・安心食用 】", get_font(36, bold=True), bg_color=(16, 185, 129))
    draw_text_with_shadow(draw, (W//2, 235), "純天然食材・健康無負擔", get_font(60, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 335), "嚴選屏東在地好物", get_font(74, bold=True), fill=(255, 230, 0))
    
    card_w, card_h = 960, 240
    card_x = (W - card_w) // 2
    card_y = 1150
    draw.rounded_rectangle([card_x+4, card_y+4, card_x+card_w+4, card_y+card_h+4], radius=35, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+card_h], radius=35, fill=(185, 28, 28), outline=(255, 220, 80), width=3)
    
    draw_text_with_shadow(draw, (W//2, card_y + 35), "超大份量！每瓶 400 公克", get_font(42, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, card_y + 115), "特惠價只要 NT$ 250 元", get_font(76, bold=True), fill=(255, 235, 60))
    
    draw_text_with_shadow(draw, (W//2, 1450), "★ 100% 嚴選台灣在地青芒果", get_font(38, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 1520), "★ 絕無添加防腐劑與人工香料", get_font(38, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 1590), "★ 社區銀髮長輩純手工愛心慢醃", get_font(38, bold=True), fill=(255, 255, 255))
    
    draw_pill_badge(bg, W//2, 1680, "【 產地直發・純手作限量供應 】", get_font(34, bold=True), bg_color=(234, 88, 12))
    draw_text_with_shadow(draw, (W//2, 1790), "屏東縣內埔鄉黎明社區發展協會", get_font(28, bold=False), fill=(180, 180, 180))
    bg.save('assets/slides/slide6.png')
    print("slide6.png done")

# =========================================================================
# SLIDE 7: CTA (42-45s) - 喜歡這口台灣好味道嗎？點擊連結帶回家！
# =========================================================================
def render_slide7():
    bg = create_gradient_bg((25, 20, 35), (45, 18, 14))
    
    jar_med = jar_img.resize((500, 555), Image.Resampling.LANCZOS)
    bg.paste(jar_med, ((W - 500)//2, 470), jar_med)
    
    draw = ImageDraw.Draw(bg)
    draw_pill_badge(bg, W//2, 160, "【 支持台灣在地農村好味道 】", get_font(36, bold=True), bg_color=(234, 88, 12))
    draw_text_with_shadow(draw, (W//2, 250), "喜歡這口台灣好味道嗎？", get_font(68, bold=True), fill=(255, 255, 255))
    draw_text_with_shadow(draw, (W//2, 350), "快點擊連結帶回家！", get_font(84, bold=True), fill=(255, 230, 0))
    
    btn_w, btn_h = 920, 180
    btn_x = (W - btn_w) // 2
    btn_y = 1100
    draw.rounded_rectangle([btn_x+4, btn_y+6, btn_x+btn_w+4, btn_y+btn_h+6], radius=40, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([btn_x, btn_y, btn_x+btn_w, btn_y+btn_h], radius=40, fill=(22, 163, 74), outline=(255, 255, 255), width=3)
    draw_text_with_shadow(draw, (W//2, btn_y + 45), "▼ 點擊連結 立即搶購 ▼", get_font(72, bold=True), fill=(255, 255, 255))
    
    draw_pill_badge(bg, W//2, 1360, "★ 連結在上方 / 留言區！別錯過這口台灣味 ★", get_font(36, bold=True), bg_color=(0, 0, 0, 200), text_color=(255, 220, 100), border_color=(255, 180, 0))
    
    draw_text_with_shadow(draw, (W//2, 1500), "每瓶 400g ／ 250元 限量熱銷中", get_font(46, bold=True), fill=(255, 235, 100))
    draw_text_with_shadow(draw, (W//2, 1580), "屏東縣內埔鄉黎明社區手作醋溜泡果", get_font(36, bold=False), fill=(220, 220, 220))
    
    draw_pill_badge(bg, W//2 - 220, 1670, "● 產地直送", get_font(32, bold=True), bg_color=(217, 119, 6))
    draw_pill_badge(bg, W//2 + 220, 1670, "● 純天然手作", get_font(32, bold=True), bg_color=(5, 150, 105))
    
    draw_text_with_shadow(draw, (W//2, 1780), "感謝您支持長輩手作與永續農業發展", get_font(28, bold=False), fill=(180, 180, 180))
    bg.save('assets/slides/slide7.png')
    print("slide7.png done")

print("Rendering updated slides...")
render_slide1()
render_slide2()
render_slide3()
render_slide4()
render_slide5()
render_slide6()
render_slide7()
print("Updated all 7 slides successfully!")
