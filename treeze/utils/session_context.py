"""
Name:         session_context.py
Description: Task-local session ownership during widget construction and callbacks

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..runtime.session import Session

# ______________________________________________________________________________________________________________________

_current_session: ContextVar[Session | None] = ContextVar('current_treeze_session', default=None)

def get_current_session() -> Session | None:
    return _current_session.get()

@contextmanager
def use_session(session: Session) -> Iterator[None]:
    token = _current_session.set(session)
    try:
        yield
    finally:
        _current_session.reset(token)
