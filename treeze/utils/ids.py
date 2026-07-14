"""
Name:         ids.py
Description: Short internal ID generation for Treeze runtime objects.
"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from itertools import count
from collections.abc import Iterator

# ______________________________________________________________________________________________________________________


class IdScope:

    def __init__(self):
        self._widget_counter = count(1)

    def create_widget_id(self) -> str:
        return f'w{next(self._widget_counter)}'

_default_id_scope = IdScope()

_current_id_scope: ContextVar[IdScope | None] = ContextVar(
    'current_treeze_id_scope',
    default=None,
)

def create_id_scope() -> IdScope:
    return IdScope()

@contextmanager
def use_id_scope(scope: IdScope) -> Iterator[None]:
    token = _current_id_scope.set(scope)

    try:
        yield
    finally:
        _current_id_scope.reset(token)

def create_widget_id() -> str:
    scope = _current_id_scope.get()

    if scope is None:
        scope = _default_id_scope

    return scope.create_widget_id()