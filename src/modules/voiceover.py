"""
Step 5: Voiceover Generator
Creates expressive voiceover audio using edge-tts with async batch processing.
"""

import asyncio
import os

import edge_tts

from app_config import Config


class VoiceoverGenerator:
    """Generate scene-level voiceovers using edge-tts."""

    TONE_ADJUSTMENTS = {
        "normal": {"pitch": "+0Hz", "rate": "+0%"},
        "neutral": {"pitch": "+0Hz", "rate": "+0%"},
        "informative": {"pitch": "-2Hz", "rate": "+5%"},
        "suspenseful": {"pitch": "-15Hz", "rate": "-15%"},
        "intense": {"pitch": "+10Hz", "rate": "+15%"},
        "dramatic": {"pitch": "-10Hz", "rate": "-5%"},
        "shocked": {"pitch": "+15Hz", "rate": "+20%"},
        "satisfying": {"pitch": "+2Hz", "rate": "-5%"},
        "direct": {"pitch": "-5Hz", "rate": "+10%"},
        "excited": {"pitch": "+20Hz", "rate": "+10%"},
        "angry": {"pitch": "-30Hz", "rate": "+15%"},
        "sad": {"pitch": "-20Hz", "rate": "-20%"},
        "scared": {"pitch": "+30Hz", "rate": "+5%"},
    }

    def __init__(self):
        self.voice_map = {
            "NARRATOR": Config.NARRATOR_VOICE,
            "male": Config.CHARACTER_VOICE_MALE,
            "female": Config.CHARACTER_VOICE_FEMALE,
        }
        self._ensure_event_loop()

    def _ensure_event_loop(self):
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

    def generate_scene_voiceover(self, scene, scene_index, output_dir, character_voices=None):
        """Generate voiceover audio for a single scene."""
        dialogue = self._normalize_dialogue(scene.get("dialogue", ""))
        if not dialogue:
            return None

        speaker = scene.get("speaker", "NARRATOR")
        tone = scene.get("tone", "normal")
        voice = self._get_voice(speaker, character_voices)
        adjustments = self.TONE_ADJUSTMENTS.get(tone, self.TONE_ADJUSTMENTS["normal"])

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"voice_{scene_index:02d}.mp3")
        asyncio.run(self._synthesize(dialogue, voice, adjustments, filepath))
        return filepath

    async def generate_all_voiceovers(self, storyboard, output_dir):
        """Generate voiceovers for all scenes using async batch synthesis."""
        all_characters = set()
        for scene in storyboard:
            for char in scene.get("characters_present", []):
                all_characters.add(char)

        character_voices = {}
        voice_options = [Config.CHARACTER_VOICE_MALE, Config.CHARACTER_VOICE_FEMALE]
        for i, char in enumerate(sorted(all_characters)):
            character_voices[char] = voice_options[i % len(voice_options)]

        voiceover_dir = os.path.join(output_dir, "voiceovers")
        os.makedirs(voiceover_dir, exist_ok=True)
        return await self._batch_synthesize(storyboard, voiceover_dir, character_voices)

    def generate_all_voiceovers_sync(self, storyboard, output_dir):
        """Synchronous wrapper for callers outside an event loop."""
        return asyncio.run(self.generate_all_voiceovers(storyboard, output_dir))

    async def _batch_synthesize(self, storyboard, voiceover_dir, character_voices):
        tasks = []
        paths = []

        for i, scene in enumerate(storyboard):
            dialogue = self._normalize_dialogue(scene.get("dialogue", ""))
            if not dialogue:
                paths.append(None)
                continue

            speaker = scene.get("speaker", "NARRATOR")
            tone = scene.get("tone", "normal")
            voice = self._get_voice(speaker, character_voices)
            adjustments = self.TONE_ADJUSTMENTS.get(tone, self.TONE_ADJUSTMENTS["normal"])
            filepath = os.path.join(voiceover_dir, f"voice_{i + 1:02d}.mp3")

            paths.append(filepath)
            tasks.append(self._synthesize(dialogue, voice, adjustments, filepath))

        if tasks:
            await asyncio.gather(*tasks)

        return paths

    def _get_voice(self, speaker, character_voices=None):
        if speaker == "NARRATOR":
            return self.voice_map["NARRATOR"]
        if character_voices and speaker in character_voices:
            return character_voices[speaker]
        return self.voice_map.get("male", Config.CHARACTER_VOICE_MALE)

    async def _synthesize(self, text, voice, adjustments, output_path):
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=adjustments.get("rate", "+0%"),
            pitch=adjustments.get("pitch", "+0Hz"),
        )
        await communicate.save(output_path)

    def generate_narration(self, full_text, output_path):
        """Generate a single narration audio from full script text."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        adjustments = self.TONE_ADJUSTMENTS["dramatic"]
        asyncio.run(self._synthesize(full_text, Config.NARRATOR_VOICE, adjustments, output_path))
        return output_path

    @staticmethod
    def _normalize_dialogue(dialogue):
        if isinstance(dialogue, list):
            return " ".join(str(part) for part in dialogue if part).strip()
        if isinstance(dialogue, str):
            return dialogue.strip()
        return ""
