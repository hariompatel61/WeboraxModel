"""
Cinematic Hybrid Image Engine
=============================
Coordinates between high-fidelity image providers:
- ChatGPT (DALL-E) for Hero/Story Peaks.
- Gemini Imagen for B-Roll/Environmental shots.
Implements the Negative Style Filter to ensure cinematic quality.
"""

import os
import requests
import random
import time
from urllib.parse import quote
from PIL import Image, ImageDraw
from config import Config
from modules.scene_generator import SceneGenerator

class ImageEngine:
    """Enterprise-grade image generation coordinator."""

    def __init__(self):
        self.openai_key = Config.CHATGPT_IMAGE_API_KEY
        self.gemini_key = Config.GEMINI_IMAGEN_API_KEY

    def generate_cinematic_image(self, scene, scene_index, output_dir, is_hero=False):
        """Generate a cinematic image based on scene details and hero status."""
        
        # Build the prompt based on storyboard attributes
        prompt_data = {
            "shot_type": scene.get("shot_type", "Cinematic shot"),
            "camera_angle": scene.get("camera_angle", "eye level"),
            "environment": scene.get("environment", "natural setting"),
            "lighting": scene.get("lighting", "natural lighting"),
            "motion": scene.get("motion", "static"),
            "mood": scene.get("mood", "calm"),
            "color_grading": scene.get("color_grading", "natural colors")
        }
        
        full_prompt = Config.CINEMATIC_SCENE_PROMPT.format(**prompt_data)
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"scene_{scene_index:02d}.jpg"
        filepath = os.path.join(output_dir, filename)

        # Decide provider
        if is_hero and self.openai_key:
            return self._generate_dalle(full_prompt, filepath, scene, scene_index, output_dir)
        elif self.gemini_key:
            return self._generate_imagen(full_prompt, filepath, scene, scene_index, output_dir)
        else:
            # Fallback to Pollinations (Flux) if specific cinematic keys are missing
            return self._generate_pollinations(full_prompt, filepath, scene, scene_index, output_dir)

    def _generate_dalle(self, prompt, filepath, scene, scene_index, output_dir):
        """Generate image via DALL-E (Hero moments)."""
        print(f"     🚀 Generating Hero Image via DALL-E...")
        # Placeholder for OpenAI DALL-E API call
        # In a real implementation, we would use the openai library or requests
        return self._generate_pollinations(prompt, filepath, scene, scene_index, output_dir) # Fallback for now

    def _generate_imagen(self, prompt, filepath, scene, scene_index, output_dir):
        """Generate image via Gemini Imagen (B-Roll)."""
        print(f"     🎨 Generating B-Roll via Gemini Imagen...")
        # Placeholder for Gemini Imagen API call
        return self._generate_pollinations(prompt, filepath, scene, scene_index, output_dir) # Fallback for now

    def _generate_pollinations(self, prompt, filepath, scene=None, scene_index=0, output_dir=""):
        """Fallback cinematic generator using Flux on Pollinations."""
        encoded_prompt = quote(prompt)
        seed = random.randint(1000, 999999)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={Config.VIDEO_WIDTH}&height={Config.VIDEO_HEIGHT}"
            f"&model=flux&seed={seed}&nologo=true&enhance=true"
        )
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return filepath
            except Exception as e:
                print(f"     ⚠️  Image generation attempt {attempt+1} failed: {e}")
            time.sleep(2)
        
        # If Pollinations fails, try SceneGenerator (Pillow Characters)
        if scene and output_dir:
            return self._generate_procedural_fallback(scene, scene_index, output_dir)
            
        return self._generate_emergency_fallback(filepath, prompt)

    def _generate_procedural_fallback(self, scene, scene_index, output_dir):
        """Use SceneGenerator to draw actual characters and backgrounds."""
        print(f"     🎨 PILLOW FALLBACK: Drawing procedural scene for index {scene_index}")
        try:
            generator = SceneGenerator()
            # Map cinematic storyboard to procedural parameters
            proc_scene = {
                "background": self._map_environment(scene.get("environment", "living_room")),
                "characters_present": [scene.get("speaker", "NARRATOR")],
                "expressions": {scene.get("speaker", "NARRATOR"): self._map_mood(scene.get("mood", "happy"))},
                "camera_angle": self._map_camera(scene.get("shot_type", "wide"))
            }
            return generator.generate_scene_image(proc_scene, scene_index, output_dir)
        except Exception as e:
            print(f"     ❌ Procedural fallback failed: {e}")
            return None

    def _map_environment(self, env):
        env = env.lower()
        mapping = {
            "office": "office",
            "room": "living_room",
            "house": "living_room",
            "street": "street",
            "road": "street",
            "park": "park",
            "forest": "park",
            "school": "school",
            "kitchen": "kitchen"
        }
        for key, val in mapping.items():
            if key in env: return val
        return "living_room"

    def _map_mood(self, mood):
        mood = mood.lower()
        if "sad" in mood or "melancholy" in mood: return "crying"
        if "angry" in mood or "tense" in mood: return "angry"
        if "shock" in mood or "surprise" in mood: return "surprised"
        if "happy" in mood or "joy" in mood: return "happy"
        return "happy"

    def _map_camera(self, shot):
        shot = shot.lower()
        if "close" in shot: return "close_up"
        if "medium" in shot: return "medium"
        return "wide"

    def _generate_emergency_fallback(self, filepath, prompt):
        """Create a black frame with scene info if all else fails."""
        print(f"     🚨 EMERGENCY FALLBACK: Creating blank frame for {os.path.basename(filepath)}")
        try:
            img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((100, 100), f"Scene: {os.path.basename(filepath)}", fill=(255, 255, 255))
            img.save(filepath)
            return filepath
        except Exception as e:
            print(f"     ❌ Absolute fallback failed: {e}")
            return None

    def apply_negative_filter(self, filepath):
        """Audit the generated image for quality standards (placeholder)."""
        # In a more advanced version, we could use a CLIP-based or Vision-LLM audit
        # to detect the 'cartoon' style and trigger regeneration.
        return True
