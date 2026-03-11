"""
Step 1: Topic Generator
Builds fresh topic ideas from recent live trend feeds.
Applies duplicate avoidance and dynamic duration suggestions.
"""

import html
import json
import random
import time
import xml.etree.ElementTree as ET

import requests

from app_config import Config
from modules.llm_client import LLMClient
from modules.topic_history import TopicHistory


class TopicGenerator:
    """Generate fresh topic ideas from live trend signals."""

    TREND_FEEDS = [
        "https://trends.google.com/trending/rss?geo=US",
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "https://www.reddit.com/r/popular/.rss",
    ]
    FEED_TIMEOUT = 10
    TREND_CACHE_SECONDS = 900
    MAX_TREND_TOPICS = 30
    MAX_RETRIES = 4

    PROMPT_TEMPLATE = """You are a creative YouTube Shorts and animation content director specializing in virality.

We are generating {count} unique, high-retention story ideas using LIVE RECENT TREND SIGNALS.
The ideas must be suitable for animated videos between 30 seconds and 5 minutes.

Primary Trend Focus: {primary_trend}

Recent Trend Signals:
{trend_signals}

Story categories to blend with these trends: {categories}

IMPORTANT:
- Base each idea on a recent public trend, headline, or cultural moment from the signals above
- Avoid stale evergreen topics unless they are clearly tied to a current trend
- Give each idea a different angle from the others
- Decide the ideal duration based on complexity:
  - Simple gag or quick interrupt -> 30-60 seconds
  - Short story arc with a twist -> 60-180 seconds
  - Bigger narrative -> 180-300 seconds

For each idea, provide:
1. topic
2. title
3. category
4. premise
5. humor_type
6. keywords
7. search_intent
8. viral_score
9. suggested_duration
10. characters

Return ONLY valid JSON array. No markdown.
"""

    def __init__(self):
        self.client = LLMClient()
        self.history = TopicHistory()
        self._trend_cache = []
        self._trend_cache_time = 0.0

    def _get_trending_topics(self):
        """Fetch and cache recent trend titles from live public feeds."""
        now = time.time()
        if self._trend_cache and (now - self._trend_cache_time) < self.TREND_CACHE_SECONDS:
            return list(self._trend_cache)

        topics = []
        seen = set()

        for feed_url in self.TREND_FEEDS:
            try:
                response = requests.get(
                    feed_url,
                    timeout=self.FEED_TIMEOUT,
                    headers={"User-Agent": "WeboraxTopicBot/1.0"},
                )
                response.raise_for_status()
                for title in self._parse_feed_titles(response.text):
                    key = self.history._normalize(title)
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    topics.append(title)
                    if len(topics) >= self.MAX_TREND_TOPICS:
                        break
            except Exception:
                continue
            if len(topics) >= self.MAX_TREND_TOPICS:
                break

        self._trend_cache = topics
        self._trend_cache_time = now
        return list(topics)

    def _parse_feed_titles(self, xml_text):
        """Parse RSS/Atom titles and clean noisy source suffixes."""
        titles = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return titles

        raw_titles = []
        raw_titles.extend(node.text or "" for node in root.findall(".//item/title"))
        raw_titles.extend(node.text or "" for node in root.findall(".//{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title"))

        for raw_title in raw_titles:
            title = html.unescape(raw_title).strip()
            if not title:
                continue

            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            if " | " in title:
                title = title.rsplit(" | ", 1)[0].strip()

            title = " ".join(title.split())
            if len(title) < 5:
                continue
            titles.append(title)

        return titles

    def _get_trending_focus(self):
        """Pick a fresh trend anchor from recent live topics."""
        live_topics = self._get_trending_topics()
        recent_focuses = {
            self.history._normalize(str(value))
            for value in self.history.get_recent_values("trending_focus", 10)
        }
        available = [
            topic for topic in live_topics
            if self.history._normalize(topic) not in recent_focuses
        ]

        if available:
            return random.choice(available)
        if live_topics:
            return random.choice(live_topics)
        return "current breaking headlines"

    def _build_trend_signals(self, primary_trend, limit=6):
        """Build a compact list of recent trend titles for the prompt."""
        live_topics = self._get_trending_topics()
        recent_focuses = {
            self.history._normalize(str(value))
            for value in self.history.get_recent_values("trending_focus", 12)
        }

        filtered = [
            topic for topic in live_topics
            if self.history._normalize(topic) not in recent_focuses
        ]

        if primary_trend in filtered:
            filtered.remove(primary_trend)

        random.shuffle(filtered)
        signals = [primary_trend] + filtered[: max(0, limit - 1)]
        return signals

    def _build_avoidance_section(self):
        """Build a prompt section telling the model what not to repeat."""
        recent_titles = self.history.get_recent_topics(15)
        recent_focuses = self.history.get_recent_values("trending_focus", 10)
        recent_seeds = self.history.get_recent_values("topic_seed", 10)
        sections = []

        if recent_titles:
            sections.append(
                "Do not repeat or lightly remix these recent topic titles:\n"
                + "\n".join(f"- {title}" for title in recent_titles[-10:])
            )

        if recent_focuses:
            sections.append(
                "Avoid using these recently used trend anchors again:\n"
                + "\n".join(f"- {focus}" for focus in recent_focuses[-8:])
            )

        if recent_seeds:
            sections.append(
                "Do not reuse these recent topic setups:\n"
                + "\n".join(f"- {seed}" for seed in recent_seeds[-8:])
            )

        return "\n\n".join(sections)

    def _coerce_topics(self, topics):
        """Normalize LLM output into a list of topic dictionaries."""
        if isinstance(topics, dict):
            for key in ("topics", "ideas", "results"):
                if key in topics and isinstance(topics[key], list):
                    return topics[key]
            return [topics]

        if isinstance(topics, str):
            try:
                topics = json.loads(topics)
            except (json.JSONDecodeError, ValueError):
                return [{
                    "topic": topics[:80] if len(topics) > 5 else "Current Trend Topic",
                    "title": topics[:50] if len(topics) > 5 else "Current Trend Twist",
                    "category": "trending",
                    "premise": topics,
                    "humor_type": "suspense",
                    "keywords": ["trend"],
                    "search_intent": "curiosity",
                    "viral_score": 7,
                    "suggested_duration": 60,
                    "characters": ["Narrator"],
                }]

        return topics if isinstance(topics, list) else []

    def _normalize_topic_record(self, topic, trending_focus):
        """Fill missing fields and attach trend metadata."""
        title = topic.get("title", topic.get("topic", "")).strip()
        premise = topic.get("premise", "")
        topic_name = topic.get("topic", title).strip() or title or "Unknown"

        if "suggested_duration" not in topic:
            if len(premise) > 150:
                topic["suggested_duration"] = 180
            elif len(premise) > 80:
                topic["suggested_duration"] = 90
            else:
                topic["suggested_duration"] = 60

        topic["suggested_duration"] = max(
            Config.VIDEO_DURATION_MIN if hasattr(Config, "VIDEO_DURATION_MIN") else 30,
            min(
                Config.VIDEO_DURATION_MAX if hasattr(Config, "VIDEO_DURATION_MAX") else 300,
                topic["suggested_duration"],
            ),
        )

        topic["topic"] = topic_name
        topic["title"] = title or topic_name
        topic["keywords"] = topic.get("keywords") or [topic.get("category", "General")]
        topic["trending_focus"] = trending_focus
        topic["topic_seed"] = topic_name
        return topic

    def _filter_unique_topics(self, topics, trending_focus):
        """Filter out repeated topics and return the best unique set."""
        valid_topics = []
        seen_titles = set()

        for raw_topic in topics:
            topic = self._normalize_topic_record(raw_topic, trending_focus)
            title = topic.get("title", "")
            topic_name = topic.get("topic", "")
            title_key = self.history._normalize(title)

            if not title_key or title_key in seen_titles:
                continue
            if self.history.is_duplicate(title, threshold=0.5):
                continue
            if self.history.is_similar_to_recent(topic_name, field="topic_seed", threshold=0.55, limit=30):
                continue

            valid_topics.append(topic)
            seen_titles.add(title_key)

        valid_topics.sort(key=lambda item: item.get("viral_score", 0), reverse=True)
        return valid_topics

    def generate_topics(self, count=5):
        """Generate animated story topic ideas from recent live trends."""
        categories = ", ".join(Config.TOPIC_CATEGORIES)
        avoidance_section = self._build_avoidance_section()
        attempted_focuses = set()

        for _ in range(self.MAX_RETRIES):
            trending_focus = self._get_trending_focus()
            if trending_focus in attempted_focuses:
                continue
            attempted_focuses.add(trending_focus)

            trend_signals = self._build_trend_signals(trending_focus)
            signal_block = "\n".join(f"- {signal}" for signal in trend_signals)
            prompt = self.PROMPT_TEMPLATE.format(
                count=count,
                primary_trend=trending_focus,
                trend_signals=signal_block,
                categories=categories,
            )

            if avoidance_section:
                prompt += (
                    f"\n\nSTRICT UNIQUENESS RULES:\n{avoidance_section}"
                    "\n\nEach returned idea must explore a clearly different recent trend angle."
                )

            topics = self._coerce_topics(self.client.generate_json(prompt))
            valid_topics = self._filter_unique_topics(topics, trending_focus)
            if valid_topics:
                return valid_topics

        fallback_focus = self._get_trending_focus()
        return [{
            "topic": fallback_focus,
            "title": f"{fallback_focus[:50]} Twist",
            "category": "trending",
            "premise": f"A fresh animated take on the recent trend: {fallback_focus}.",
            "humor_type": "suspense",
            "keywords": [fallback_focus, "trend", "viral"],
            "search_intent": "curiosity",
            "viral_score": 7,
            "suggested_duration": 60,
            "characters": ["Narrator"],
            "trending_focus": fallback_focus,
            "topic_seed": fallback_focus,
        }]

    def pick_best_topic(self, topics=None):
        """Generate topics and return the best one."""
        if topics is None:
            topics = self.generate_topics()
        return topics[0]

    def generate_from_custom(self, custom_topic):
        """Structure a user-provided custom topic with a fresh angle."""
        avoidance_section = self._build_avoidance_section()
        live_trend_context = self._build_trend_signals(self._get_trending_focus(), limit=4)

        prompt = f"""Take this video idea and structure it as JSON:
Topic: {custom_topic}

Recent live trend context:
{chr(10).join(f"- {topic}" for topic in live_trend_context)}

Return ONLY valid JSON (no markdown). Format:
{{
  "title": "Short catchy title",
  "category": "best fitting category",
  "premise": "2-3 sentence story description",
  "humor_type": "type of humor",
  "viral_score": 8,
  "suggested_duration": 120,
  "characters": ["Character1", "Character2"]
}}

RULES:
- Create a fresh title and sub-angle, not just a restatement of the prompt
- Tie the idea loosely to the recent trend context when useful
- Avoid recent topic/title overlap
"""

        if avoidance_section:
            prompt += f"\n\nSTRICT UNIQUENESS RULES:\n{avoidance_section}"

        for _ in range(4):
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
            if "topic" not in result:
                result["topic"] = custom_topic

            result["topic_seed"] = result.get("topic", custom_topic)
            result["trending_focus"] = live_trend_context[0] if live_trend_context else "current breaking headlines"

            if not self.history.is_duplicate(result.get("title", ""), threshold=0.5):
                return result

            prompt += "\n\nRetry with a noticeably different title, premise, and sub-angle."

        return {
            "title": f"{custom_topic[:35]} Twist",
            "category": "comedy",
            "premise": custom_topic,
            "humor_type": "absurd",
            "viral_score": 7,
            "suggested_duration": 90,
            "characters": ["Character1", "Character2"],
            "topic": custom_topic,
            "topic_seed": custom_topic,
            "trending_focus": live_trend_context[0] if live_trend_context else "current breaking headlines",
        }
