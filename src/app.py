import sys
import os

# Fix Windows CP1252 encoding crash with emoji in print()
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import asyncio
import re
import traceback
import time
import random
import json
import base64
import requests as http_requests
from io import BytesIO
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure src modules are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_config import Config
from modules.llm_client import LLMClient

# --- Image & Video libraries ---
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
)

app = FastAPI()

# Global status tracker
status_log = ["System ready - High-Quality AI Studio"]


def safe_print(msg):
    try:
        print(str(msg))
    except (UnicodeEncodeError, Exception):
        try:
            print(msg.encode('ascii', 'replace').decode())
        except Exception:
            pass


# Mount static files
os.makedirs("src/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/static"), name="static")


class GenerateRequest(BaseModel):
    prompt: str

class ScriptUpdate(BaseModel):
    script: str

# LLM Client
llm = LLMClient()


# ================================================================
# SCRIPT PARSER
# ================================================================

def parse_script(script_text):
    """Parse script with Scene X markers, Visual and dialogue fields."""
    scenes = []
    
    markers = list(re.finditer(
        r'(?im)(?:^[#\s]*)?(?:🎬\s*)?Scene\s*(\d+)\s*(?:[:\-—–]+[^\n]*)?',
        script_text
    ))
    
    if not markers:
        safe_print(f"DEBUG: No scene markers found. Script length={len(script_text)}")
        return scenes
    
    safe_print(f"DEBUG: Found {len(markers)} scene markers")
    
    # Last occurrence of each scene number wins (skips template/preamble)
    seen_numbers = {}
    for marker in markers:
        num = int(marker.group(1))
        seen_numbers[num] = marker
    
    unique_markers = sorted(seen_numbers.values(), key=lambda m: m.start())
    
    for idx, marker in enumerate(unique_markers):
        scene_num = int(marker.group(1))
        start = marker.end()
        end = unique_markers[idx + 1].start() if idx + 1 < len(unique_markers) else len(script_text)
        block = script_text[start:end]
        
        if not block.strip():
            continue
        
        try:
            # Extract Visual
            visual_match = re.search(
                r'(?i)\*{0,2}Visual[:\s]*\*{0,2}\s*[:\-]?\s*(.*?)(?=\n\s*\*{0,2}(?:Camera|Narrator|Rahul|Modi|Yogi|Kejriwal|Shah|Amit|Common|Text|Background|End|Audience|\w+\s*\()[:\*]|\Z)',
                block, re.DOTALL
            )
            visual = visual_match.group(1).strip() if visual_match else ""
            visual = re.sub(r'[*_#]', '', visual).strip()
            visual = re.sub(r'\n+', ' ', visual).strip()

            # Extract narration/dialogue
            narration_parts = []
            for m in re.finditer(r'(?i)\*{0,2}Narrator[^:]*:\*{0,2}\s*["\u201c]?([^"\u201d\n]+)["\u201d]?', block):
                narration_parts.append(m.group(1).strip())
            for m in re.finditer(r'(?i)\*{0,2}(?:Rahul|Modi|Kejriwal|Yogi|Shah|Amit|Common\s*Man|Narendra)[^:]*:\*{0,2}\s*["\u201c]?([^"\u201d\n]+)["\u201d]?', block):
                narration_parts.append(m.group(1).strip())
            if not narration_parts:
                for m in re.finditer(r'"([^"]{5,})"', block):
                    narration_parts.append(m.group(1).strip())
            
            narration = " ... ".join(
                re.sub(r'[*_#]', '', p).strip()
                for p in narration_parts if p.strip()
            )

            if visual or narration:
                scenes.append({
                    "id": scene_num,
                    "visual": visual[:500],
                    "narration": narration
                })
        except Exception as e:
            safe_print(f"DEBUG: Error parsing scene {scene_num}: {e}")
            continue
    
    return scenes


# ================================================================
# AI IMAGE GENERATION (AIMLAPI free → DALL-E 3 → Pillow fallback)
# ================================================================

def _build_3d_prompt(visual_desc):
    """Build a rich 3D cinematic prompt."""
    return (
        f"3D cartoon animation scene in Pixar DreamWorks style, "
        f"cinematic lighting, dramatic camera angles, vibrant saturated colors, "
        f"ultra-detailed 3D render, professional quality, no text or watermarks. "
        f"Scene: {visual_desc}"
    )[:2000]


