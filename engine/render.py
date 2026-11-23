"""Render one scene of a Pasta Clara short. Usage: render.py script.json timing.json env.npy scene_idx out.mp4"""
import json, sys, math, subprocess, random
import numpy as np, skia

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/"
TF = {k: skia.Typeface.MakeFromFile(FD + f"Inter-{v}.otf") for k, v in
      {"black": "Black", "xbold": "ExtraBold", "bold": "Bold", "semi": "SemiBold", "med": "Medium"}.items()}
EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")

def col(h, a=1.0):
    h = h.lstrip("#"); r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, int(max(0, min(1, a)) * 255))

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x, s=1.9):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def elastic(x):
    x = clamp(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1

def font(w, size): return skia.Font(TF[w], size)

def text_w(f, s): return f.measureText(s)

def draw_text(c, s, x, y, size, color="#ffffff", w="black", align="center", alpha=1.0, shadow=True, maxw=980):
    f = font(w, size)
    tw = text_w(f, s)
    if tw > maxw:  # shrink to fit
        f = font(w, size * maxw / tw); tw = text_w(f, s)
    x0 = x - tw / 2 if align == "center" else (x - tw if align == "right" else x)
    if shadow:
        p = skia.Paint(Color=skia.Color(0, 0, 0, int(140 * alpha)), AntiAlias=True,
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.08))
        c.drawString(s, x0, y + size * 0.06, f, p)
    c.drawString(s, x0, y, f, skia.Paint(Color=col(color, alpha), AntiAlias=True))
    return tw

def draw_emoji(c, ch, x, y, size, alpha=1.0):
    f = skia.Font(EMOJI, 109)  # bitmap strike size
    sc = size / 109.0
    tw = f.measureText(ch)
    c.save(); c.translate(x, y); c.scale(sc, sc)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(clamp(alpha))
    c.drawString(ch, -tw / 2, 109 * 0.36, f, p)
    c.restore()

def fmt_num(v, dec=0, sep="."):
    if dec == 0:
        s = f"{int(round(v)):,}".replace(",", sep)
    else:
        s = f"{v:,.{dec}f}"; ip, fp = s.split("."); s = ip.replace(",", sep) + "," + fp
    return s

def rrect(c, x, y, w, h, r, paint):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint)

# ---------------------------------------------------------------- background
class Background:
    def __init__(self, accent, seed):
        rnd = random.Random(seed)
        s = skia.Surface(W, H); c = s.getCanvas()
        sh = skia.GradientShader.MakeLinear([(0, 0), (W * 0.3, H)], [col("#0a1030"), col("#16113f"), col("#0c1a3a")], [0, 0.6, 1])
        c.drawPaint(skia.Paint(Shader=sh))
        vg = skia.GradientShader.MakeRadial((W / 2, H * 0.42), H * 0.75, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 150)])
        c.drawPaint(skia.Paint(Shader=vg))
        self.img = s.makeImageSnapshot()
        self.dots = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(18, 70), rnd.uniform(0.04, 0.14),
                      rnd.uniform(-12, 12), rnd.uniform(-22, -6), rnd.choice([accent, "#7b6cff", "#3fa9ff", "#ffffff"]))
                     for _ in range(26)]
        self.accent = accent

    def draw(self, c, t):
        c.drawImage(self.img, 0, 0)
        for x, y, r, a, vx, vy, cc in self.dots:
            px = (x + vx * t) % (W + 200) - 100; py = (y + vy * t) % (H + 200) - 100
            a2 = a * (0.7 + 0.3 * math.sin(t * 0.8 + x))
            sh = skia.GradientShader.MakeRadial((px, py), r, [col(cc, a2), col(cc, 0)])
            c.drawCircle(px, py, r, skia.Paint(Shader=sh, AntiAlias=True))
        # slow light sweep
        sx = ((t * 90) % (W + 1600)) - 800
        sh = skia.GradientShader.MakeLinear([(sx, 0), (sx + 500, 300)],
                                            [skia.Color(255, 255, 255, 0), skia.Color(255, 255, 255, 14), skia.Color(255, 255, 255, 0)], [0, 0.5, 1])
        c.drawPaint(skia.Paint(Shader=sh))

