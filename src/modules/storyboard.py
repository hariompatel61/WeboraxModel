"""
Step 3: Storyboard Creator
Breaks script into dynamically-scaled cartoon scenes with visual descriptions.
Supports 3–35 scenes based on video duration (30s–5min).
"""

import json
from modules.llm_client import LLMClient
from app_config import Config


class StoryboardCreator:
    """Creates scene-by-scene storyboard from an animated script with cinematic visual prompts."""

    PROMPT_TEMPLATE = """You are a master cinematic storyboard artist for high-end documentary-style YouTube videos.

Break this script into {min_scenes}-{max_scenes} cinematic scenes for a {duration}-second video.

SCRIPT:
{script_text}

For each scene provide:
1. scene_number (1-based)
2. visual_prompt - A rich, highly-detailed Midjourney/DALL-E style image prompt (e.g., "ultra cinematic, dramatic lighting, high contrast, 4k, depth of field...")
3. motion - (e.g., slow push-in, fast pan, vertigo effect, handheld shake, static cinematic)
4. duration_seconds - how long this scene lasts (total across all scenes must equal {duration}s)
5. text_overlay - Punchy, 2-4 word text to overlay on the screen for retention (e.g., "THE TRUTH", "SHOCKING REVELATION")
6. emotion - The dominant emotional tone of the scene (e.g., shocked, suspense, majestic, eerie)
7. dialogue - the spoken line(s) or narration for this scene
8. sfx - ambient sounds or transitions (e.g., deep drone, wind howl, glitch whoosh, low boom)

Return ONLY valid JSON array:
[
  {{
    "scene_number": 1,
    "visual_prompt": "ultra cinematic, dramatic lighting, high contrast, 4k, depth of field, wide shot of a futuristic city at sunset, neon reflections",
    "motion": "slow push-in",
    "duration_seconds": 4,
    "text_overlay": "THE FUTURE IS NOW",
    "emotion": "majestic",
    "dialogue": "Narration line here...",
    "speaker": "NARRATOR",
    "sfx": "deep cinematic drone"
  }}
]

ANTI-CARTOON RULES:
- Never use words like 'cartoon', 'animated', 'sketch'.
- Scenes must feel like a National Geographic or Netflix documentary.
- visual_prompts must be extremely detailed for accurate image generation.
"""

    def __init__(self):
        self.client = LLMClient()

    def create_storyboard(self, script, duration=None):
        """Generate storyboard scenes from a script with dynamic scene count.

        Args:
            script: dict from ScriptWriter with 'script_lines', 'characters',
                    and 'target_duration'.

        Returns:
            list[dict]: Scene-by-scene storyboard.
        """
        # Get dynamic duration from script (set by topic_generator)
        if isinstance(script, dict):
            resolved_duration = duration or script.get("target_duration", Config.VIDEO_DURATION)
            script_lines = script.get("script_lines", [])
            if script_lines:
                script_text = "\n".join(
                    f"{line.get('speaker', 'NARRATOR')}: {line.get('line', '')}"
                    for line in script_lines
                )
            else:
                script_text = script.get("hook", "A funny story")
        else:
            resolved_duration = duration or Config.VIDEO_DURATION
            script_text = str(script)

        settings = Config.get_duration_settings(resolved_duration)

        characters = []
        if isinstance(script, dict):
            characters = script.get("characters", [])

        prompt = self.PROMPT_TEMPLATE.format(
            min_scenes=settings["min_scenes"],
            max_scenes=settings["max_scenes"],
            duration=settings["duration"],
            script_text=script_text,
        )

        scenes = self.client.generate_json(prompt)

        # Handle various response formats
        if isinstance(scenes, dict):
            for key in ("scenes", "storyboard", "results"):
                if key in scenes and isinstance(scenes[key], list):
                    scenes = scenes[key]
                    break
            else:
                scenes = [scenes]

        if isinstance(scenes, str):
            try:
                scenes = json.loads(scenes)
            except:
                scenes = [{"scene_number": 1, "duration_seconds": resolved_duration, "shot_type": "Static Wide", "environment": scenes}]

        # Ensure scene_number exists
        for i, scene in enumerate(scenes):
            if "scene_number" not in scene:
                scene["scene_number"] = i + 1

        # Validate and fix total duration
        total = sum(s.get("duration_seconds", 0) for s in scenes)
        if total != settings["duration"] and scenes:
            diff = settings["duration"] - total
            scenes[-1]["duration_seconds"] = max(1, scenes[-1].get("duration_seconds", 4) + diff)

        return scenes
