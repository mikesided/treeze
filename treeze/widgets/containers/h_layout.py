"""
Name:         h_layout.py
Description:  Horizontal Layout

"""
# ______________________________________________________________________________________________________________________
# Imports
from abc import ABC, abstractmethod

from ..bases.layout import Layout

from ...core.enums import Orientation
from ...core.node import Node

# ______________________________________________________________________________________________________________________

class HLayout(Layout, ABC):

    _CSS_CLASS = 'tz-horizontal-layout'
    _ORIENTATION = Orientation.HORIZONTAL

    def _styles(self) -> dict[str, str]:
        styles = super()._styles()
        styles.update({
            'align-items': self.vertical_alignment.value,
            'justify-content': self.horizontal_alignment.value,
        })
            
        return styles
    
    def _render(self) -> Node:
        node = Node(
            id=self.id,
            tag='div',
            classes=self._classes(),
            styles=self._styles(),
        )

        self._build_children(node)

        return node