# ---------------------------------------------------------------- mascot "Duro"
def draw_duro(c, t, amp, hop=0.0):
    cx, cy, r = 165, 1500 - hop * 40, 100
    c.save()
    c.translate(cx, cy); c.rotate(math.sin(t * 1.7) * 4)
    # shadow
    c.drawOval(skia.Rect.MakeXYWH(-80, r + 18 + hop * 40, 160, 24), skia.Paint(Color=skia.Color(0, 0, 0, 90), AntiAlias=True,
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
    # coin body
    sh = skia.GradientShader.MakeLinear([(-r, -r), (r, r)], [col("#ffe38a"), col("#f2b632"), col("#c9860f")], [0, 0.5, 1])
    c.drawCircle(0, 0, r, skia.Paint(Shader=sh, AntiAlias=True))
    c.drawCircle(0, 0, r - 12, skia.Paint(Color=col("#a86a06", 0.55), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5))
    for i in range(36):  # milled edge
        a = i * math.pi * 2 / 36
        c.drawLine(math.cos(a) * (r - 5), math.sin(a) * (r - 5), math.cos(a) * r, math.sin(a) * r,
                   skia.Paint(Color=col("#a86a06", 0.6), StrokeWidth=3, AntiAlias=True))
    # headset
    hp = skia.Paint(Color=col("#2b2f45"), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=12, StrokeCap=skia.Paint.kRound_Cap)
    c.drawArc(skia.Rect.MakeXYWH(-r - 6, -r - 14, 2 * r + 12, 2 * r + 12), 200, 140, False, hp)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-r - 18, -22, 26, 50), 10, 10), skia.Paint(Color=col("#7b6cff"), AntiAlias=True))
    mp = skia.Paint(Color=col("#2b2f45"), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, StrokeCap=skia.Paint.kRound_Cap)
    path = skia.Path(); path.moveTo(-r - 4, 20); path.quadTo(-r + 10, 75, -30, 70); c.drawPath(path, mp)
    c.drawCircle(-28, 70, 9, skia.Paint(Color=col("#2b2f45"), AntiAlias=True))
    # eyes (blink)
    bl = 1.0
    ph = (t % 3.7)
    if ph < 0.14: bl = abs(ph - 0.07) / 0.07
    for ex in (-32, 32):
        c.drawOval(skia.Rect.MakeXYWH(ex - 13, -28 - 17 * bl, 26, 34 * bl + 1), skia.Paint(Color=col("#ffffff"), AntiAlias=True))
        c.drawCircle(ex + 3, -26, 8 * max(bl, 0.2), skia.Paint(Color=col("#1d1b2e"), AntiAlias=True))
    # grumpy brows
    bp = skia.Paint(Color=col("#6b3f00"), AntiAlias=True, StrokeWidth=8, StrokeCap=skia.Paint.kRound_Cap)
    lift = amp * 8
    c.drawLine(-50, -58 - lift, -16, -50 - lift, bp); c.drawLine(50, -58 - lift, 16, -50 - lift, bp)
    # moustache
    mus = skia.Paint(Color=col("#6b3f00"), AntiAlias=True)
    c.drawOval(skia.Rect.MakeXYWH(-42, 6, 40, 16), mus); c.drawOval(skia.Rect.MakeXYWH(2, 6, 40, 16), mus)
    # mouth
    mh = 6 + amp * 34
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-22, 24, 44, mh), 14, 14), skia.Paint(Color=col("#5a1a1a"), AntiAlias=True))
    if mh > 16:
        c.drawOval(skia.Rect.MakeXYWH(-12, 24 + mh - 12, 24, 9), skia.Paint(Color=col("#ff7b7b"), AntiAlias=True))
    c.restore()
    # sound waves
    if amp > 0.08:
        for i in range(3):
            a = clamp(amp * 1.6 - i * 0.25) * (0.5 + 0.5 * math.sin(t * 14 - i))
            c.drawArc(skia.Rect.MakeXYWH(cx + 40 - (60 + i * 26), cy - (60 + i * 26), 2 * (60 + i * 26), 2 * (60 + i * 26)), -35, 70, False,
                      skia.Paint(Color=col("#ffffff", a * 0.7), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, StrokeCap=skia.Paint.kRound_Cap))

# ---------------------------------------------------------------- elements
def appear(e, st):
    at = e.get("at", 0)
    return st[at] + e.get("delay", 0.0) if isinstance(at, int) else at

