"""
Step 2: Script Writer
Generates comedy/animated scripts with dynamic duration scaling.
Supports 30-second shorts to 5-minute stories.
"""

import json
import random
from modules.llm_client import LLMClient
from app_config import Config
from modules.topic_history import TopicHistory


class ScriptWriter:
    """Writes highly engaging, cinematic scripts scaled to dynamic video duration."""

    PROMPT_TEMPLATE = """You are an elite YouTube Shorts/Video Scriptwriter with millions of subscribers.
Your goal is max retention, emotional engagement, and extreme curiosity.

Write a script for this trending topic:
Topic: {topic}
Title: {title}
Premise: {premise}
Target Duration: {duration} seconds (approx. {min_words}-{max_words} words)

Selected Style: {script_style}
Tone: {tone} (Documentary, Storytelling, Suspense)

STRICT HIGH-RETENTION STRUCTURE:
1. **HOOK** (0–5s): Pattern interrupt! Start with a shocking fact, crazy visual, or a question that demands an answer.
2. **OPEN LOOP**: Introduce the core mystery—make them stay to find out what happens.
3. **STORY/CONTEXT**: Quick context, no filler. Use emotional triggers (shock, awe, humor).
4. **ESCALATION/CLIMAX**: Stakes go up. Peak tension.
5. **RESOLUTION & CTA**: Fast wrap-up and a strong Call-To-Action (subscribe, comment).

STRICT FORMATTING FORMAT:
- Avoid repetitive sentence structures.
- Use sharp, punchy phrases. 
- Tone must be cinematic: high-vocabulary, emotional pacing, ZERO filler.
- Include stage directions in parentheses for visual cues.

Return ONLY valid JSON (no markdown):
{{
  "hook": "The pattern interrupt first line that hooks the viewer",
  "segments": [
    {{"type": "hook", "line": "...", "speaker": "NARRATOR", "tone": "intense"}},
    {{"type": "open_loop", "line": "...", "speaker": "NARRATOR", "tone": "suspenseful"}},
    {{"type": "story", "line": "...", "speaker": "NARRATOR", "tone": "informative"}},
    {{"type": "escalation", "line": "...", "speaker": "NARRATOR", "tone": "dramatic"}},
    {{"type": "climax", "line": "...", "speaker": "NARRATOR", "tone": "shocked"}},
    {{"type": "resolution", "line": "...", "speaker": "NARRATOR", "tone": "satisfying"}},
    {{"type": "cta", "line": "...", "speaker": "NARRATOR", "tone": "direct"}}
  ],
  "metadata": {{
    "total_word_count": {max_words},
    "retention_score_estimate": "95+"
  }}
}}
"""

    def __init__(self):
        self.client = LLMClient()
        self.history = TopicHistory()

    def _get_random_style(self, exclude=None):
        """Pick a unique narrative style randomly."""
        styles = [
            "storytelling (immersive, emotional narrative)",
            "shocking facts (rapid-fire mind-blowing info)",
            "list format (top 3 countdown to a crazy twist)",
            "mystery (unfolding a bizarre secret slowly)",
            "documentary (serious cinematic deep-dive)"
        ]
        available = [style for style in styles if style not in (exclude or [])]
        return random.choice(available or styles)

    def _build_uniqueness_section(self):
        recent_topics = self.history.get_recent_topics(10)
        recent_hooks = self.history.get_recent_values("hook", 10)
        recent_styles = self.history.get_recent_values("style", 6)
        parts = []

        if recent_topics:
            parts.append(
                "Do not repeat these recent titles or subject lines:\n"
                + "\n".join(f"- {title}" for title in recent_topics)
            )
        if recent_hooks:
            parts.append(
                "Do not echo these recent opening hooks:\n"
                + "\n".join(f"- {hook}" for hook in recent_hooks)
            )
        if recent_styles:
            parts.append(
                "Prefer a different storytelling flavor from these recent styles:\n"
                + "\n".join(f"- {style}" for style in recent_styles)
            )

        return "\n\n".join(parts)

    def _build_signature(self, script):
        text = self.get_full_text(script)
        return " ".join(text.lower().split())

    def write_script(self, topic):
        """Generate a cinematic documentary script from a topic.

        Args:
            topic: dict with 'topic', 'title', 'premise', 'suggested_duration'.

        Returns:
            dict: Structured script with hook, segments, metadata.
        """
        duration = topic.get("suggested_duration", Config.VIDEO_DURATION)
        settings = Config.get_duration_settings(duration)
        uniqueness_section = self._build_uniqueness_section()
        tried_styles = []
        last_error = None

        for _ in range(4):
            script_style = self._get_random_style(exclude=tried_styles)
            tried_styles.append(script_style)

            prompt = self.PROMPT_TEMPLATE.format(
                topic=topic.get("topic", "Trending Mystery"),
                title=topic.get("title", "Cinematic Documentary"),
                premise=topic.get("premise", "An incredible true story"),
                tone=topic.get("humor_type", topic.get("tone", "suspenseful")),
                duration=settings["duration"],
                min_words=settings["min_words"],
                max_words=settings["max_words"],
                script_style=script_style,
            )

            if uniqueness_section:
                prompt += f"\n\nSTRICT UNIQUENESS RULES:\n{uniqueness_section}\n\nThe hook, escalation, and ending must all feel materially different from the recent scripts above."

            try:
                script = self.client.generate_json(prompt)

                if isinstance(script, str):
                    try:
                        script = json.loads(script)
                    except Exception:
                        script = {
                            "hook": script[:100],
                            "segments": [
                                {"type": "hook", "line": script[:100], "speaker": "NARRATOR", "tone": "intense"},
                                {"type": "story", "line": script, "speaker": "NARRATOR", "tone": "neutral"},
                            ],
                        }

                if "segments" in script and "script_lines" not in script:
                    script["script_lines"] = script["segments"]

                script["target_duration"] = settings["duration"]
                script["applied_style"] = script_style

                for line in script.get("script_lines", []):
                    if "..." in line["line"] and "<break" not in line["line"]:
                        line["line"] = line["line"].replace("...", ' <break time="0.5s"/> ')

                hook = script.get("hook", "")
                signature = self._build_signature(script)

                if self.history.is_similar_to_recent(hook, field="hook", threshold=0.52, limit=25):
                    raise ValueError("Generated hook is too similar to a recent script.")
                if self.history.is_similar_to_recent(signature, field="script_signature", threshold=0.65, limit=25):
                    raise ValueError("Generated script body is too similar to a recent script.")

                self.history.add_topic(
                    title=topic.get("title", topic.get("topic", "Untitled")),
                    angle=topic.get("category", ""),
                    extra={
                        "hook": hook,
                        "style": script_style,
                        "topic_seed": topic.get("topic_seed", topic.get("topic", "")),
                        "trending_focus": topic.get("trending_focus", ""),
                        "script_signature": signature,
                    },
                )
                return script
            except Exception as exc:
                last_error = exc

        raise RuntimeError(f"Unable to generate a fresh script after multiple attempts: {last_error}")

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
