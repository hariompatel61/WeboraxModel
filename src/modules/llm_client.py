"""
LLM Client: Unified interface for LLM inference.
Supports multiple providers:
  1. Bytez (125+ models, cloud SDK) — DEFAULT
  2. Groq (free, ultra-fast, cloud)
  3. Ollama (free, local)
  4. Google Gemini (free tier)

OPTIMIZED: Connection pooling, Bytez SDK, faster retries.
"""

import json
import os
import re
import time
import requests
from app_config import Config


# Module-level session for connection pooling (for non-SDK providers)
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})


class LLMClient:
    """Client for generating text using LLM APIs (Bytez/Groq/Ollama/Gemini)."""

    MAX_RETRIES = 3
    DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
    JSON_SYSTEM_PROMPT = (
        "You are a helpful assistant that always responds with valid JSON when asked for JSON output. "
        "Never wrap JSON in markdown code blocks."
    )

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.model = Config.get_active_model()
        self.session = _session

        if self.provider == "bytez":
            from bytez import Bytez
            self._sdk = Bytez(Config.BYTEZ_API_KEY)
        elif self.provider == "groq":
            self.api_key = Config.GROQ_API_KEY
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.provider == "ollama":
            self.base_url = Config.OLLAMA_URL
        elif self.provider == "gemini":
            self.api_key = Config.GEMINI_API_KEY
            self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate(self, prompt):
        """Generate text from a prompt.

        Args:
            prompt: The text prompt to send to the model.

        Returns:
            str: The generated text response.
        """
        if self.provider == "bytez":
            return self._generate_bytez(prompt)
        elif self.provider == "groq":
            return self._generate_groq(prompt)
        elif self.provider == "ollama":
            return self._generate_ollama(prompt)
        elif self.provider == "gemini":
            return self._generate_gemini(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _generate_bytez(self, prompt, _retry_count=0, system_prompt=None):
        """Generate text using Bytez Python SDK (125+ models)."""
        try:
            if system_prompt is None:
                system_prompt = self.DEFAULT_SYSTEM_PROMPT
            model = self._sdk.model(self.model)
            results = model.run([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ])

            if results.error:
                # If Bytez key is invalid/unauthorized, fall back to Gemini (if configured)
                err_text = str(results.error)
                err_lower = err_text.lower()
                if (
                    ("unauthorized" in err_lower or "forbidden" in err_lower or "invalid api key" in err_lower)
                    and Config.GEMINI_API_KEY
                ):
                    print(f"   ⚠️  Bytez auth error. Falling back to Gemini ({Config.GEMINI_MODEL}) for this request.")
                    return self._generate_gemini_direct(prompt)
                # If Bytez is rate-limited, fall back to Gemini (if configured) instead of failing the whole run.
                if ("rate limit" in err_lower or "rate limited" in err_lower or "too many requests" in err_lower) and Config.GEMINI_API_KEY:
                    print(f"   ⚠️  Bytez rate limited. Falling back to Gemini ({Config.GEMINI_MODEL}) for this request.")
                    return self._generate_gemini_direct(prompt, system_prompt=system_prompt)
                if _retry_count < 3:
                    wait = 3 * (_retry_count + 1)
                    print(f"   ⏳ Bytez error, retrying in {wait}s... ({results.error})")
                    time.sleep(wait)
                    return self._generate_bytez(prompt, _retry_count + 1, system_prompt=system_prompt)
                raise RuntimeError(f"Bytez error: {results.error}")

            # Extract text content from the response
            output = results.output
            if isinstance(output, dict):
                content = output.get("content", "")
            elif isinstance(output, str):
                content = output
            else:
                content = str(output)

            # Strip <think>...</think> reasoning tags (Qwen3 models include these)
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

            return content

        except Exception as e:
            if "RuntimeError" in str(type(e)):
                raise
            # Same fallback for exception paths mentioning unauthorized/invalid key
            if Config.GEMINI_API_KEY and any(s in str(e).lower() for s in ["unauthorized", "forbidden", "invalid api key", "invalid key"]):
                print(f"   ⚠️  Bytez auth error. Falling back to Gemini ({Config.GEMINI_MODEL}) for this request.")
                return self._generate_gemini_direct(prompt, system_prompt=system_prompt)
            raise RuntimeError(f"Bytez error: {e}")

    def _generate_gemini_direct(self, prompt, _retry_count=0, system_prompt=None):
        """Generate using Gemini without needing provider='gemini' initialization."""
        api_key = Config.GEMINI_API_KEY
        model = Config.GEMINI_MODEL
        if not api_key:
            raise RuntimeError("Gemini fallback requested but GEMINI_API_KEY is not set")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": (f"{system_prompt}\n\n{prompt}" if system_prompt else prompt)}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            },
        }
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except requests.HTTPError as e:
            if response.status_code == 429 and _retry_count < 3:
                wait_time = 5 * (_retry_count + 1)
                print(f"   ⏳ Gemini rate limited, waiting {wait_time}s... (retry {_retry_count + 1}/3)")
                time.sleep(wait_time)
                return self._generate_gemini_direct(prompt, _retry_count + 1)
            raise RuntimeError(f"Gemini fallback error: {e} ({getattr(response, 'text', '')[:200]})")
        except Exception as e:
            raise RuntimeError(f"Gemini fallback error: {e}")

    def _generate_groq(self, prompt):
        """Generate text using Groq API (free, ultra-fast)."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        try:
            response = self.session.post(
                self.base_url, json=payload, timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.HTTPError as e:
            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", "3"))
                print(f"   ⏳ Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                return self._generate_groq(prompt)
            raise RuntimeError(f"Groq API error {response.status_code}: {e}")
        except Exception as e:
            raise RuntimeError(f"Groq error: {e}")

    def _generate_ollama(self, prompt):
        """Generate text using Ollama (local, no limits)."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048,
            },
        }
        try:
            response = self.session.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (start it with 'ollama serve')."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")

    def _generate_gemini(self, prompt, _retry_count=0):
        """Generate using Google Gemini free API with rate-limit retry."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            },
        }
        url = f"{self.base_url}?key={self.api_key}"
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except requests.HTTPError as e:
            if response.status_code == 429 and _retry_count < 3:
                wait_time = 5 * (_retry_count + 1)
                print(f"   ⏳ Gemini rate limited, waiting {wait_time}s... (retry {_retry_count + 1}/3)")
                time.sleep(wait_time)
                return self._generate_gemini(prompt, _retry_count + 1)
            raise RuntimeError(f"Gemini error: {e}")
        except Exception as e:
            raise RuntimeError(f"Gemini error: {e}")

    def generate_json(self, prompt):
        """Generate text and parse as JSON, with retries.

        Args:
            prompt: The text prompt expecting JSON output.

        Returns:
            dict or list: Parsed JSON response.
        """
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                if self.provider == "bytez":
                    raw = self._generate_bytez(prompt, system_prompt=self.JSON_SYSTEM_PROMPT)
                else:
                    # Force JSON via prompt + system instructions where possible
                    raw = self.generate(self.JSON_SYSTEM_PROMPT + "\n\n" + prompt)
                cleaned = self._clean_json(raw)
                result = json.loads(cleaned)

                # Unwrap nested JSON strings (model may return '\"{ ... }\"')
                for _ in range(3):
                    if isinstance(result, str):
                        try:
                            result = json.loads(result)
                        except (json.JSONDecodeError, ValueError):
                            # Try cleaning again in case of embedded JSON
                            inner = self._clean_json(result)
                            try:
                                result = json.loads(inner)
                            except (json.JSONDecodeError, ValueError):
                                break
                    else:
                        break

                return result
            except json.JSONDecodeError as e:
                last_error = e
                print(f"   ⚠️  JSON parse error (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying...")
                try:
                    repaired = self._repair_json(cleaned)
                    return json.loads(repaired)
                except (json.JSONDecodeError, Exception):
                    time.sleep(0.5)
                    continue

        raise ValueError(
            f"Failed to get valid JSON after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    @staticmethod
    def _clean_json(text):
        """Strip markdown code fences and extract JSON from LLM response."""
        text = text.strip()
        # Remove markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        # Strip any remaining <think> tags that weren't caught earlier
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        # Try to find JSON — prefer OBJECTS over arrays (objects are more common for structured output)
        # Also prefer the LARGEST valid JSON candidate
        best = None
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                candidate = text[start : end + 1]
                # Only accept if it's larger than what we already found
                if best and len(candidate) <= len(best):
                    continue
                try:
                    json.loads(candidate)
                    best = candidate
                except json.JSONDecodeError:
                    try:
                        decoder = json.JSONDecoder()
                        obj, idx = decoder.raw_decode(candidate)
                        best = json.dumps(obj, ensure_ascii=False)
                    except json.JSONDecodeError:
                        if not best:
                            best = candidate
        return best if best else text

    @staticmethod
    def _repair_json(text):
        """Attempt to repair common JSON issues from LLM output."""
        text = re.sub(r',\s*([\]}])', r'\1', text)
        text = text.replace("'", '"')
        text = re.sub(r'[\x00-\x1f\x7f]', ' ', text)
        text = re.sub(r'}\s*{', '},{', text)
        for start_c, end_c in [('{', '}'), ('[', ']')]:
            s = text.find(start_c)
            e = text.rfind(end_c)
            if s != -1 and e != -1 and e > s:
                return text[s:e+1]
        return text

    @staticmethod
    def check_connection():
        """Check if the configured LLM provider is accessible.

        Returns:
            tuple: (bool, str) — (is_connected, message)
        """
        provider = Config.LLM_PROVIDER

        if provider == "bytez":
            if Config.BYTEZ_API_KEY and Config.BYTEZ_API_KEY != "YOUR_BYTEZ_API_KEY_HERE":
                return True, f"Bytez SDK configured, model: {Config.BYTEZ_MODEL}"
            return False, "BYTEZ_API_KEY not set in .env"

        elif provider == "groq":
            try:
                headers = {
                    "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                }
                r = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers=headers,
                    timeout=10,
                )
                if r.status_code == 200:
                    models = [m["id"] for m in r.json().get("data", [])]
                    return True, f"Groq connected. Models: {', '.join(models[:5])}"
                return False, f"Groq returned status {r.status_code}"
            except Exception as e:
                return False, f"Cannot connect to Groq: {e}"

        elif provider == "ollama":
            try:
                r = requests.get(f"{Config.OLLAMA_URL}/api/tags", timeout=5)
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models", [])]
                    if models:
                        return True, f"Ollama running with models: {', '.join(models)}"
                    return True, "Ollama running but no models. Run: ollama pull gemma2:2b"
                return False, f"Ollama returned status {r.status_code}"
            except Exception:
                return False, "Ollama is not running. Start with: ollama serve"

        elif provider == "gemini":
            if Config.GEMINI_API_KEY:
                return True, "Gemini API key configured"
            return False, "GEMINI_API_KEY not set"

        return False, f"Unknown provider: {provider}"
