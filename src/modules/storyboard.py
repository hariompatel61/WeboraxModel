"""
Step 3: Storyboard Creator
Breaks script into dynamically-scaled cartoon scenes with visual descriptions.
Supports 3–35 scenes based on video duration (30s–5min).
"""

import json
from modules.llm_client import LLMClient
from config import Config


class StoryboardCreator:
    """Creates scene-by-scene storyboard from an animated script."""

    PROMPT_TEMPLATE = """You are a cinematic storyboard artist for high-end documentary-style YouTube videos.

Break this script into {min_scenes}-{max_scenes} cinematic scenes for a {duration}-second video.

SCRIPT:
{script_text}

For each scene provide:
1. scene_number (1-based)
2. duration_seconds - how long this scene lasts (total must reach {duration}s)
3. shot_type - (e.g., Wide cinematic drone shot, Tight close-up, Medium tracking shot)
4. camera_angle - (e.g., low angle, high angle, Dutch angle, eye level)
5. motion - (e.g., slow push-in, fast pan, vertigo effect, handheld shake, static cinematic)
6. environment - (e.g., abandoned factory at dusk, busy Tokyo street, deep ocean trench)
7. lighting - (e.g., volumetric lighting, golden hour, moody low-key, harsh street lights)
8. mood - (e.g., suspenseful, majestic, melancholy, intense)
9. color_grading - (e.g., teal and orange, washed out vintage, high contrast noir)
10. depth_of_field - (e.g., shallow focus, deep focus, rack focus)
11. dialogue - the spoken line(s) or narration for this scene
12. sfx - ambient sounds or transitions (e.g., deep drone, wind howl, glitch whoosh)

Return ONLY valid JSON array:
[
  {{
    "scene_number": 1,
    "duration_seconds": 5,
    "shot_type": "Wide cinematic drone shot",
    "camera_angle": "high angle",
    "motion": "slow push-in",
    "environment": "futuristic city at sunset",
    "lighting": "volumetric lighting",
    "mood": "majestic",
    "color_grading": "teal and orange",
    "depth_of_field": "deep focus",
    "dialogue": "Narration line here...",
    "speaker": "NARRATOR",
    "sfx": "deep cinematic drone"
  }}
]

ANTI-CARTOON RULES:
- Never use words like 'cartoon', 'animated', 'sketch'.
- Scenes must feel like a National Geographic or Netflix documentary.
- Descriptions must be ultra-realistic and visceral.
"""

    def __init__(self):
        self.client = LLMClient()

    def create_storyboard(self, script):
        """Generate storyboard scenes from a script with dynamic scene count.

        Args:
            script: dict from ScriptWriter with 'script_lines', 'characters',
                    and 'target_duration'.

        Returns:
            list[dict]: Scene-by-scene storyboard.
        """
        # Get dynamic duration from script (set by topic_generator)
        duration = script.get("target_duration", Config.VIDEO_DURATION)
        settings = Config.get_duration_settings(duration)

        # Build full script text
        script_lines = script.get("script_lines", [])
        if script_lines:
            script_text = "\n".join(
                f"{line.get('speaker', 'NARRATOR')}: {line.get('line', '')}"
                for line in script_lines
            )
        else:
            script_text = script.get("hook", "A funny story")

        characters = ", ".join(script.get("characters", ["Character1", "Character2"]))

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
                scenes = [{"scene_number": 1, "duration_seconds": duration, "shot_type": "Static Wide", "environment": scenes}]

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
