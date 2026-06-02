"""Abstract and concrete LLM clients."""
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

from linguaresume.llm.cache import LLMCache

logger = logging.getLogger("linguaresume")


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the LLM response string."""


class OllamaClient(LLMClient):
    def __init__(
        self,
        url: str,
        model: str,
        temperature: float = 0.3,
        timeout: int = 720,
        max_retries: int = 2,
        cache: Optional[LLMCache] = None,
    ):
        self.url = url
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache = cache or LLMCache()
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def complete(self, system: str, user: str) -> str:
        cache_payload = f"{self.model}:{self.temperature}:{system}:{user}"
        cached = self.cache.get(cache_payload)
        if cached is not None:
            return cached

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        last_error: Exception = RuntimeError("No LLM call attempted")
        for attempt in range(self.max_retries + 1):
            try:
                r = self._session.post(self.url, json=payload, timeout=self.timeout)
                r.raise_for_status()
                result = r.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                elif "message" in result:
                    content = result["message"]["content"]
                else:
                    raise RuntimeError(f"Unexpected LLM response format: {list(result.keys())}")
                self.cache.set(cache_payload, content)
                return content
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 1 * (attempt + 1)
                    logger.warning("⚠️ LLM call failed (attempt %d), retrying in %ds...", attempt + 1, wait)
                    time.sleep(wait)

        raise last_error


class OpenAIClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        timeout: int = 120,
        max_retries: int = 2,
        cache: Optional[LLMCache] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache = cache or LLMCache()
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        })

    def complete(self, system: str, user: str) -> str:
        cache_payload = f"{self.model}:{self.temperature}:{system}:{user}"
        cached = self.cache.get(cache_payload)
        if cached is not None:
            return cached

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
        }

        last_error: Exception = RuntimeError("No LLM call attempted")
        for attempt in range(self.max_retries + 1):
            try:
                r = self._session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                )
                r.raise_for_status()
                result = r.json()
                content = result["choices"][0]["message"]["content"]
                self.cache.set(cache_payload, content)
                return content
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 1 * (attempt + 1)
                    logger.warning("⚠️ LLM call failed (attempt %d), retrying in %ds...", attempt + 1, wait)
                    time.sleep(wait)

        raise last_error


class MockLLMClient(LLMClient):
    """Return canned responses for unit testing."""
    def __init__(self, responses: Optional[dict] = None):
        self.responses = responses or {}

    def complete(self, system: str, user: str) -> str:
        return self.responses.get(user, "<resume_middle>\n## Profile\n\nTest\n</resume_middle>")
