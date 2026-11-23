"""Per-sentence TTS with Supertonic 3 (sid 7, es). Usage: tts.py script.json outdir"""
import json, sys, os
import numpy as np, soundfile as sf
import sherpa_onnx as so

M = "/home/claude/models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11/"
FPS = 30
PAUSE = 0.22

def make_tts():
    sc = so.OfflineTtsSupertonicModelConfig(
        duration_predictor=M + "duration_predictor.int8.onnx",
        text_encoder=M + "text_encoder.int8.onnx",
        vector_estimator=M + "vector_estimator.int8.onnx",
        vocoder=M + "vocoder.int8.onnx",
        tts_json=M + "tts.json",
        unicode_indexer=M + "unicode_indexer.bin",
        voice_style=M + "voice.bin")
    mc = so.OfflineTtsModelConfig()
    mc.supertonic = sc
    mc.num_threads = 2
    return so.OfflineTts(so.OfflineTtsConfig(model=mc))

def trim(x, sr, thr=0.012):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(0.03 * sr)); b = min(len(x), idx[-1] + int(0.06 * sr))
    return x[a:b]

def main(script_path, out):
    os.makedirs(out, exist_ok=True)
    script = json.load(open(script_path))
    tts = make_tts()
    sr = None
    timing = {"scenes": []}
    full = []
    t = 0.0
    for si, scene in enumerate(script["scenes"]):
        sc_start = t
        sents = []
        for s in scene["sentences"]:
            g = so.GenerationConfig()
            g.sid = 7; g.num_steps = 12; g.speed = 1.05
            g.extra = {"lang": "es"}
            a = tts.generate(s["tts"], g)
            sr = a.sample_rate
            x = trim(np.array(a.samples, dtype=np.float32), sr)
            d = len(x) / sr
            sents.append({"start": t - sc_start, "end": t - sc_start + d, "chunks": s["chunks"]})
            full.append(x); full.append(np.zeros(int(PAUSE * sr), np.float32))
            t += d + PAUSE
        # extra tail for scene, rounded to frames
        tail = scene.get("tail", 0.35)
        full.append(np.zeros(int(tail * sr), np.float32)); t += tail
        dur = t - sc_start
        nfr = int(np.ceil(dur * FPS))
        pad = nfr / FPS - dur
        full.append(np.zeros(int(round(pad * sr)), np.float32)); t = sc_start + nfr / FPS
        timing["scenes"].append({"start": sc_start, "frames": nfr, "sentences": sents})
    voice = np.concatenate(full)
    sf.write(os.path.join(out, "voice.wav"), voice, sr)
    timing["sr"] = sr; timing["total"] = t
    json.dump(timing, open(os.path.join(out, "timing.json"), "w"), indent=1)
    print("total", round(t, 2), "s")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
