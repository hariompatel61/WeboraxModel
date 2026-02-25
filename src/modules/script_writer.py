"""
Step 2: Script Writer
Generates comedy/animated scripts with dynamic duration scaling.
Supports 30-second shorts to 5-minute stories.
"""

import json
from modules.llm_client import LLMClient
from config import Config


class ScriptWriter:
    """Writes animated scripts scaled to dynamic video duration."""

    PROMPT_TEMPLATE = """You are an enterprise-grade AI YouTube Scriptwriter specializing in cinematic, high-retention documentaries.

Write a cinematic documentary script for this topic:
Title: {title}
Premise: {premise}
Tone: {tone} (Documentary, Storytelling, Suspense)
Target Duration: {duration} seconds

STRICT STRUCTURE & RETENTION RULES:
1. **HOOK** (pattern interrupt, curiosity gap): Start with a line that stops the scroll.
2. **OPEN LOOP**: Introduce a mystery or question.
3. **CONTEXT**: Briefly set the stage.
4. **STORY SEGMENTS**: Evidence-based or narrative escalation.
5. **ESCALATION**: Increase the stakes or tension.
6. **CLIMAX**: The peak moment of the story.
7. **RESOLUTION**: Tie up the narrative.
8. **CALL-TO-ACTION (CTA)**: A compelling request for viewer engagement.

STRICT FORMATTING:
- Total word count: {min_words}-{max_words} words.
- Tone must be cinematic: high-vocabulary, emotional pacing, zero filler.
- Include NARRATOR lines and occasional character dialogue if relevant.
- Include stage directions in parentheses for cinematic visual cues.

Return ONLY valid JSON (no markdown):
{{
  "hook": "The pattern interrupt first line",
  "segments": [
    {{"type": "hook", "line": "...", "speaker": "NARRATOR", "tone": "{tone}"}},
    {{"type": "open_loop", "line": "...", "speaker": "NARRATOR", "tone": "suspenseful"}},
    {{"type": "story", "line": "...", "speaker": "NARRATOR", "tone": "informative"}},
    {{"type": "escalation", "line": "...", "speaker": "NARRATOR", "tone": "dramatic"}},
    {{"type": "climax", "line": "...", "speaker": "NARRATOR", "tone": "intense"}},
    {{"type": "resolution", "line": "...", "speaker": "NARRATOR", "tone": "satisfying"}},
    {{"type": "cta", "line": "...", "speaker": "NARRATOR", "tone": "direct"}}
  ],
  "metadata": {{
    "total_word_count": {max_words},
    "retention_score_estimate": "90+"
  }}
}}
"""

    def __init__(self):
        self.client = LLMClient()

    def write_script(self, topic):
        """Generate a cinematic documentary script from a topic.

        Args:
            topic: dict with 'title', 'premise', 'suggested_duration'.

        Returns:
            dict: Structured script with hook, segments, metadata.
        """
        duration = topic.get("suggested_duration", Config.VIDEO_DURATION)
        settings = Config.get_duration_settings(duration)

        prompt = self.PROMPT_TEMPLATE.format(
            title=topic.get("title", "Cinematic Documentary"),
            premise=topic.get("premise", "An incredible true story"),
            tone=topic.get("tone", "documentary"),
            duration=settings["duration"],
            min_words=settings["min_words"],
            max_words=settings["max_words"],
        )

        script = self.client.generate_json(prompt)

        # Handle various response formats
        if isinstance(script, str):
            try:
                script = json.loads(script)
            except:
                script = {"hook": script[:100], "segments": [{"type": "story", "line": script, "speaker": "NARRATOR", "tone": "neutral"}]}

        # Normalize to 'script_lines' for backward compatibility with editor if needed
        if "segments" in script and "script_lines" not in script:
            script["script_lines"] = script["segments"]

        script["target_duration"] = settings["duration"]
        return script

    def get_full_text(self, script):
        """Get the full script as plain text for voiceover.

        Args:
            script: dict from write_script().

        Returns:
            str: Full script text.
        """
        lines = []
        for entry in script.get("script_lines", []):
            lines.append(entry.get("line", ""))
        return " ".join(lines)

    def get_dialogue_segments(self, script):
        """Get script broken into timed segments for voiceover.

        Args:
            script: dict from write_script().

        Returns:
            list[dict]: Each with 'speaker', 'line', 'tone'.
        """
        return script.get("script_lines", [])
