---
name: avatar-mix
description: >-
  Crea un video 16:9 con tu avatar HeyGen (tu cara + tu voz) presentando contenido,
  con montaje dinamico que alterna entre avatar a pantalla completa, avatar en esquina
  sobre un fondo, y solo fondo, con transiciones, musica y SFX. Acepta una URL o un guion.
  Usa cuando el usuario quiera generar un video de avatar a partir de una web o un guion.
---

# avatar-mix

Pipeline para producir un video 16:9 (1920x1080) donde **el avatar HeyGen del usuario**
presenta contenido sobre fondos generados, con un montaje que va alternando 3 modos.

## Motores
- **HeyGen MCP** (`https://mcp.heygen.com/mcp/v1/`, OAuth) → avatar hablando + audio/SFX.
- **HyperFrames** (`npx hyperframes`) o **tarjetas PIL** → video de fondo.
- **FFmpeg** (`scripts/composite.py`) → montaje, chroma-key, transiciones, mezcla de audio.

## Identidad del avatar (config por usuario)
- Copia `config/avatar.example.json` a `config/avatar.json` y rellena `avatar_id` + `voice_id`
  (descúbrelos con `list_avatar_looks` / `list_voices` del MCP; `get_current_user` para la cuenta).
- `config/avatar.json` está en `.gitignore` (es personal). Engine por defecto: **Avatar V**.
- Plan HeyGen recomendado: **Creator** (600 créditos). El free no permite varias escenas ni TTS.

## Set multicámara (looks del avatar)
`config/avatar.json` → `multicam.looks`: varios looks del MISMO avatar y fondo con encuadres
distintos (plano medio / primer plano, en horizontal y vertical). Intercalarlos por escena =
**multicámara real** (mucho mejor que cualquier zoom fake). Cada look lleva `aspect` y `framing`.

**Plan de cámaras (obligatorio al escribir el guion):** asignar a cada escena un `look` del set:
- **Nunca dos escenas seguidas con el mismo look** (si el avatar es visible en ambas).
- `fullscreen` en proyectos 16:9 o doble formato → SOLO looks `16:9`, alternando `wide`/`close`
  entre escenas fullscreen consecutivas (los verticales recortarían fatal a pantalla completa en 16:9).
- `side` y `corner` → cualquier look (el recuadro recorta); los **verticales encajan de lujo** aquí
  y así se intercalan también en videos horizontales. En `corner` favorece un `close`.
- Videos SOLO 9:16 (reels) → looks verticales en `fullscreen` (encuadre nativo, más real).
- **El patrón debe cambiar en cada video** (qué modo sigue a cuál, qué look abre, dónde va el
  `side`, cuántos `enter`…). Nunca repetir el plan del video anterior.

## Los 4 modos de escena
- `fullscreen` → avatar a pantalla completa (arranque siempre en este modo).
- `corner` → fondo a pantalla completa + avatar en recuadro PiP (webcam). **NO se borra el fondo**
  (borde + esquinas redondeadas). En **16:9** va abajo-derecha (`corner` en config, ~28%).
  En **9:16** va **centrado abajo y más grande** (`corner_9x16` en config: ~58%, `position: bottom-center`).
- `side` → split-screen: fondo full + **avatar en panel lateral a toda altura** (~42%, `side` en
  config, derecha por defecto). El `bg_visual` de estas escenas debe componer su contenido en la
  mitad IZQUIERDA (el panel tapa la derecha). En 9:16 cae automáticamente a `corner`.
- `bg_only` → solo el fondo; la voz del avatar sigue como locucion.
- **`enter: "slide"`** (opcional, en `corner`/`side`): el avatar entra deslizándose desde su borde
  (0.6s ease-out). Usar 1–2 veces por video, idealmente tras una escena `fullscreen` y con
  `transition: "cut"` en la escena anterior (con `fade` el avatar se ve doblado durante el cruce).

## Flujo (orden estricto por dependencias)

### 0. Config (una vez)
- `config/avatar.json`: rellenar `avatar_id` y `voice_id`. Obtenerlos con las tools MCP
  `list_avatar_looks` y `list_voices` (o `get_current_user`).
- Verificar entorno: `ffmpeg -version`, `node -v` (>=22), MCP conectado (`get_current_user`).

