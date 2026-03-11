# Weborax Model

This repository contains two Python tools:

1. An AI video generation studio for creating Shorts-style videos with LLM-written scripts, generated images, voiceover, music, and optional YouTube upload.
2. A website cloner that mirrors a public site into static local files.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Make sure `ffmpeg` is available on your system path for video rendering.

## AI Video Studio

Primary entry points:

- `python src/main.py`
- `python src/app.py`
- `python scheduler.py --test`
- `python run_bot.py`

Environment variables are loaded from `.env`. Common settings include:

- `LLM_PROVIDER`
- `BYTEZ_API_KEY`
- `GEMINI_API_KEY`
- `AIMLAPI_KEY`
- `CHATGPT_IMAGE_API_KEY`
- `VIDEO_DURATION`
- `YOUTUBE_CLIENT_SECRET_FILE`

Generated files are written under `outputs/`.

## Website Cloner

```bash
python clone_site.py https://imageconverttools.site --output cloned_site --max-pages 400
```

Notes:

- Only public pages and same-domain assets are cloned.
- JavaScript-heavy pages may need browser automation instead of plain HTTP scraping.
- Respect robots, rate limits, and the target site's terms before using it.
