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

from ..bases.layout import Layout

from ...core.exceptions import TreezeRuntimeError, TreezeValueError
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

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

    _SUPPORTED_VARIANTS = ()
    _CSS_CLASS = 'tz-window'
    _STYLE_PREFIX = None
    _VARIANT_PREFIX = None

    layout_changed = Signal(Widget | None, Widget | None)
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
        self._layout: Layout | None = None

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
        layout = Validator.ensure(layout, Layout, None, attr_name='Window.layout')

        if layout is self._layout:
            return

        if layout is not None:
            layout.unparent()

        if self._layout is not None:
            self._layout._set_parent(None)

        self._layout = layout

        if self._layout is not None:
            self._layout._set_parent(self)
            
            if self._session is not None:
                layout._set_session(self._session)

    # ==========================================================================
    #  Private
    # ==========================================================================

    def _remove_widget(self, widget: Widget) -> None:
        """Detach the window's root layout through the common parent removal API."""
        old_layout = self.layout
        Validator.ensure(widget, Widget, attr_name='Window._remove_widget(widget=...)')
        if widget is not self._layout:
            raise TreezeValueError("Window._remove_widget(widget=...): widget is not this window's layout.")

        self.layout = None
        widget._set_parent(None)

        if old_layout != self.layout:
            self.layout_changed.emit(old_layout, self.layout)
            self._mark_dirty()

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
