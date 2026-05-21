from pathlib import Path
from collections import OrderedDict
import json

class HistoryCache:
    """In‑memory LRU cache for conversation history.

    Stores the last *cache_size* entries (default from settings). Each entry is a JSON
    object containing ``session_id`` and a list of ``messages`` (each message is a
    dict with ``role`` and ``content``). When a session becomes idle the ``summarise_idle``
    method can be called to generate a one‑sentence summary (stub implementation).
    """

    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self.cache: OrderedDict[str, dict] = OrderedDict()

    def _evict_if_needed(self):
        while len(self.cache) > self.max_size:
            # pop the oldest entry
            self.cache.popitem(last=False)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        entry = self.cache.get(session_id)
        if entry is None:
            entry = {"session_id": session_id, "messages": []}
            self.cache[session_id] = entry
        entry["messages"].append({"role": role, "content": content})
        self._evict_if_needed()

    def get_history(self, session_id: str) -> list[dict]:
        entry = self.cache.get(session_id)
        if entry:
            return entry["messages"]
        return []

    def get_messages(self, session_id: str) -> list[dict]:
        """Alias for :meth:`get_history` used by :class:`JobMatchService`."""
        return self.get_history(session_id)

    def clear(self, session_id: str) -> None:
        """Remove all cached messages for *session_id*.

        Called by :class:`JobMatchService` when a job offer is rejected so the
        RAG context is reset for the next evaluation attempt.
        """
        self.cache.pop(session_id, None)

    def summarise_idle(self, session_id: str) -> str:
        """Generate a one‑sentence summary for idle periods.

        In a real implementation this would call the LLM with the recent history.
        Here we return a simple placeholder.
        """
        messages = self.get_history(session_id)
        if not messages:
            return ""
        # Very naive summary: join the last two user messages
        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
        summary = " ".join(user_msgs[-2:])
        return summary[:200]

