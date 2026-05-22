"""OGP画像生成スクリプト (1200x630)
ResumeAI ロゴの下にサブタイトルを配置する。
"""
from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1200, 630
OUT = r"C:\clude-code\resume-saas\frontend\ogp.png"

img = Image.new("RGB", (W, H), "#0a0f1e")
draw = ImageDraw.Draw(img)

# グリッド
GRID_COLOR = "#0d2d4a"
CELL = 80
for x in range(0, W + CELL, CELL):
    draw.line([(x, 0), (x, H)], fill=GRID_COLOR, width=1)
for y in range(0, H + CELL, CELL):
    draw.line([(0, y), (W, y)], fill=GRID_COLOR, width=1)

# フォント
font_logo = ImageFont.truetype(r"C:\Windows\Fonts\ariblk.ttf", 110)
font_sub  = ImageFont.truetype(r"C:\Windows\Fonts\meiryo.ttc",  38)
font_url  = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf",   22)

# --- ロゴ "ResumeAI" ---
LOGO_TEXT = "ResumeAI"
bbox = draw.textbbox((0, 0), LOGO_TEXT, font=font_logo)
logo_w = bbox[2] - bbox[0]
logo_h = bbox[3] - bbox[1]

# ロゴを上寄り中央（縦全体の40%付近）に配置
logo_x = (W - logo_w) // 2
logo_y = int(H * 0.28)

# グロー効果（外側に薄いシアンを数層描く）
for offset, alpha in [(6, 30), (4, 60), (2, 120)]:
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_img)
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            gd.text((logo_x + dx, logo_y + dy), LOGO_TEXT,
                    font=font_logo, fill=(0, 200, 255, alpha))
    img.paste(Image.alpha_composite(
        img.convert("RGBA"), glow_img).convert("RGB"))
    draw = ImageDraw.Draw(img)

# ロゴ本体（白）
draw.text((logo_x, logo_y), LOGO_TEXT, font=font_logo, fill="#ffffff")

# アクセントライン（ロゴ直下）
line_y = logo_y + logo_h + 12
draw.line([(logo_x, line_y), (logo_x + logo_w, line_y)],
          fill="#00c8ff", width=2)

# --- サブタイトル "履歴書をAIでリメイク  ¥250" ---
SUB_TEXT = "履歴書をAIでリメイク  ¥250"
sbbox = draw.textbbox((0, 0), SUB_TEXT, font=font_sub)
sub_w = sbbox[2] - sbbox[0]

# ロゴ下端から十分な余白（40px）を取って配置
sub_x = (W - sub_w) // 2
sub_y = line_y + 30

draw.text((sub_x, sub_y), SUB_TEXT, font=font_sub, fill="#a0d8ef")

# --- URL ---
URL_TEXT = "www.resumeai.jp"
ubbox = draw.textbbox((0, 0), URL_TEXT, font=font_url)
url_w = ubbox[2] - ubbox[0]
draw.text(((W - url_w) // 2, H - 55), URL_TEXT, font=font_url, fill="#4a9ab5")

img.save(OUT, "PNG", optimize=True)
print(f"保存完了: {OUT}")
