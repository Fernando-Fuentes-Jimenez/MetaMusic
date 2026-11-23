#!/bin/bash
# Prepara el motor de vídeo de Pasta Clara en /home/claude
set -e
cd /home/claude
python3 -m venv --system-site-packages venv_st
./venv_st/bin/pip install -q sherpa-onnx==2.0.3 skia-python numpy soundfile
mkdir -p models && cd models
[ -d sherpa-onnx-supertonic-3-tts-int8-2026-05-11 ] || (curl -sSL -o st.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2 && tar xjf st.tar.bz2)
cd /home/claude && mkdir -p engine && cp -r /home/claude/metamusic/engine/*.py engine/
echo "motor listo"