def _download_and_save_image(image_url, filepath):
    """Download image from URL and resize to video dimensions."""
    img_response = http_requests.get(image_url, timeout=30)
    if img_response.status_code == 200 and len(img_response.content) > 1000:
        img = Image.open(BytesIO(img_response.content))
        img = img.resize((Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), Image.LANCZOS)
        img.save(filepath, "PNG", optimize=True)
        return True
    return False


def generate_ai_image(visual_desc, scene_id, output_dir):
    """Generate high-quality 3D image. Tries: AIMLAPI → DALL-E 3 → Pillow."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"scene_{scene_id:02d}.png")
    prompt = _build_3d_prompt(visual_desc)
    
    # --- Provider 1: AIMLAPI (free tier, flux model) ---
    aiml_key = Config.AIMLAPI_KEY
    if aiml_key:
        for attempt in range(2):
            try:
                safe_print(f"  [AIMLAPI] Attempt {attempt+1} for scene {scene_id}...")
                response = http_requests.post(
                    "https://api.aimlapi.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {aiml_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "flux/schnell",
                        "prompt": prompt,
                        "n": 1,
                        "image_size": {"width": 1024, "height": 1792},
                    },
                    timeout=90,
                )
                if response.status_code == 200:
                    data = response.json()
                    # AIMLAPI returns URL or base64
                    img_data = data.get("data", [{}])[0]
                    image_url = img_data.get("url", "")
                    b64 = img_data.get("b64_json", "")
                    
                    if image_url:
                        if _download_and_save_image(image_url, filepath):
                            safe_print(f"  [OK] AIMLAPI scene {scene_id} saved!")
                            return filepath
                    elif b64:
                        img_bytes = base64.b64decode(b64)
                        img = Image.open(BytesIO(img_bytes))
                        img = img.resize((Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), Image.LANCZOS)
                        img.save(filepath, "PNG", optimize=True)
                        safe_print(f"  [OK] AIMLAPI scene {scene_id} saved (b64)!")
                        return filepath
                else:
                    safe_print(f"  [WARN] AIMLAPI {response.status_code}: {response.text[:150]}")
            except Exception as e:
                safe_print(f"  [WARN] AIMLAPI attempt {attempt+1} failed: {e}")
            time.sleep(2)
    
    # --- Provider 2: DALL-E 3 (paid, OpenAI) ---
    openai_key = Config.CHATGPT_IMAGE_API_KEY
    if openai_key:
        for attempt in range(2):
            try:
                safe_print(f"  [DALL-E 3] Attempt {attempt+1} for scene {scene_id}...")
                response = http_requests.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1792",
                        "quality": "standard",
                        "response_format": "url",
                    },
                    timeout=90,
                )
                if response.status_code == 200:
                    image_url = response.json()["data"][0]["url"]
                    if _download_and_save_image(image_url, filepath):
                        safe_print(f"  [OK] DALL-E 3 scene {scene_id} saved!")
                        return filepath
                else:
                    safe_print(f"  [WARN] DALL-E 3 {response.status_code}: {response.text[:150]}")
                    # If billing issue, don't retry
                    if "billing" in response.text.lower():
                        break
            except Exception as e:
                safe_print(f"  [WARN] DALL-E 3 attempt {attempt+1} failed: {e}")
            time.sleep(2)
    
    # --- Provider 3: Pillow fallback ---
    safe_print(f"  [FALLBACK] Using Pillow for scene {scene_id}")
    return generate_pillow_fallback(visual_desc, scene_id, output_dir)



def generate_pillow_fallback(visual_desc, scene_id, output_dir):
    """Pillow cartoon fallback when DALL-E fails."""
    W, H = Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT
    
    v = visual_desc.lower()
    if "parliament" in v or "sansad" in v or "arena" in v:
        bg_colors = [(40, 40, 70), (20, 20, 50)]
    elif "petrol" in v or "pump" in v:
        bg_colors = [(255, 200, 150), (200, 120, 80)]
    elif "school" in v or "student" in v or "degree" in v:
        bg_colors = [(200, 230, 255), (150, 180, 220)]
    elif "bulldozer" in v or "law" in v:
        bg_colors = [(255, 180, 100), (200, 130, 60)]
    elif "reel" in v or "social" in v or "media" in v:
        bg_colors = [(100, 50, 150), (60, 20, 100)]
    elif "family" in v or "tv" in v or "common" in v:
        bg_colors = [(180, 200, 180), (130, 150, 130)]
    elif "vote" in v or "remote" in v or "public" in v:
        bg_colors = [(200, 180, 50), (150, 130, 30)]
    else:
        bg_colors = [(80, 100, 140), (40, 50, 80)]

    c1, c2 = np.array(bg_colors[0], dtype=np.float32), np.array(bg_colors[1], dtype=np.float32)
    ratios = np.linspace(0, 1, H).reshape(-1, 1)
    gradient = (c1 * (1 - ratios) + c2 * ratios).astype(np.uint8)
    gradient_img = np.broadcast_to(gradient[:, np.newaxis, :], (H, W, 3)).copy()
    img = Image.fromarray(gradient_img)
    draw = ImageDraw.Draw(img)
    
    floor_y = int(H * 0.72)
    draw.rectangle([0, floor_y, W, H], fill=tuple(max(0, c - 30) for c in bg_colors[1]))
    
    char_colors = [(255, 153, 51), (65, 105, 225), (50, 205, 50), (220, 20, 60)]
    names = re.findall(r'(?i)(Modi|Rahul|Kejriwal|Yogi|Shah|Common Man)', visual_desc)
    if not names:
        names = ["Leader 1", "Leader 2"]
    names = list(dict.fromkeys(names))[:4]
    
    for ci, name in enumerate(names):
        x = int(W * (ci + 1) / (len(names) + 1))
        color = char_colors[ci % len(char_colors)]
        body_top = int(H * 0.42)
        draw.rounded_rectangle([x-60, body_top, x+60, floor_y-10], radius=25, fill=color)
        skin = (255, 220, 185)
        hr = 50
        hy = body_top - hr + 10
        draw.ellipse([x-hr, hy-hr, x+hr, hy+hr], fill=skin, outline=(200, 170, 140), width=3)
        for dx in [-15, 15]:
            draw.ellipse([x+dx-5, hy-5, x+dx+5, hy+5], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.ellipse([x+dx-2, hy-2, x+dx+2, hy+2], fill=(0, 0, 0))
        draw.arc([x-12, hy+10, x+12, hy+24], start=0, end=180, fill=(200, 50, 50), width=3)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), name, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw//2, floor_y + 5), name, fill=(255, 255, 255), font=font)
    
    filepath = os.path.join(output_dir, f"scene_{scene_id:02d}.png")
    img.save(filepath, "PNG", optimize=True)
    return filepath


# ================================================================
# VOICEOVER (edge-tts, async)
# ================================================================

async def generate_voiceover(text, output_path, voice=None):
    """Generate voiceover using edge-tts."""
    if not voice:
        voice = Config.NARRATOR_VOICE
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    communicate = edge_tts.Communicate(text, voice, rate="-5%", pitch="-3Hz")
    await communicate.save(output_path)


# ================================================================
# VIDEO ASSEMBLY (moviepy, 30s cap)
# ================================================================

def assemble_video(scene_images, scene_audios, output_path, max_duration=None):
    """Assemble scene images + audio into final MP4, capped at max_duration."""
    if max_duration is None:
        max_duration = Config.VIDEO_DURATION
    
    clips = []
    total_dur = 0.0

    for i, (img_path, audio_path) in enumerate(zip(scene_images, scene_audios)):
        if not img_path or not os.path.exists(img_path):
            continue

        duration = 5.0
        audio_clip = None
        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration + 0.3
            except Exception as e:
                safe_print(f"  [WARN] Audio load failed for scene {i+1}: {e}")

        # Cap remaining duration
        remaining = max_duration - total_dur
        if remaining <= 0:
            break
        duration = min(duration, remaining)
        
        if duration < 1.0:
            break

        img_clip = ImageClip(img_path, duration=duration)
        img_clip = img_clip.resized(lambda t: 1.0 + 0.04 * (t / max(duration, 0.1)))
        img_clip = img_clip.with_position("center")

        if audio_clip:
            if audio_clip.duration > duration:
                audio_clip = audio_clip.subclipped(0, duration)
            img_clip = img_clip.with_audio(audio_clip)

        clips.append(img_clip)
        total_dur += duration

    if not clips:
        safe_print("  [ERROR] No clips to assemble!")
        return None

    safe_print(f"  [ASSEMBLE] Concatenating {len(clips)} clips, total ~{total_dur:.1f}s...")
    final = concatenate_videoclips(clips, method="compose")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    final.write_videofile(
        output_path,
        fps=Config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2,
        logger=None,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )

    final.close()
    for c in clips:
        try:
            c.close()
        except:
            pass

    return output_path


# ================================================================
# YOUTUBE UPLOAD
# ================================================================

def upload_to_youtube(video_path, title, description, tags):
    """Upload video to YouTube using the YouTubeUploader module."""
    try:
        from modules.youtube_uploader import YouTubeUploader
        
        uploader = YouTubeUploader()
        if not uploader.authenticate():
            return {"error": "YouTube authentication failed. Make sure Client_secret.json exists."}
        
        metadata = {
            "title": title[:100],
            "description": description,
            "tags": tags,
        }
        
        result = uploader.upload_video(video_path, metadata)
        return result
    except ImportError as e:
        return {"error": f"YouTube upload dependencies missing: {e}"}
    except Exception as e:
        return {"error": f"YouTube upload failed: {e}"}


# ================================================================
# SCRIPT GENERATION (via LLM)
# ================================================================

def generate_satire_script():
    """Generate a 30-second political satire script using the configured LLM."""
    prompt = """You are a top-tier Indian political satire writer for YouTube Shorts.

