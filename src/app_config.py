import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ---- LLM Settings ----
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bytez")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    BYTEZ_API_KEY = os.getenv("BYTEZ_API_KEY", "")
    BYTEZ_MODEL = os.getenv("BYTEZ_MODEL", "Qwen/Qwen3-4B")

    @classmethod
    def get_active_model(cls):
        if cls.LLM_PROVIDER == "ollama":
            return cls.OLLAMA_MODEL
        elif cls.LLM_PROVIDER == "groq":
            return cls.GROQ_MODEL
        elif cls.LLM_PROVIDER == "gemini":
            return cls.GEMINI_MODEL
        elif cls.LLM_PROVIDER == "bytez":
            return cls.BYTEZ_MODEL
        return cls.OLLAMA_MODEL

    # ---- Paths ----
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
    IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
    AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
    VIDEO_DIR = os.path.join(OUTPUT_DIR, "video")
    SCRIPT_DIR = os.path.join(OUTPUT_DIR, "scripts")
    VOICEOVER_DIR = os.path.join(OUTPUT_DIR, "voiceovers")
    LOG_DIR = os.path.join(OUTPUT_DIR, "logs")
    MUSIC_DIR = os.path.join(OUTPUT_DIR, "music")
    SFX_DIR = os.path.join(OUTPUT_DIR, "sfx")
    THUMBNAIL_PATH = os.path.join(OUTPUT_DIR, "thumbnail.png")

    # ---- Video Settings ----
    VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
    VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", "24"))
    VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", "30"))
    VIDEO_DURATION_MIN = int(os.getenv("VIDEO_DURATION_MIN", "30"))
    VIDEO_DURATION_MAX = int(os.getenv("VIDEO_DURATION_MAX", "300"))

    # ---- Voice Settings (edge-tts) ----
    NARRATOR_VOICE = os.getenv("NARRATOR_VOICE", "en-US-GuyNeural")
    CHARACTER_VOICE_MALE = os.getenv("CHARACTER_VOICE_MALE", "en-US-ChristopherNeural")
    CHARACTER_VOICE_FEMALE = os.getenv("CHARACTER_VOICE_FEMALE", "en-US-JennyNeural")

    # ---- Image Generation ----
    CHATGPT_IMAGE_API_KEY = os.getenv("CHATGPT_IMAGE_API_KEY", "")
    GEMINI_IMAGEN_API_KEY = os.getenv("GEMINI_IMAGEN_API_KEY", "")
    AIMLAPI_KEY = os.getenv("AIMLAPI_KEY", "")
    POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "flux")

    # ---- YouTube Upload ----
    YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "Client_secret.json")
    YOUTUBE_CATEGORY = os.getenv("YOUTUBE_CATEGORY", "24")
    MADE_FOR_KIDS = os.getenv("MADE_FOR_KIDS", "false").lower() == "true"
    PLAYLIST_ID = os.getenv("PLAYLIST_ID", "")
    SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "")

    # ---- Trending & Virality ----
    TRENDING_SOURCES = ["youtube", "google_trends", "reddit", "twitter"]
    VIRALITY_THRESHOLD = int(os.getenv("VIRALITY_THRESHOLD", "8"))
    TOPIC_CATEGORIES = [
        "creepy mysteries", "mind-bending science", "bizarre history",
        "futuristic technology", "untold true crime", "internet rabbit holes"
    ]

    @classmethod
    def get_duration_settings(cls, duration):
        """Return normalized script and storyboard settings for a target duration."""
        duration = int(max(cls.VIDEO_DURATION_MIN, min(cls.VIDEO_DURATION_MAX, duration)))

        if duration <= 60:
            return {
                "duration": duration,
                "min_words": 70,
                "max_words": 110,
                "min_scenes": 4,
                "max_scenes": 6,
            }
        if duration <= 120:
            return {
                "duration": duration,
                "min_words": 120,
                "max_words": 180,
                "min_scenes": 6,
                "max_scenes": 10,
            }
        if duration <= 180:
            return {
                "duration": duration,
                "min_words": 180,
                "max_words": 260,
                "min_scenes": 8,
                "max_scenes": 14,
            }
        return {
            "duration": duration,
            "min_words": 260,
            "max_words": 420,
            "min_scenes": 10,
            "max_scenes": 18,
        }

    @classmethod
    def ensure_directories(cls):
        for path in [
            cls.OUTPUT_DIR,
            cls.IMAGE_DIR,
            cls.AUDIO_DIR,
            cls.VIDEO_DIR,
            cls.SCRIPT_DIR,
            cls.VOICEOVER_DIR,
            cls.LOG_DIR,
            cls.MUSIC_DIR,
            cls.SFX_DIR,
        ]:
            os.makedirs(path, exist_ok=True)
