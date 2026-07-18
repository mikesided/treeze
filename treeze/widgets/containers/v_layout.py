"""
Name:         v_layout.py
Description:  Base class for a Layout (abstract)

"""
# ______________________________________________________________________________________________________________________
# Imports
from abc import ABC, abstractmethod

from ..bases.layout import Layout

from ...core.enums import Orientation
from ...core.node import Node

# ______________________________________________________________________________________________________________________

class VLayout(Layout, ABC):

    _CSS_CLASS = 'tz-vertical-layout'
    _ORIENTATION = Orientation.VERTICAL
    def _render(self) -> Node:
        node = Node(
            id=self.id,
            tag='div',
            classes=[
                'tz-vertical-layout'
            ],
            styles=self._styles()
        )

        self._build_children(node)

        return node