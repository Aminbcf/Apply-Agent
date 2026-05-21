# Simple in-memory LRU cache for LLM prompts and conversation history
from collections import OrderedDict
from typing import Any, Dict, List, Tuple

class HistoryCache:
    """Cache recent conversation turns and generated responses.

    The cache stores a limited number of entries (default 20) and evicts the least
    recently used item when full. Each entry is a tuple ``(scenario, user_query)``
    mapping to the generated response. This allows the LLM layer to reuse recent
    results without recomputing them, improving latency when the model is idle.
    """

    def __init__(self, max_size: int = 20) -> None:
        self.max_size = max_size
        self._cache: "OrderedDict[Tuple[str, str], str]" = OrderedDict()

    def get(self, scenario: str, query: str) -> str | None:
        key = (scenario, query)
        if key in self._cache:
            # Move to end to mark as recently used
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, scenario: str, query: str, response: str) -> None:
        key = (scenario, query)
        self._cache[key] = response
        self._cache.move_to_end(key)
        if len(self._cache) > self.max_size:
            # pop the oldest item
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    def recent(self, count: int = 3) -> List[Tuple[str, str, str]]:
        """Return the most recent *count* cached entries as a list of
        ``(scenario, query, response)`` tuples."""
        return [(k[0], k[1], v) for k, v in list(self._cache.items())[-count:]]
