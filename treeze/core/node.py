"""
Name:         node.py
Description:  A Node is a low level renderable element. It maps to something a browser can render

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from enum import StrEnum


from .events import EventBinding

# ______________________________________________________________________________________________________________________


JsonValue = str | int | float | bool | None

@dataclass(slots=True)
class Node():
    id: str
    tag: str

    text: str | None = None

    attributes: dict[str, JsonValue] = field(default_factory=dict)
    properties: dict[str, JsonValue] = field(default_factory=dict)

    classes: list[str] = field(default_factory=list)
    styles: dict[str, str] = field(default_factory=dict)
    events: dict[StrEnum, EventBinding] = field(default_factory=dict)

    children: list[Node] = field(default_factory=list)

    
    def add_child(self, child: Node) -> Node:
        """
        Add a child node.
        """
        self.children.append(child)
        return child



    def serialize(self) -> dict:
        """
        Convert the node tree into a JSON-compatible dictionary.
        """
        return {
            'id': self.id,
            'tag': self.tag,
            'text': self.text,
            'attributes': self.attributes,
            'properties': self.properties,
            'classes': self.classes,
            'styles': self.styles,
            'events': self._serialize_events(),
            'children': self._serialize_children(),
        }
    
    def _serialize_events(self) -> dict:
        return {
            browser_event.value: event.serialize()
            for browser_event, event in self.events.items()
        }
    
    def _serialize_children(self) -> list:
        return [
            child.serialize()
            for child in self.children
        ]