def draw_element(c, e, t, st, acc, scene_end):
    t0 = appear(e, st)
    if t < t0: return
    lt = t - t0
    alpha = clamp(lt / 0.18)
    if "out" in e:
        to = st[e["out"]] if e["out"] < len(st) else scene_end
        if t > to: alpha *= 1 - clamp((t - to) / 0.25)
        if alpha <= 0: return
    typ = e["type"]
    x = e.get("x", 540); y = e.get("y", 600)
    color = e.get("color", "#ffffff").replace("ACC", acc)
    if typ == "text":
        s = elastic(lt / 0.8) if e.get("pop", True) else 1
        c.save(); c.translate(x, y); c.scale(s, s)
        draw_text(c, e["text"], 0, 0, e.get("size", 90), color, e.get("w", "black"), e.get("align", "center"), alpha, maxw=e.get("maxw", 980))
        c.restore()
    elif typ == "emoji":
        s = elastic(lt / 0.9)
        hop = 0
        for hi in e.get("hop", []):
            if hi < len(st):
                d = t - st[hi]
                if 0 <= d < 0.5: hop = math.sin(d / 0.5 * math.pi)
        bob = math.sin(t * 2.2 + x) * 8
        c.save(); c.translate(x, y + bob - hop * 60); c.rotate(math.sin(t * 1.3 + y) * 5 + hop * 8); c.scale(s, s)
        draw_emoji(c, e["ch"], 0, 0, e.get("size", 240), alpha)
        c.restore()
    elif typ == "count":
        d = e.get("dur", 1.1)
        p = ease_out(lt / d)
        v = e.get("from", 0) + (e["to"] - e.get("from", 0)) * p
        s = back(lt / 0.5) * (1 + 0.05 * math.exp(-max(0, lt - d) * 8) * (lt > d))
        txt = e.get("prefix", "") + fmt_num(v, e.get("dec", 0)) + e.get("suffix", "")
        c.save(); c.translate(x, y); c.scale(s, s)
        draw_text(c, txt, 0, 0, e.get("size", 150), color, "black", "center", alpha)
        c.restore()
        if lt > d and lt < d + 0.6:  # ring burst at finish
            q = (lt - d) / 0.6
            c.drawCircle(x, y - e.get("size", 150) * 0.35, 80 + q * 320, skia.Paint(Color=col(color, (1 - q) * 0.6), AntiAlias=True,
                         Style=skia.Paint.kStroke_Style, StrokeWidth=10 * (1 - q) + 1))
    elif typ == "stamp":
        q = clamp(lt / 0.35)
        s = 2.2 - 1.2 * ease_out(q)
        shake = math.sin(lt * 60) * 10 * math.exp(-lt * 7) if lt > 0.35 else 0
        c.save(); c.translate(x + shake, y); c.rotate(e.get("rot", -10)); c.scale(s, s)
        f = font("black", e.get("size", 64)); tw = text_w(f, e["text"]); hh = e.get("size", 64)
        p = skia.Paint(Color=col(color, alpha * q), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8)
        rrect(c, -tw / 2 - 30, -hh * 0.95, tw + 60, hh * 1.3, 18, p)
        c.drawString(e["text"], -tw / 2, 0, f, skia.Paint(Color=col(color, alpha * q), AntiAlias=True))
        c.restore()
    elif typ == "bars":
        for i, it in enumerate(e["items"]):
            bt = st[it["at"]] + it.get("delay", 0) if "at" in it else t0 + i * 0.4
            if t < bt: continue
            bl = t - bt; a = clamp(bl / 0.2) * alpha
            by = y + i * e.get("gap", 175)
            draw_text(c, it["label"], 90, by, 46, "#ffffff", "xbold", "left", a, maxw=560)
            draw_text(c, it.get("text", ""), 990, by, 46, it.get("color", acc).replace("ACC", acc), "black", "right", a, maxw=440)
            rrect(c, 90, by + 22, 900, 52, 26, skia.Paint(Color=col("#ffffff", 0.12 * a), AntiAlias=True))
            wv = 900 * it["frac"] * ease_out(bl / 0.9)
            if wv > 2:
                cc = it.get("color", acc).replace("ACC", acc)
                sh = skia.GradientShader.MakeLinear([(90, 0), (990, 0)], [col(cc, a), col(cc, a * 0.75)])
                rrect(c, 90, by + 22, max(wv, 52), 52, 26, skia.Paint(Shader=sh, AntiAlias=True))
    elif typ == "stack":
        bx, bw, bh = 90, 900, 110
        rrect(c, bx, y, bw, bh, 30, skia.Paint(Color=col("#ffffff", 0.10 * alpha), AntiAlias=True))
        cx0 = bx
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, y, bw, bh), 30, 30), True)
        for i, sg in enumerate(e["segments"]):
            stt = (st[sg["at"]] if "at" in sg else t0) + sg.get("delay", i * 0.5)
            full = bw * sg["frac"]
            if t >= stt:
                g = ease_out((t - stt) / 0.8)
                cc = sg["color"].replace("ACC", acc)
                c.drawRect(skia.Rect.MakeXYWH(cx0, y, full * g, bh), skia.Paint(Color=col(cc, alpha), AntiAlias=True))
                if g > 0.6 and sg.get("inside"):
                    draw_text(c, sg["inside"], cx0 + full / 2, y + bh / 2 + 18, 46, "#0b1230", "black", "center", alpha * clamp((g - 0.6) / 0.3), shadow=False, maxw=full - 20)
            cx0 += full
        c.restore()
        # labels below
        cx0 = bx; row = 0
        for i, sg in enumerate(e["segments"]):
            stt = (st[sg["at"]] if "at" in sg else t0) + sg.get("delay", i * 0.5)
            full = bw * sg["frac"]
            if t >= stt + 0.3 and sg.get("label"):
                a = clamp((t - stt - 0.3) / 0.3) * alpha
                ly = y + bh + 70 + row * 70
                cc = sg["color"].replace("ACC", acc)
                c.drawCircle(bx + 20, ly - 16, 16, skia.Paint(Color=col(cc, a), AntiAlias=True))
                draw_text(c, sg["label"], bx + 52, ly, 48, "#ffffff", "xbold", "left", a, maxw=850)
                row += 1
            cx0 += full
    elif typ == "coins":
        n = e.get("n", 100); hl = e.get("hl", 4.5); cols = 10; sz = 74
        gx = 540 - cols * sz / 2 + sz / 2
        for i in range(n):
            r_, c_ = divmod(i, cols)
            ct = t0 + i * 0.012
            if t < ct: continue
            s = back((t - ct) / 0.35)
            px, py = gx + c_ * sz, y + r_ * sz
            lit = clamp(hl - i)
            hl_t = st[e["hl_at"]] if "hl_at" in e else t0 + 1.4
            on = lit > 0 and t > hl_t + i * 0.15
            cc = "#ffd34d" if on else "#3a4570"
            rr = sz * 0.42 * s
            c.drawCircle(px, py, rr, skia.Paint(Color=col(cc, alpha), AntiAlias=True))
            if on and lit < 1:  # half coin
                c.drawRect(skia.Rect.MakeXYWH(px - rr + 2 * rr * lit, py - rr, 2 * rr * (1 - lit), 2 * rr), skia.Paint(Color=col("#3a4570", alpha)))
            if on:
                d = t - (hl_t + i * 0.15)
                if d < 0.5:
                    c.drawCircle(px, py, rr + d * 90, skia.Paint(Color=col("#ffd34d", (1 - d / 0.5) * alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=5, AntiAlias=True))
    elif typ == "clock":
        r = e.get("r", 290); cx, cy = x, y
        g = ease_out(lt / 0.8)
        c.drawCircle(cx, cy, r * g, skia.Paint(Color=col("#ffffff", 0.08 * alpha), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=70))
        for sg in e["segments"]:
            stt = st[sg["at"]] + sg.get("delay", 0)
            if t < stt: continue
            q = ease_out((t - stt) / 0.9)
            a0 = -90 + sg["from"] * 15; sw = (sg["to"] - sg["from"]) * 15 * q
            c.drawArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), a0, sw, False,
                      skia.Paint(Color=col(sg["color"], alpha), AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=70))
        for h in range(0, 24, 3):
            a = math.radians(-90 + h * 15)
            draw_text(c, f"{h}", cx + math.cos(a) * (r - 90), cy + math.sin(a) * (r - 90) + 14, 38, "#c9d2ff", "bold", "center", alpha * g, shadow=False)
        # hand sweeping through the day
        ha = math.radians(-90 + ((t * 40) % 360))
        c.drawLine(cx, cy, cx + math.cos(ha) * (r - 140), cy + math.sin(ha) * (r - 140),
                   skia.Paint(Color=col("#ffffff", alpha * g), StrokeWidth=10, StrokeCap=skia.Paint.kRound_Cap, AntiAlias=True))
        c.drawCircle(cx, cy, 16, skia.Paint(Color=col(acc, alpha * g), AntiAlias=True))
    elif typ == "confetti":
        rnd = random.Random(7)
        for i in range(90):
            vx = rnd.uniform(-520, 520); vy = rnd.uniform(-1300, -500); cc = rnd.choice([acc, "#ffd34d", "#ff5fa2", "#4cc9f0", "#ffffff"])
            px = 540 + vx * lt; py = 900 + vy * lt + 900 * lt * lt
            if py > 2000: continue
            c.save(); c.translate(px, py); c.rotate(lt * rnd.uniform(200, 700))
            c.drawRect(skia.Rect.MakeXYWH(-9, -5, 18, 10), skia.Paint(Color=col(cc, alpha * clamp(2.5 - lt)), AntiAlias=True))
            c.restore()
    elif typ == "footer":
        draw_text(c, e["text"], 540, e.get("y", 1160), 30, "#9aa6d6", "semi", "center", alpha * 0.9, shadow=False, maxw=960)

