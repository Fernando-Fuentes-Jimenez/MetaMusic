"""Full pipeline. Usage: build.py script.json outdir [--sheet]"""
import json, sys, os, subprocess, math
import numpy as np, soundfile as sf
from concurrent.futures import ThreadPoolExecutor

PY = "/home/claude/venv_st/bin/python"; ENG = "/home/claude/engine/"
FPS = 30

def run(cmd): subprocess.run(cmd, check=True)

def envelope(voice, sr, n):
    hop = sr // FPS; e = np.zeros(n)
    for i in range(n):
        seg = voice[i * hop:(i + 1) * hop]
        if len(seg): e[i] = np.sqrt(np.mean(seg ** 2))
    e = e / (np.percentile(e, 95) + 1e-6); e = np.clip(e, 0, 1)
    sm = np.copy(e)
    for i in range(1, n): sm[i] = max(e[i], sm[i - 1] * 0.6)
    return sm

def music(total, sr):
    bpm = 100; beat = 60 / bpm; bar = beat * 4
    chords = [[57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 56, 59]]  # Am G F E
    n = int(total * sr); t = np.arange(n) / sr; out = np.zeros(n)
    f = lambda m: 440 * 2 ** ((m - 69) / 12)
    for bi in range(int(total / bar) + 1):
        ch = chords[bi % 4]; s0 = int(bi * bar * sr); s1 = min(n, int((bi + 1) * bar * sr))
        if s0 >= n: break
        tt = t[s0:s1] - bi * bar
        env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.4)
        for m in ch:
            out[s0:s1] += 0.05 * env * (np.sin(2 * np.pi * f(m) * tt) + 0.3 * np.sin(2 * np.pi * f(m) * 2.003 * tt))
        out[s0:s1] += 0.06 * env * np.sin(2 * np.pi * f(ch[0] - 12) * tt)
        for k in range(8):  # pluck arpeggio
            ps = s0 + int(k * beat / 2 * sr)
            if ps >= s1: break
            m = ch[k % 3] + 12; L = min(s1 - ps, int(0.5 * sr)); tp = np.arange(L) / sr
            out[ps:ps + L] += 0.045 * np.exp(-tp * 7) * np.sin(2 * np.pi * f(m) * tp)
        for k in (0, 2):  # soft kick
            ps = s0 + int(k * beat * sr)
            if ps >= s1: break
            L = min(s1 - ps, int(0.25 * sr)); tp = np.arange(L) / sr
            out[ps:ps + L] += 0.12 * np.exp(-tp * 18) * np.sin(2 * np.pi * (50 + 60 * np.exp(-tp * 30)) * tp)
    fade = np.minimum(1, np.minimum(t / 1.0, (total - t) / 1.5))
    return (out * fade).astype(np.float32)

def sfx(total, sr, starts):
    n = int(total * sr); out = np.zeros(n); rng = np.random.default_rng(3)
    for s in starts:
        L = int(0.45 * sr); p0 = int(max(0, s - 0.3) * sr)
        if p0 + L > n: continue
        noise = rng.standard_normal(L); tp = np.arange(L) / L
        # band sweep via moving-average lowpass of varying width
        y = np.zeros(L); acc = 0
        for i in range(L):
            a = 0.02 + 0.5 * tp[i]
            acc += a * (noise[i] - acc); y[i] = acc
        out[p0:p0 + L] += 0.35 * y * np.sin(np.pi * tp) ** 2
    return out.astype(np.float32)

def main(script_p, out, sheet=False):
    os.makedirs(out, exist_ok=True)
    run([PY, ENG + "tts.py", script_p, out])
    T = json.load(open(out + "/timing.json"))
    voice, sr = sf.read(out + "/voice.wav", dtype="float32")
    total = T["total"]; nfr = sum(s["frames"] for s in T["scenes"])
    np.save(out + "/env.npy", envelope(voice, sr, nfr + 5))
    if sheet: return
    jobs = []
    for i in range(len(T["scenes"])):
        jobs.append([PY, ENG + "render.py", script_p, out + "/timing.json", out + "/env.npy", str(i), f"{out}/scene{i}.mp4"])
    with ThreadPoolExecutor(2) as ex: list(ex.map(run, jobs))
    with open(out + "/list.txt", "w") as fl:
        for i in range(len(jobs)): fl.write(f"file 'scene{i}.mp4'\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", out + "/list.txt", "-c", "copy", out + "/video.mp4"])
    sf.write(out + "/music.wav", music(total, sr), sr)
    sf.write(out + "/sfx.wav", sfx(total, sr, [s["start"] for s in T["scenes"][1:]]), sr)
    fc = ("[0:a]highpass=f=75,equalizer=f=140:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1.2:g=2.5,"
          "acompressor=threshold=-20dB:ratio=3:attack=5:release=90,aecho=0.8:0.8:45:0.07,asplit=2[v][vk];"
          "[1:a]volume=0.55[m];[m][vk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[md];"
          "[2:a]volume=0.8[s];[v][md][s]amix=inputs=3:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", out + "/voice.wav", "-i", out + "/music.wav", "-i", out + "/sfx.wav",
         "-filter_complex", fc, "-map", "[a]", "-ar", "44100", "-c:a", "pcm_s16le", out + "/mix.wav"])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", out + "/video.mp4", "-i", out + "/mix.wav", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-shortest", "-movflags", "+faststart", out + "/final.mp4"])
    print("done", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--sheet" in sys.argv)
