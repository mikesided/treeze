"""
Name:         container.py
Description:  Base class for a Container (abstract)

"""
# ______________________________________________________________________________________________________________________
# Imports
from abc import ABC, abstractmethod

from ...core.enums import InsertPosition
from ...core.exceptions import TreezeValueError
from ...core.node import Node
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class Container(Widget, ABC):

    _CHILDHOST = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._children: list[Widget] = []

    @property
    def children(self) -> tuple[Widget, ...]:
        return tuple(self._children)
    
    def add_widget(
            self, 
            widget: Widget, 
            position: InsertPosition = InsertPosition.LAST,
            index: int | None = None,
            ) -> None:
        """
        Adds a child widget to the container
        If index is specified, the position's InsertPosition is ignored
        """
        index = Validator.ensure(index, int, None)
        widget = Validator.ensure(widget, Widget)

        if index is None:
            if position == InsertPosition.FIRST:
                index = 0
            elif position == InsertPosition.LAST:
                index = len(self.children)

        self._children.insert(index, widget)
        widget._set_parent(self)

        if self._session is not None:
            widget._set_session(self._session)

        self._mark_dirty()

    def remove_widget(self, widget: Widget):
        """
        Removes a child widget from the container
        """
        Validator.ensure(widget, Widget)
        
        if widget not in self._children:
            raise TreezeValueError('widget is not a child of this container')

        self._children.remove(widget)
        widget._set_parent(None)
        self._mark_dirty()

    def _walk_widgets(self):
        yield self

        for child in self.children:
            yield from child._walk_widgets()
        
    @abstractmethod
    def _render(self) -> Node:
        raise NotImplementedError

    def _build_children(self, node: Node):
        """Builds children in the provided node"""
        for child in self.children:
            node.add_child(child._build())