Write a VERY SHORT (30 seconds / 60-80 words) Hindi-English mix comedy script.

FORMAT - exactly 4 scenes:

Scene 1 -- Hook
Visual: [describe a funny 3D cartoon scene with Indian politicians]
Narrator: [one punchy sarcastic line in Hinglish]

Scene 2 -- Problem
Visual: [visual gag about inflation/unemployment/education]  
Modi: [funny dialogue]
Rahul: [funny response]

Scene 3 -- Punchline
Visual: [visual comedy twist]
Kejriwal: [sarcastic one-liner]

Scene 4 -- Ending
Visual: [common man reaction shot]
Narrator: [final punchline about voting power]

RULES:
- Keep it FUNNY and SARCASTIC
- No hate speech, no abuse
- Mix Hindi + English naturally
- Total spoken words: 60-80 (fits 30 seconds)
- Each dialogue max 15 words
- Make it VIRAL-worthy"""

    try:
        script = llm.generate(prompt)
        return script
    except Exception as e:
        safe_print(f"Script generation error: {e}")
        # Return a default script
        return DEFAULT_SCRIPT


DEFAULT_SCRIPT = """
Scene 1 -- Sansad Reality Show Opening
Visual: Indian Parliament turned into a WWE arena with spotlights and dramatic music. 3D cartoon politicians sitting at desks.
Narrator: "Swagat hai duniya ke sabse bade reality show mein... jahan action real hai, solutions scripted!"