### 1. Entrada → guion por escenas
- Si la fuente es **URL** → `WebFetch` para extraer el contenido. Si es **guion**, usarlo tal cual.
- **El guion se escribe COMO SE HABLA, no como se escribe** (directriz de realismo: el TTS plano
  delata al avatar más que la cara). Reglas: frases cortas; preguntas retóricas ("¿Y esto qué
  significa?"); coletillas naturales ("ojo con esto", "y aquí viene lo bueno"); puntos suspensivos
  para forzar pausas; números redondeados como se dicen ("casi nueve mil euros", no "8.412,55").
  Nada de sintaxis "de blog" (subordinadas largas, conectores formales tipo "asimismo").
- **Máximo realismo (opcional):** `create_video_from_avatar` acepta **audio** en vez de `script`.
  Se puede generar la locución fuera (TTS más expresivo, o el usuario grabándose) y HeyGen solo
  hace el lipsync — respiraciones y énfasis reales. Ofrecerlo cuando el video sea importante.
- Redactar el guion hablado y segmentarlo en escenas. Crear `work/<slug>/script.json`
  (ver `templates/script.example.json`). Reglas:
  - Escena 1 = `fullscreen`.
  - Alternar `corner` / `side` / `bg_only` / `fullscreen` segun el ritmo del contenido, siguiendo
    el **plan de cámaras** (ver sección multicámara): patrón distinto en cada video.
  - Cada escena: `id`, `mode`, `narration`, `look` (id del look del set multicam), `enter`
    (opcional: `"slide"` en corner/side), `bg_visual` (`headline`, `subline`/`bullets`, `style`),
    `transition` (`fade`|`slide`|`cut`), `transition_after_sec`.
  - `style` de `bg_visual`: `title_card` | `bullets` | `fullbleed` | `screenshot` (con `image`).

### 2. Avatar (HeyGen MCP) — un clip por escena
Para cada escena, igual en todos los modos (no se toca el fondo del avatar):
- `mcp__heygen__create_video_from_avatar` con `avatarId` = **el `look` de la escena** (plan de
  cámaras; fallback: `avatar_id` de config), `voiceId`, `script` = narration,
  `aspectRatio` = **el `aspect` del look** (16:9 para looks horizontales, 9:16 para verticales),
  `resolution: "1080p"` (usar `720p` en pruebas), y SIEMPRE
  `engine: {"type": "avatar_v"}` (mejor calidad; ver config). Devuelve `video_id` y `status: waiting`.
- **SIEMPRE pasar `motionPrompt`** (photo_avatar + Avatar V lo admite; NO usar `expressiveness`, que es
  solo Avatar IV y lo rechaza con avatar_v). **Variar el motionPrompt POR ESCENA según su función**,
  no usar el mismo en todo el video (rompe la sensación de "misma persona en bucle"). Guía:
  - **Hook / intro (escena 1):** `"High energy, leans slightly toward the camera; expressive eyebrows;
    quick confident hand gestures; direct eye contact, as if hooking the viewer in the first seconds."`
  - **Explicación / desarrollo:** `"Calm, measured delivery; occasional thoughtful pauses; subtle nods;
    natural hand gestures that emphasize key points; gestures a bit more when mentioning numbers or results."`
  - **CTA / cierre:** `"Direct and confident; a small warm smile; slower deliberate gestures;
    steady eye contact with the camera, as if closing a deal."`
  Coste extra: 0 (solo un parámetro). Afinar los textos al tono de cada video.
- Plan free: cuota mensual de avatar muy limitada (~3 videos) y SIN TTS. Para varias escenas
  hace falta plan **Creator** ($29/mes, 600 creditos). ~20 creditos por video de 1 min.
- Poll con `mcp__heygen__get_video` (o REST `GET /v1/video_status.get?video_id=...` con
  `X-Api-Key` del `.env`) hasta `completed`; coger `video_url`.
- Descargar a `work/<slug>/clips/avatar_<id>.mp4` (curl).
- En `bg_only` el clip se genera igual; en el montaje solo se usa su audio.

### 3. Medir duraciones → completar script.json
- Para cada clip: `ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 clip`.
- Escribir `duration` (segundos) en cada escena de `script.json`. **Obligatorio** antes del paso 4.

### 4. Fondos (uno por escena → `work/<slug>/<bgdir>/<id>.mp4`)
**REGLA DE ORO (directriz del usuario):** los fondos deben ser **gráficos animados PROPIOS,
explicativos y visuales**, NO capturas de la web casi nunca. Generar nosotros con HyperFrames
mock-ups y data-viz que EXPLIQUEN el producto. Usar `hyperframes capture <url>` solo de forma
**puntual** (1 escena como mucho) cuando una prueba real aporte; no como recurso por defecto.

Componentes custom que funcionan muy bien (autorízalos en `work/<slug>/hf/index.html`):
  - **Chat del agente**: burbujas usuario/agente que entran en secuencia, con checks (✓ Conciliada…),
    adjuntos (📎 factura.pdf) y chips de preguntas. Comunica "todo desde un chat".
  - **Tarjeta de datos / conciliación**: card con **número que cuenta** (GSAP onUpdate → fmtEur con
    miles "8.412,55 €"), filas (cobros/comisiones/reembolsos) y sello "Conciliado". Para cifras/dinero.
  - **Hub de integraciones**: pill central "tu-app · API + MCP" → chips Claude/Cursor/ChatGPT + nota.
  - **Title cards** (intro/outro) y **flujos** (icono→agente→hecho).
  - **Badge de marca SIEMPRE** (directriz del usuario, 2026-07-09): logo + tagline arriba-izquierda
    en toda escena con gráficos (corner/side/bg_only), salvo reveals/title cards donde el wordmark
    grande ya es la firma, o videos marcados "sin marca". Ref: `.badge` en work/launch2/hf/index.html.
  - Estética de marca: bg #0b0f1a, accent #3ddc97, glows en deriva, entradas animadas, paneo/zoom suave.

Modo rápido sin gráficos ricos: `--mode card` (tarjetas PIL responsivas).

**Capturas reales de navegador como fondo (validado en claude-aikount, 2026-07-10):** para
tutoriales, grabar el flujo real con las tools de claude-in-chrome (`gif_creator`, sin watermark
ni labels) → GIF→MP4 (`ffmpeg -vf fps=30`) en `work/<slug>/captures/`. El index.html dibuja solo
la `.capzone` (marco vacío) y `python3 scripts/overlay_captures.py --slug <slug> --aspect ...`
incrusta cada captura en su zona tras `make_bg` (lee `bg_visual.capture` + `zone_16x9`/`zone_9x16`
del script.json; congela el último frame con tpad; entra en t=1.2s). OJO: revisar que en las
capturas no salgan tokens/API keys (revocar antes de publicar) ni contenido no deseado (recortar
con `-t` si hace falta).

**Registro siempre al día:** en cada render de HyperFrames el skill **sincroniza las animaciones
nuevas** del registro (`scripts/sync_animations.py`, lo llama `make_bg.py` una vez por proyecto vía
marcador `.animations_synced`). Así las animaciones que vaya publicando HeyGen (p. ej. las 9 de
código: `code-typing`, `code-diff`, `code-highlight`, `code-morph`, `code-particle-assemble`…)
aparecen disponibles en `compositions/` sin tocar nada. Manual: `python3 scripts/sync_animations.py
--hf work/<slug>/hf` (o `--all` para todo el registro; `HF_NO_SYNC=1` lo desactiva). Úsalas vía
`data-composition-src="compositions/<nombre>.html"`. Ideal para vídeos **code/dev explainer**
(avatar en `corner` + animación de código de fondo).

**Animaciones al ritmo de la voz (directriz del usuario — validado en mejor-ia-contabilidad):**
los elementos NO se pintan del tirón con staggers fijos; cada tile/burbuja/fila/sello aparece
cuando la narración dice exactamente eso. Flujo:
  1. Por cada escena con gráficos, `mcp__heygen__create_speech` con la MISMA voz+speed+locale del
     avatar y el texto exacto de `narration` → devuelve `word_timestamps` (start/end por palabra).
  2. Escalar cada timestamp a la duración real del clip: `t_real = t_tts × (dur_clip / dur_tts)`
     (el clip de avatar trae lead-in/tail; el escalado lineal es suficiente, ±0.5s es aceptable
     y mejor que llegue un pelín antes que después).
  3. Elegir la palabra-gatillo de cada elemento (ej.: tile "conciliar el banco" → palabra
     "conciliar"; sello "Conciliado" → la palabra final "conciliado"; chip Claude → "Claude";
     contador de dinero → "el dinero llega"). Poner esos tiempos como offsets absolutos en las
     animaciones GSAP del index.html (arrays tipo `const T2=[7.0,9.66,...]` por escena, comentando
     la palabra-gatillo de cada uno).
  4. Actualizar `sfx_manifest.json` con los MISMOS tiempos (pop al aparecer el elemento, chime en
     los checks, achievement en el sello final, coins al hablar de dinero).
  Nota: los timestamps del TTS starfish con la voz habitual clavan el pacing del clip Avatar V
  (misma fuente); si cambian los clips (regeneración), re-medir duraciones y re-escalar.

Flujo HyperFrames (v0.6.98, requiere Chrome — validado):
  1. **Dos proyectos** por formato: `work/<slug>/hf/` (16:9, root 1920x1080) y
     `work/<slug>/hf_9x16/` (vertical, root 1080x1920). `make_bg.py` elige por `--aspect`.
     Scaffold: `npx hyperframes init hf` (copiar package/hyperframes/meta.json al hf_9x16).
  2. Autorizar `index.html` con los componentes custom: cada escena = elementos `class="clip"` +
     `data-start`(acumulado)/`data-duration`(real)/`data-track-index`; timeline maestra paused en
     `window.__timelines["main"]`; `data-duration` del root = total. Solo lógica determinista.
  3. `python3 scripts/make_bg.py --slug <slug> --mode hyperframes --aspect 16:9|9:16`
     (renderiza el proyecto y trocea `renders/` en `<bgdir>/<id>.mp4`).
Para máxima calidad se pueden instalar las skills oficiales (`npx skills add heygen-com/hyperframes`
→ `/hyperframes-read-first`).

### 5. Musica / SFX (HeyGen MCP) — CONTEXTUAL POR VIDEO
La gracia: elegir SFX que peguen con el contenido de CADA video, no siempre los mismos.
- Musica: `search_audio_sounds` (type=music) con `music_query` → `assets/music.*`.
- SFX base: whoosh de transicion → `assets/sfx/whoosh.mp3`.
- SFX contextuales: leer el guion y, por cada momento que lo pida, buscar el efecto adecuado en
  HeyGen (`type=sound_effects`) y descargarlo a `assets/sfx/`. Ej.: "riser" en la intro,
  "coins/cash register" al hablar de dinero/Stripe, "single chime/notification" cuando aparece un
  chat, "achievement" al completar algo (factura conciliada, 303 listo).
- Escribir el manifiesto `work/<slug>/sfx_manifest.json`:
  `[{ "scene": <id>, "offset": <seg desde inicio de la escena>, "file": "assets/sfx/x.mp3", "gain_db": -12 }]`
  (tambien admite `{"at": <seg en timeline final>}`).
- HeyGen es la fuente de SFX; no hay otro CLI para esto (HyperFrames `tts/beats` es voz/musica).

### 6. Montaje (FFmpeg)
- `python3 scripts/composite.py --slug <slug> --aspect 16:9|9:16 [--music ...] [--whoosh assets/sfx/whoosh.mp3] [--sfx-manifest work/<slug>/sfx_manifest.json]`
- Produce `output/<slug>{_9x16}.mp4`, con los 4 modos, transiciones (`xfade`/`acrossfade`),
  musica con ducking (`sidechaincompress`) y SFX (con `alimiter` final).
  **La salida YA sale sin metadata** (composite.py llama a `strip_meta` al final). Un solo archivo limpio.
- **Pases de realismo automáticos** (todos activos por defecto, con flag para desactivar):
  - **Punch-in** en escenas `fullscreen`: zoom lento continuo 1.00→1.05 (1.04 en 9:16) durante
    toda la escena, la cámara nunca está quieta. **SIN cortes de encuadre** (directriz del
    usuario: el corte "multicam" no gusta; el zoom sí). Desactivar: `--no-punch`.
  - **Grading unificado**: eq (contraste/saturación) + viñeta suave sobre todas las escenas
    (avatar y fondos comparten look). El **grano fino va SOLO sobre el avatar** (frame completo
    en fullscreen, píxeles del PiP en corner) — **nunca sobre los gráficos de HyperFrames**
    (directriz del usuario: en gráficos no tiene sentido). Ajustable en `config/avatar.json` →
    `"grade": {contrast, saturation, vignette_angle, grain, enabled}`. Desactivar: `--no-grade`.
  - **Loudnorm final** a -14 LUFS / -1.5 dBTP (target YouTube/TikTok), sobre la mezcla completa.
    Desactivar: `--no-loudnorm`.
- **Doble formato sin gastar avatar**: los mismos clips sirven para 16:9 y 9:16. Atajo:
  `bash scripts/run.sh <slug> <musica> <card|hyperframes> both` genera las dos versiones (ya limpias).

### 6.5 Subtítulos estilo Hormozi (recomendado para 9:16 — Reels/TikTok)
Palabras grandes en MAYÚSCULAS, palabra activa resaltada en acento, animadas. Flujo:
- Timing por palabra, dos fuentes (guardar en `work/<slug>/captions_src.json`,
  `[{id, tts_dur, words:[{t,start,end}]}]`):
  - `mcp__heygen__create_speech` (voz starfish) → `word_timestamps` (gasta créditos API; escalar
    t_real = t_tts × dur_clip/dur_tts).
  - **whisper.cpp local (PREFERIDO, validado 2026-07-10, gratis y sin escalado)**: transcribir el
    clip final → `ffmpeg -ar 16000 -ac 1` + `~/Documents/whisper.cpp/build/bin/main -m
    models/ggml-small.bin -l es -ml 1 -sow -oj` → timestamps exactos del audio real (f=1);
    también sirve para los triggers de las animaciones. CORREGIR marcas mal transcritas
    (Cloud/Clout→Claude, iCount→aikount) antes de quemar subs. El `whisper` de Anaconda (Python)
    sigue roto (NumPy/Numba) — usar SIEMPRE el binario de whisper.cpp.
- `python3 scripts/make_captions.py --slug <slug> --aspect 9:16` → genera `work/<slug>/hf_captions/`
  (proyecto HyperFrames transparente; escala cada escena a la duración real del clip y evita solapes).
- `python3 scripts/burn_captions.py --slug <slug> --aspect 9:16` → renderiza el MOV con alfa
  (ProRes 4444), hace el overlay, **deja la salida sin metadata** y borra el MOV. Produce
  `output/<slug>_9x16_subs.mp4` (un solo archivo limpio).
  - Detalles internos: MOV (no WebM; el VP9-alpha no overlaya bien con este FFmpeg). `capY` (~60% alto)
    coloca los subs por encima del avatar (bottom-center).

### 7. Entregar
- Mostrar la ruta de `output/<slug>.mp4` y un resumen de escenas/duracion.
- **Los MP4 de `output/` ya salen sin metadata** (encoder/fecha/handler) — no hay doble versión.
  `scripts/strip_meta.sh` queda disponible por si hay que limpiar un fichero externo.

### 8. Publicar en redes (Upload-Post API — subida directa del fichero local)
Sube los DOS formatos a todas las redes con `scripts/publish.sh` (API REST de Upload-Post via curl;
**sube el MP4 local directamente**, sin staging ni URL pública). Genérico: cada persona usa su
`UPLOAD_POST_API_KEY` (.env) y su propio perfil.
- Perfil: cada cuenta tiene uno o varios "user profiles" con sus redes conectadas. Listar con
  `curl -H "Authorization: Apikey $KEY" https://api.upload-post.com/api/uploadposts/users`.
- Vertical (con subs) → short-form:
  `bash scripts/publish.sh output/<slug>_9x16_subs.mp4 <perfil> tiktok,instagram,youtube,threads "<titulo>" "<desc>" "#hashtags" REELS`
- Horizontal → long-form:
  `bash scripts/publish.sh output/<slug>.mp4 <perfil> youtube,linkedin,facebook,x "<titulo>" "<desc>"`
- El script es asincrono (`request_id`) y hace poll a `/uploadposts/status`. Confirmar SIEMPRE antes.
- Regla: **vertical → TikTok/Reels/Shorts/Threads · horizontal → YouTube/LinkedIn/Facebook/X**.
- **Declaración de IA obligatoria (directriz del usuario, 2026-07-08):** en YouTube SIEMPRE
  `youtubeContainsSyntheticMedia: true` (y en TikTok `tiktokIsAigc: true`). El avatar realista
  con voz clonada lo exige la política de la plataforma; la nota es discreta y no declarar
  expone el canal a strikes/retirada.
- Alternativa: el MCP `Upload-Post` (tools `upload_video`/`get_status`), pero al ser remoto NO lee
  rutas locales (requiere `open_upload_studio` o URL publica) — por eso el script con la API es mejor aqui.

## Atajo determinista
Pasos 3-6 (cuando ya existen `clips/avatar_<id>.mp4`): `bash scripts/run.sh <slug> [musica]`.

## Estructura por proyecto (work/<slug>/)
- `script.json` (guion+duraciones), `clips/avatar_<id>.mp4` (HeyGen Avatar V),
- `hf/` (proyecto HyperFrames 16:9) y `hf_9x16/` (proyecto HyperFrames vertical),
- `hf/captured/` (solo si se usó `hyperframes capture` puntual),
- `bg/` y `bg_9x16/` (fondos troceados por escena), `sfx_manifest.json`.

## Notas
- `config/avatar.json`: marca, `corner` (PiP 16:9) y `corner_9x16` (PiP vertical: bottom-center, ~58%).
- Si `make_bg --mode card` no encuentra fuente TTF, instalar fuentes o usar `--mode hyperframes`.
- El FFmpeg de Homebrew de esta maquina **no trae `drawtext`** (sin libfreetype): las tarjetas PIL
  se renderizan con Pillow. Los gráficos ricos van por HyperFrames (Chrome headless).
