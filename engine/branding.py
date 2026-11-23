import sys, math
sys.path.insert(0, "/home/claude/engine")
import skia
from render import draw_duro, draw_text, col, font, text_w

OUT = "/home/claude/out/branding/"
import os; os.makedirs(OUT, exist_ok=True)

def bg(c, w, h):
    sh = skia.GradientShader.MakeLinear([(0, 0), (w * 0.4, h)], [col("#0a1030"), col("#16113f"), col("#0c1a3a")], [0, 0.6, 1])
    c.drawPaint(skia.Paint(Shader=sh))

def duro_at(c, x, y, s):
    c.save(); c.translate(x, y); c.scale(s, s); c.translate(-165, -1500)
    draw_duro(c, 0.0, 0.07); c.restore()

# avatar 800x800 (shown as circle)
s = skia.Surface(800, 800); c = s.getCanvas(); bg(c, 800, 800)
glow = skia.GradientShader.MakeRadial((400, 400), 380, [col("#36d399", 0.45), col("#36d399", 0)])
c.drawCircle(400, 400, 380, skia.Paint(Shader=glow))
duro_at(c, 400, 410, 2.7)
s.makeImageSnapshot().save(OUT + "avatar_pasta_clara.png", skia.kPNG)

# banner 2560x1440, safe area 1546x423 centred
W, H = 2560, 1440
s = skia.Surface(W, H); c = s.getCanvas(); bg(c, W, H)
for i, (x, y, r, cc) in enumerate([(300, 300, 260, "#36d399"), (2200, 1100, 320, "#7b6cff"), (1900, 250, 200, "#ffc83d"), (500, 1200, 240, "#3fa9ff")]):
    g = skia.GradientShader.MakeRadial((x, y), r, [col(cc, 0.25), col(cc, 0)]); c.drawCircle(x, y, r, skia.Paint(Shader=g))
cx0 = (W - 1546) / 2; cy0 = (H - 423) / 2
duro_at(c, cx0 + 200, H / 2 + 10, 1.75)
draw_text(c, "PASTA CLARA", cx0 + 400, H / 2 + 20, 170, "#ffffff", "black", "left", maxw=1150)
draw_text(c, "La economía de España, explicada en 1 minuto", cx0 + 405, H / 2 + 110, 58, "#36d399", "xbold", "left", shadow=False, maxw=1130)
s.makeImageSnapshot().save(OUT + "banner_pasta_clara.png", skia.kPNG)
print("ok")
