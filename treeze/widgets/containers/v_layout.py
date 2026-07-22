"""
Name:         v_layout.py
Description:  Vertical layout

"""
# ______________________________________________________________________________________________________________________
# Imports
from abc import ABC, abstractmethod

from ..bases.layout import Layout

from ...core.enums import Orientation, LayoutStyle
from ...core.node import Node

# ______________________________________________________________________________________________________________________

class VLayout(Layout, ABC):

    _CSS_CLASS = 'tz-layout-vertical'
    _STYLE_TYPE = LayoutStyle
    _DEFAULT_STYLE = LayoutStyle.PLAIN
    _STYLE_PREFIX = 'tz-layout'
    _VARIANT_PREFIX = 'tz-layout'
    _ORIENTATION = Orientation.VERTICAL

    def _styles(self) -> dict[str, str]:
        styles = super()._styles()
        styles.update({
            'justify-content': self.vertical_alignment.value,
            'align-items': self.horizontal_alignment.value,
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