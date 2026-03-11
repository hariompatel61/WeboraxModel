"""
Step 8: SEO Metadata Generator
Generates viral titles, descriptions, tags, and hashtags using Gemini API.
"""

import json
from modules.llm_client import LLMClient
from app_config import Config


class SEOMetadataGenerator:
    """Generates SEO-optimized YouTube metadata for high retention Shorts and videos."""

    PROMPT_TEMPLATE = """You are a master YouTube SEO expert specialized in going viral.

Generate SEO-optimized metadata for this AI documentary video:

TOPIC / TRENDING FOCUS: {topic}
PREMISE: {premise}
SCRIPT HOOK: {hook}

Rules:
1. title - Must be highly clickable, curiosity-driven (e.g., "Nobody Talks About This... But It Changes Everything"). Max 60 characters. NO clickbait context that the video doesn't answer.
2. description - 150-200 words using "keyword clustering". Include long-tail keywords naturally. Add 5 high-reach hashtags at the end.
3. tags - 15-20 highly relevant long-tail and broad tags.
4. hashtags - Top 8 trending hashtags.

Return ONLY valid JSON (no markdown):
{{
  "title": "Your curiosity-driven cinematic title",
  "description": "Engaging, clustered description...",
  "tags": ["tag1", "tag2", "long tail tag"],
  "hashtags": ["#Cinematic", "#Documentary", "#Trending"]
}}
"""

    def __init__(self):
        self.client = LLMClient()

    def generate_metadata(self, topic, script):
        """Generate SEO metadata for the video.

        Args:
            topic: dict with 'topic', 'title', and 'premise'.
            script: dict with 'hook'.

        Returns:
            dict: With 'title', 'description', 'tags', 'hashtags'.
        """
        prompt = self.PROMPT_TEMPLATE.format(
            topic=topic.get("topic", topic.get("title", "Mystery History")),
            premise=topic.get("premise", "A gripping story"),
            hook=script.get("hook", "Wait for it..."),
        )

        metadata = self.client.generate_json(prompt)

        # Validate title length
        if len(metadata.get("title", "")) > 60:
            metadata["title"] = metadata["title"][:57] + "..."

        return metadata
