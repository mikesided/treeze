"""
    Name:         event.py
    Description:  Browser event bindings used by the render protocol

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum

from .enums import EventData

# ______________________________________________________________________________________________________________________


JsonValue = str | int | float | bool | None


@dataclass(slots=True)
class EventBinding:
    signal: str
    args: tuple[JsonValue, ...] = ()
    kwargs: dict[str, JsonValue] = field(default_factory=dict)
    data: tuple[EventData | str, ...] = ()

    def serialize(self) -> dict:
        return {
            'signal': self.signal,
            'args': list(self.args),
            'kwargs': self.kwargs,
            'data': [
                item.value if isinstance(item, EventData) else item
                for item in self.data
            ],
        }
        