# Pasta Clara: guía del canal (léela entera antes de trabajar)

Canal de YouTube Shorts «Pasta Clara»: la economía de España explicada en 1 minuto. Dueño: Fer. Claude lleva el canal.
Mascota y presentador: «Duro», una moneda de 5 pesetas cascarrabias con bigote y cascos.

## Cómo está montado
- Rama `pasta-clara-media` de este repo (Fernando-Fuentes-Jimenez/MetaMusic) = carpeta del proyecto.
- `engine/`: motor de vídeo (tts.py, render.py, build.py, branding.py). `engine/setup.sh` lo instala en /home/claude.
- `scripts/*.json`: guiones (escenas → frases con `tts` y `chunks` de subtítulo + `elements` animados). Úsalos como plantilla.
- `calendario.json`: lo lee un flujo de n8n cada día a las 19:00 (Europe/Madrid) y publica el vídeo cuya `fecha` es hoy (si `n8n` no es false).
  Cada entrada: fecha (YYYY-MM-DD), url (raw.githubusercontent.com/Fernando-Fuentes-Jimenez/MetaMusic/pasta-clara-media/<archivo>.mp4), title (≤100 car., acaba en #shorts), description, tags (separados por comas), categoryId "27".
- Windsor.ai (conector YouTube, cuenta 118451 = canal Pasta Clara): leer estadísticas y comentarios, responder/moderar, editar título/descr./etiquetas. La subida de vídeos por Windsor está bloqueada (rate limit): NO subir por Windsor, para eso está n8n.

## Fabricar un vídeo
1. `bash /home/claude/metamusic/engine/setup.sh`
2. Escribir el guion en `/home/claude/scripts/<n>_<tema>.json` (formato de los ejemplos). Números en `tts` escritos en letra; cifras en `chunks`.
3. `/home/claude/venv_st/bin/python /home/claude/engine/build.py <guion.json> /home/claude/out/<n>` → `final.mp4` (~80 s de render).
4. Revisar: `ffmpeg -i final.mp4 -vf "fps=1/4,scale=270:-1,tile=6x2" -frames:v 1 sheet.png` y mirar la hoja; nada pisa los subtítulos (y≈1290) ni la zona inferior.
5. Copiar el mp4 a la raíz de la rama con nombre `AAAA-MM-DD_tema.mp4`, añadir la entrada en calendario.json, commit y push (`git -c push.negotiate=true push`).

## Reglas editoriales
- Temas: dinero y economía cotidiana en España (súper, impuestos, luz, vivienda, sueldos, empresas conocidas, precios, curiosidades). Mezclar actualidad de la semana con temas atemporales.
- Datos reales y verificados con búsqueda web, de fuentes de este año. Fuentes en el pie de la última escena y en la descripción.
- 40-60 s, 5 escenas, gancho fuerte en la primera frase, pregunta a comentarios al final.
- Neutralidad política: describir, nunca opinar ni dar veredictos. Nada de consejos de inversión personalizados.
- Cada vídeo con enfoque y estructura propios (evitar plantillas clonadas: política de «contenido no auténtico» de YouTube).
- Voz: Supertonic 3, sid 7 (ya configurado). Estilo visual: el del motor, no cambiarlo sin que Fer lo pida.

## Comentarios
- Responder como Pasta Clara: cercano, con humor, breve, en español. Aportar dato o fuente si preguntan algo.
- Prioridad: preguntas y comentarios con más likes. Máximo ~10 respuestas al día.
- Spam, insultos o enlaces sospechosos → moderate_comment rejected. No discutir de política.