# ---------------------------------------------------------------- subtitles
def draw_subs(c, sents, t):
    for s in sents:
        if not (s["start"] - 0.05 <= t < s["end"] + 0.2): continue
        ch = s["chunks"]; L = [max(len(x), 4) for x in ch]; tot = sum(L)
        dur = s["end"] - s["start"]; acc_t = s["start"]
        for i, x in enumerate(ch):
            d = dur * L[i] / tot
            if acc_t <= t < acc_t + d or (i == len(ch) - 1 and t >= acc_t):
                lt = t - acc_t
                sc = back(lt / 0.25, 2.4)
                f = font("black", 60); tw = min(text_w(f, x), 900)
                c.save(); c.translate(540, 1290); c.scale(sc, sc)
                rrect(c, -tw / 2 - 34, -62, tw + 68, 104, 30, skia.Paint(Color=skia.Color(0, 0, 0, 200), AntiAlias=True))
                draw_text(c, x, 0, 12, 60, "#ffffff", "black", "center", 1, shadow=False, maxw=900)
                c.restore()
                return
            acc_t += d

# ---------------------------------------------------------------- main
def main(script_p, timing_p, env_p, idx, out):
    S = json.load(open(script_p)); T = json.load(open(timing_p)); env = np.load(env_p)
    idx = int(idx); sc = S["scenes"][idx]; tm = T["scenes"][idx]
    acc = S["accent"]; bg = Background(acc, idx)
    st = [s["start"] for s in tm["sentences"]]
    nfr = tm["frames"]; dur = nfr / FPS
    last = idx == len(S["scenes"]) - 1
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    buf = np.zeros((H, W, 4), np.uint8)
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    for fi in range(nfr):
        t = fi / FPS; gt = tm["start"] + t
        c = surf.getCanvas()
        bg.draw(c, gt)
        # camera
        punch = 0
        for s0 in st:
            d = t - s0
            if 0 <= d < 0.6: punch = max(punch, 0.035 * math.sin(clamp(d / 0.6) * math.pi) * (1 - d / 0.6 * 0.5))
        z = 1.0 + 0.025 * ease_io(t / max(dur, 1)) + punch
        c.save()
        c.translate(540 + math.sin(gt * 0.35) * 10, 760 + math.cos(gt * 0.28) * 8); c.scale(z, z); c.translate(-540, -760)
        for e in sc["elements"]:
            draw_element(c, e, t, st, acc, dur)
        c.restore()
        # header pill
        f = font("xbold", 34); lab = "PASTA CLARA  ·  " + S["tag"]; tw = text_w(f, lab)
        rrect(c, 540 - tw / 2 - 28, 168, tw + 56, 62, 31, skia.Paint(Color=col(acc, 0.18), AntiAlias=True))
        draw_text(c, lab, 540, 211, 34, acc, "xbold", "center", 1, shadow=False)
        draw_subs(c, tm["sentences"], t)
        ai = min(int(gt * FPS), len(env) - 1)
        draw_duro(c, gt, float(env[ai]))
        # wipes
        wp = None
        if idx > 0 and t < 0.32: wp = 1 + ease_io(t / 0.32)          # reveal: 1->2
        if not last and t > dur - 0.32: wp = ease_io((t - (dur - 0.32)) / 0.32)  # cover: 0->1
        if wp is not None:
            p = skia.Path()
            if wp <= 1:
                xr = -500 + wp * 2100; p.moveTo(-500, 0); p.lineTo(xr, 0); p.lineTo(xr - 500, H); p.lineTo(-1000, H)
            else:
                xl = -500 + (wp - 1) * 2100; p.moveTo(xl, 0); p.lineTo(1700, 0); p.lineTo(1700, H); p.lineTo(xl - 500, H)
            p.close()
            c.drawPath(p, skia.Paint(Color=col(acc), AntiAlias=True))
        surf.readPixels(info, buf, W * 4)
        ff.stdin.write(buf.tobytes())
    ff.stdin.close(); ff.wait()

if __name__ == "__main__":
    main(*sys.argv[1:6])