Scene 2 -- Inflation Battle
Visual: Petrol pump meter spinning wildly like a slot machine. Price board showing 999.
Modi: "Mitron, petrol mehnga nahi hua... aapki pocket choti ho gayi hai!"
Rahul: "Yeh petrol hai ya Bitcoin? Roz naya ATH!"

Scene 3 -- Education Crisis  
Visual: Students throwing paper plane degrees out of college windows.
Kejriwal: "Degree free de denge... naukri ka jugaad aap khud karo!"

Scene 4 -- Common Man Ending
Visual: Common man holding TV remote labelled VOTE. Looks directly at camera.
Narrator: "Show unka hai... par remote aapke haath mein hai. Use it wisely!"
"""


# ================================================================
# FULL PIPELINE (Generate → Render → Upload)
# ================================================================

async def run_full_pipeline(script_text=None, auto_upload=True):
    """Full pipeline: parse/generate script → DALL-E images → voiceover → video → YouTube."""
    global status_log
    status_log = ["Starting high-quality AI video pipeline..."]
    
    Config.ensure_directories()
    
    # --- Step 1: Get Script ---
    if not script_text or len(script_text.strip()) < 50:
        status_log.append("Generating script with AI (Bytez LLM)...")
        try:
            script_text = generate_satire_script()
            status_log.append("Script generated!")
            safe_print(f"DEBUG: Generated script:\n{script_text[:500]}")
        except Exception as e:
            safe_print(f"Script gen error: {e}")
            script_text = DEFAULT_SCRIPT
            status_log.append("Using default script (LLM unavailable)")
    
    # --- Step 2: Parse Script ---
    scenes = parse_script(script_text)
    if not scenes:
        status_log.append("ERROR: Failed to parse script.")
        return

    status_log.append(f"Parsed {len(scenes)} scenes successfully!")
    
    scene_images = []
    scene_audios = []

    for scene in scenes:
        sid = scene['id']
        status_log.append(f"Generating Scene {sid}/{len(scenes)}...")
        
        # --- DALL-E 3 Image ---
        image_dir = os.path.join(Config.OUTPUT_DIR, "images")
        visual_text = scene.get('visual', '')
        status_log.append(f"  Creating 3D visual (DALL-E 3)...")
        try:
            img_path = generate_ai_image(visual_text, sid, image_dir)
            scene_images.append(img_path)
            status_log.append(f"  Visual ready!")
        except Exception as e:
            safe_print(f"ERROR image scene {sid}: {e}")
            traceback.print_exc()
            scene_images.append(None)
            status_log.append(f"  Visual failed: {str(e)[:80]}")

        # --- Voiceover ---
        audio_path = os.path.join(Config.OUTPUT_DIR, "voiceovers", f"voice_{sid:02d}.mp3")
        narration_text = scene.get('narration', '')
        narration_text = re.sub(r'[*_#]', '', narration_text).strip()
        narration_text = narration_text.replace('\u201c', '').replace('\u201d', '').replace('"', '')
        
        if narration_text:
            status_log.append(f"  Generating voiceover...")
            try:
                await generate_voiceover(narration_text, audio_path)
                scene_audios.append(audio_path)
                status_log.append(f"  Voice ready!")
            except Exception as e:
                safe_print(f"ERROR voiceover scene {sid}: {e}")
                traceback.print_exc()
                scene_audios.append(None)
                status_log.append(f"  Voice failed: {str(e)[:80]}")
        else:
            scene_audios.append(None)

    # --- Step 3: Assemble Video (30s cap) ---
    status_log.append(f"Assembling {Config.VIDEO_DURATION}s video...")
    final_video = os.path.join(Config.OUTPUT_DIR, "video", "final_video.mp4")
    
    try:
        result = assemble_video(scene_images, scene_audios, final_video, Config.VIDEO_DURATION)
        if result and os.path.exists(result):
            file_size = os.path.getsize(result) / (1024 * 1024)
            status_log.append(f"Video ready! ({file_size:.1f} MB)")
        else:
            status_log.append("FAILED: Video assembly returned no output.")
            return
    except Exception as e:
        safe_print(f"ERROR assembling video: {e}")
        traceback.print_exc()
        status_log.append(f"FAILED during assembly: {str(e)[:100]}")
        return

    # --- Step 4: YouTube Upload ---
    if auto_upload:
        status_log.append("Uploading to YouTube...")
        try:
            title = "Sansad Reality Show - Election Season | Political Satire #shorts"
            description = (
                "Indian political satire comedy cartoon! "
                "Funny 3D animation of Modi, Rahul, Kejriwal in Parliament.\n\n"
                "#shorts #politicalsatire #indianpolitics #comedy #cartoon #modi #rahul "
                "#kejriwal #parliament #funnyshorts #3Danimation"
            )
            tags = [
                "shorts", "political satire", "indian politics", "comedy",
                "modi", "rahul gandhi", "kejriwal", "cartoon", "3d animation",
                "funny", "parliament", "election", "hindi comedy"
            ]
            
            upload_result = upload_to_youtube(final_video, title, description, tags)
            
            if "error" in upload_result:
                status_log.append(f"YouTube upload failed: {upload_result['error']}")
            else:
                video_url = upload_result.get("url", "")
                status_log.append(f"Uploaded to YouTube! URL: {video_url}")
        except Exception as e:
            safe_print(f"ERROR YouTube upload: {e}")
            traceback.print_exc()
            status_log.append(f"YouTube upload error: {str(e)[:100]}")
    
    status_log.append("Pipeline complete!")


# ================================================================
# ROUTES
# ================================================================

@app.get("/")
async def read_index():
    return FileResponse("src/static/index.html")

@app.get("/api/status")
async def get_status():
    return {"log": status_log[-15:]}

@app.post("/api/generate-script")
async def generate_script_endpoint(request: GenerateRequest):
    try:
        script = llm.generate(request.prompt)
        return {"script": script}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/render-video")
async def render_video(request: ScriptUpdate, background_tasks: BackgroundTasks):
    """Render video from provided script (no auto-upload)."""
    try:
        background_tasks.add_task(run_full_pipeline, request.script, False)
        return {"message": "Rendering started"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/render-and-upload")
async def render_and_upload(request: ScriptUpdate, background_tasks: BackgroundTasks):
    """Render video from script AND upload to YouTube."""
    try:
        background_tasks.add_task(run_full_pipeline, request.script, True)
        return {"message": "Rendering and upload started"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-generate")
async def auto_generate(background_tasks: BackgroundTasks):
    """Auto-generate script + render + upload (fully automated)."""
    try:
        background_tasks.add_task(run_full_pipeline, None, True)
        return {"message": "Auto-generation started (script + render + upload)"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
