"""
Name:         protocol.py
Description:  Treeze client/server message protocol
"""

# ______________________________________________________________________________________________________________________
# Imports

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# ______________________________________________________________________________________________________________________


MessageType = Literal[
    'client.signal',
    'server.render',
    'server.patches',
    'server.dialog',
]


@dataclass(frozen=True)
class ProtocolMessage:
    type: MessageType
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            'type': self.type,
            'payload': self.payload,
        }


@dataclass(frozen=True)
class ClientSignalMessage:
    widget_id: str
    signal: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ClientSignalMessage:
        return cls(
            widget_id=payload['widget_id'],
            signal=payload['signal'],
            args=tuple(payload.get('args', ())),
            kwargs=payload.get('kwargs') or {},
        )


@dataclass(frozen=True)
class ServerRenderMessage:
    root: dict[str, Any]

    def to_protocol_message(self) -> ProtocolMessage:
        return ProtocolMessage(
            type='server.render',
            payload={
                'root': self.root,
            },
        )


@dataclass(frozen=True)
class ServerPatchesMessage:
    patches: list[dict[str, Any]]

    def to_protocol_message(self) -> ProtocolMessage:
        return ProtocolMessage(
            type='server.patches',
            payload={
                'patches': self.patches,
            },
        )


@dataclass(frozen=True)
class ServerDialogMessage:
    level: Literal['info', 'warning', 'error']
    title: str
    message: str
    details: str | None = None

    def to_protocol_message(self) -> ProtocolMessage:
        payload: dict[str, Any] = {
            'level': self.level,
            'title': self.title,
            'message': self.message,
        }

        if self.details is not None:
            payload['details'] = self.details

        return ProtocolMessage(
            type='server.dialog',
            payload=payload,
        )