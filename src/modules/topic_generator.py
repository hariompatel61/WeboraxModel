"""
Step 1: Topic Generator
Generates engaging animated story ideas with dynamic duration.
Themes: animals, robots+kids, comedy-tech, daily life comedy.
"""

import json
from modules.llm_client import LLMClient
from app_config import Config


class TopicGenerator:
    """Generates viral animated story topics with suggested duration and trending focus."""

    PROMPT_TEMPLATE = """You are a creative YouTube animation and Shorts content director specializing in virality.

We are pulling from CURRENT TRENDING DATA to generate {count} unique, high-retention story ideas.
The ideas must be suitable for animated videos between 30 seconds to 5 minutes long.

Current Trending Focus: {trending_focus}
Story themes to draw from: {categories}

IMPORTANT: Decide the ideal video duration based on complexity:
- Simple gags / quick pattern interrupts → 30-60 seconds
- Short story arcs with a twist → 60-180 seconds (1-3 minutes)
- Complex narratives with character development → 180-300 seconds (3-5 minutes)

For each idea, provide:
1. topic - The core concept or trending subject
2. title - A catchy, highly clickable, curiosity-driven title (max 10 words, e.g. "Nobody Talks About This...")
3. category - Which theme it fits
4. premise - 2-3 sentence engaging description of the story, focusing on the hook and payoff
5. humor_type - Type of humor or emotion (slapstick, irony, suspense, documentary, heartwarming)
6. keywords - Array of 3-5 SEO keywords
7. search_intent - Why would someone click this? (e.g., "curiosity", "entertainment", "educational")
8. viral_score - Rate 1-10 how shareable this idea is based on the trend
9. suggested_duration - Duration in seconds (30, 60, 90, 120, 180, 240, or 300)
10. characters - List of main character roles/types

Return ONLY valid JSON array. No markdown, no code blocks. Example format:
[
  {{
    "topic": "AI Taking Over Jobs",
    "title": "This Robot Just Replaced My Dad",
    "category": "futuristic technology",
    "premise": "A family buys a smart home assistant that slowly starts doing the dad's chores better than him. The dad tries to out-do the robot, causing massive destruction.",
    "humor_type": "irony",
    "keywords": ["AI", "Robot", "Comedy", "Smart Home"],
    "search_intent": "entertainment",
    "viral_score": 9,
    "suggested_duration": 120,
    "characters": ["Dad", "SmartBot", "Mom"]
  }}
]
"""

    def __init__(self):
        self.client = LLMClient()
        from modules.topic_history import TopicHistory
        self.history = TopicHistory()

    def _get_trending_focus(self):
        """Simulate pulling from trending sources to inject randomness and relevance."""
        trends = [
            "AI and the future of work", "Weird psychological space facts",
            "Unsolved internet mysteries", "Cryptocurrency crashes",
            "Animals reacting to magic", "Time travel paradoxes in everyday life",
            "Simulation theory glitches", "Ancient history but modernized"
        ]
        import random
        return random.choice(trends)

    def generate_topics(self, count=5):
        """Generate animated story topic ideas with suggested duration.

        Args:
            count: Number of topics to generate.

        Returns:
            list[dict]: List of topic dictionaries with suggested_duration.
        """
        categories = ", ".join(Config.TOPIC_CATEGORIES)
        trending_focus = self._get_trending_focus()
        
        prompt = self.PROMPT_TEMPLATE.format(
            count=count, 
            categories=categories,
            trending_focus=trending_focus
        )

        topics = self.client.generate_json(prompt)

        # Handle case where LLM returns a single dict instead of a list
        if isinstance(topics, dict):
            for key in ("topics", "ideas", "results"):
                if key in topics and isinstance(topics[key], list):
                    topics = topics[key]
                    break
            else:
                topics = [topics]

        # Handle string response fallback
        if isinstance(topics, str):
            import json
            try:
                topics = json.loads(topics)
            except (json.JSONDecodeError, ValueError):
                topics = [{
                    "topic": "Fallback Topic",
                    "title": topics[:50] if len(topics) > 5 else "The Unknown Phenomenon",
                    "category": "mystery",
                    "premise": topics,
                    "humor_type": "suspense",
                    "keywords": ["mystery"],
                    "search_intent": "curiosity",
                    "viral_score": 7,
                    "suggested_duration": 60,
                    "characters": ["Narrator"],
                }]

        recent_titles = self.history.get_recent_topics(100)
        valid_topics = []

        # Ensure schema completeness and history filtering
        for topic in topics:
            # Check history to prevent repeats
            if hasattr(self.history, 'is_duplicate') and self.history.is_duplicate(topic.get("title", "")):
                continue

            if "suggested_duration" not in topic:
                premise_len = len(topic.get("premise", ""))
                if premise_len > 150:
                    topic["suggested_duration"] = 180
                elif premise_len > 80:
                    topic["suggested_duration"] = 90
                else:
                    topic["suggested_duration"] = 60
            
            # Clamp to valid range
            topic["suggested_duration"] = max(
                Config.VIDEO_DURATION_MIN if hasattr(Config, 'VIDEO_DURATION_MIN') else 30,
                min(Config.VIDEO_DURATION_MAX if hasattr(Config, 'VIDEO_DURATION_MAX') else 300, topic["suggested_duration"])
            )
            
            # Ensure new keys exist fallback
            if "topic" not in topic: topic["topic"] = topic.get("title", "Unknown")
            if "keywords" not in topic: topic["keywords"] = [topic.get("category", "General")]

            valid_topics.append(topic)

        # Sort by viral_score descending
        valid_topics.sort(key=lambda t: t.get("viral_score", 0), reverse=True)
        
        # Fallback if all were duplicates
        if not valid_topics and topics:
            valid_topics = topics
            
        return valid_topics

    def pick_best_topic(self, topics=None):
        """Generate topics and return the best one.

        Args:
            topics: Optional pre-generated topics list.

        Returns:
            dict: The highest-rated topic.
        """
        if topics is None:
            topics = self.generate_topics()
        return topics[0]

    def generate_from_custom(self, custom_topic):
        """Structure a user-provided custom topic.

        Args:
            custom_topic: A string describing the topic.

        Returns:
            dict: Structured topic dictionary with suggested_duration.
        """
        prompt = f"""Take this animated video idea and structure it as JSON:
Topic: {custom_topic}

Return ONLY valid JSON (no markdown). Format:
{{
  "title": "Short catchy title",
  "category": "best fitting category",
  "premise": "2-3 sentence story description",
  "humor_type": "type of humor",
  "viral_score": 8,
  "suggested_duration": 120,
  "characters": ["Character1", "Character2"]
}}"""

        result = self.client.generate_json(prompt)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, ValueError):
                result = {
                    "title": custom_topic[:50],
                    "category": "comedy",
                    "premise": custom_topic,
                    "humor_type": "absurd",
                    "viral_score": 7,
                    "suggested_duration": 90,
                    "characters": ["Character1", "Character2"],
                }
        if "suggested_duration" not in result:
            result["suggested_duration"] = 90
        return result
