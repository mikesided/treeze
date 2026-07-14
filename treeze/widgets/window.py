"""
Name:         window.py
Description:  Base class for a Window widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from .layout import Layout

from ..core.exceptions import TreezeRuntimeError
from ..core.node import Node
from ..core.validation import Validator
from ..core.widget import Widget

# ______________________________________________________________________________________________________________________

_WINDOW_CONSTRUCTION_ALLOWED: ContextVar[bool] = ContextVar(
    '_WINDOW_CONSTRUCTION_ALLOWED',
    default=False,
)


@contextmanager
def _allow_window_construction() -> Iterator[None]:
    token = _WINDOW_CONSTRUCTION_ALLOWED.set(True)
    try:
        yield
    finally:
        _WINDOW_CONSTRUCTION_ALLOWED.reset(token)
        
# ______________________________________________________________________________________________________________________

class Window(Widget):

    _CSS_CLASS = 'tz-window'
    def __init__(
            self,
            layout: Layout | None = None,
            *args, 
            **kwargs
        ):
        if not _WINDOW_CONSTRUCTION_ALLOWED.get():
            raise TreezeRuntimeError(
                'Window classes cannot be instantiated directly. '
                'Assign the Window class to App.window and call app.run().'
            )
        super().__init__(*args, **kwargs)
        self._layout: Layout = None

        self.layout = layout

    # ==========================================================================
    #  Properties
    # ==========================================================================

    @property
    def layout(self) -> Layout | None:
        """The window's main layout."""
        return self._layout

    @layout.setter
    def layout(self, layout: Layout | None):
        layout = Validator.ensure(layout, Layout, None)

        if self._layout is not None:
            self._layout._set_parent(None)

        self._layout = layout

        if self._layout is not None:
            self._layout._set_parent(self)

    # ==========================================================================
    #  Private
    # ==========================================================================

    def _walk_widgets(self):
        yield self

        if self.layout is not None:
            yield from self.layout._walk_widgets()

    # ==========================================================================
    #  Rendering
    # ==========================================================================

    def _render(self) -> Node:
        node = Node(
            id=self.id,
            tag='div',
            classes=self._classes(),
            styles=self._styles(),
        )

        if self.layout is not None:
            node.add_child(self.layout._build())

        return node
