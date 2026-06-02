"""Simple in-process memory store. Can be swapped for Redis/vector DB later."""

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    role: str  # "user" | "assistant" | "system"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Memory:
    """
    Keeps a sliding window of conversation turns and a flat key-value store
    for facts the agent should remember across calls.
    """

    def __init__(self, max_turns: int = 20):
        self._turns: deque[MemoryEntry] = deque(maxlen=max_turns)
        self._facts: dict[str, Any] = {}

    def add(self, role: str, content: str, **metadata: Any) -> None:
        self._turns.append(MemoryEntry(role=role, content=content, metadata=metadata))

    def remember(self, key: str, value: Any) -> None:
        self._facts[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        return self._facts.get(key, default)

    def to_messages(self) -> list[dict[str, str]]:
        return [{"role": e.role, "content": e.content} for e in self._turns]

    def clear(self) -> None:
        self._turns.clear()
        self._facts.clear()
