"""
Name:         protocol.py
Description:  Treeze client/server message protocol
"""

# ______________________________________________________________________________________________________________________
# Imports

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..core.validation import Validator

# ______________________________________________________________________________________________________________________


MessageType = Literal[
    'client.signal',
    'server.render',
    'server.patches',
    'server.dialog',
    'server.actions',
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
        Validator.ensure(payload, dict, attr_name='client.signal.payload')
        widget_id = Validator.ensure(payload.get('widget_id'), str, attr_name='client.signal.payload.widget_id')
        signal = Validator.ensure(payload.get('signal'), str, attr_name='client.signal.payload.signal')
        args = Validator.ensure(payload.get('args', ()), list, tuple, attr_name='client.signal.payload.args')
        kwargs = Validator.ensure(payload.get('kwargs'), dict, None, attr_name='client.signal.payload.kwargs')

        if kwargs is not None:
            for key in kwargs:
                Validator.ensure(key, str, attr_name=f'client.signal.payload.kwargs.keys[{key!r}]')
                
        return cls(
            widget_id=widget_id,
            signal=signal,
            args=tuple(args),
            kwargs=kwargs if kwargs is not None else {},
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
    actions: tuple[dict[str, Any], ...] = ()

    def to_protocol_message(self) -> ProtocolMessage:
        return ProtocolMessage(
            type='server.patches',
            payload={
                'patches': self.patches,
                'actions': list(self.actions),
            },
        )


@dataclass(frozen=True)
class ServerActionsMessage:
    actions: tuple[dict[str, Any], ...]

    def to_protocol_message(self) -> ProtocolMessage:
        return ProtocolMessage(type='server.actions', payload={'actions': list(self.actions)})


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
    
@dataclass(frozen=True)
class ServerCookieMessage:
    session_id: str
    operation_id: str

    def to_protocol_message(self) -> ProtocolMessage:
        return ProtocolMessage(
            type='server.cookie',
            payload={
                'session_id': self.session_id,
                'operation_id': self.operation_id,
            },
        )