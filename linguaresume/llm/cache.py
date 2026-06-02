"""In-memory and optional disk cache for LLM calls."""
import hashlib
import json
import os
from typing import Dict, Optional


class LLMCache:
    def __init__(self, disk_dir: Optional[str] = None):
        self._memory: Dict[str, str] = {}
        self._disk_dir = disk_dir
        if disk_dir:
            os.makedirs(disk_dir, exist_ok=True)

    def _key(self, payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, payload: str) -> Optional[str]:
        key = self._key(payload)
        if key in self._memory:
            return self._memory[key]
        if self._disk_dir:
            path = os.path.join(self._disk_dir, f"{key}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._memory[key] = data
                    return data
        return None

    def set(self, payload: str, value: str) -> None:
        key = self._key(payload)
        self._memory[key] = value
        if self._disk_dir:
            path = os.path.join(self._disk_dir, f"{key}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False)
