import json
from datetime import datetime
from typing import Any


class StatusLogger:
    def __init__(self, statuses_path: str, use_timestamps: bool = True):
        with open(statuses_path, "r", encoding="utf-8-sig") as f:
            self._statuses: dict[str, Any] = json.load(f)
        self.use_timestamps = use_timestamps

    def _get_text(self, section: str, key: str) -> str:
        node = self._statuses
        for part in f"{section}.{key}".split("."):
            if not isinstance(node, dict) or part not in node:
                return f"[missing status: {section}.{key}]"
            node = node[part]
        return str(node)

    def get(self, section: str, key: str, **kwargs: Any) -> str:
        text = self._get_text(section, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                text += f" [missing placeholder: {e}]"
        return text

    def get_event(self, section: str, key: str, **kwargs: Any) -> dict:
        """Возвращает словарь с percent и text для SSE-события."""
        node = self._statuses
        for part in f"{section}.{key}".split("."):
            if not isinstance(node, dict) or part not in node:
                return {"percent": 0, "text": f"[missing: {section}.{key}]"}
            node = node[part]
            
        # Если формат старый (просто строка), возвращаем дефолтный процент
        if isinstance(node, str):
            text = node.format(**kwargs) if kwargs else node
            return {"percent": 0, "text": text}

        # Новый формат: dict с полями percent и text
        percent = node.get("percent", 0)
        text = node.get("text", "")
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                text += f" [missing placeholder: {e}]"
                
        return {"percent": percent, "text": text}

    def log(self, section: str, key: str, **kwargs: Any) -> str:
        text = self.get(section, key, **kwargs)
        prefix = f"[{datetime.now().strftime('%H:%M:%S')}] " if self.use_timestamps else ""
        line = f"{prefix}{text}"
        print(line, flush=True)
        return line