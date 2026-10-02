"""
Name:         label.py
Description:  Simple text label widget
"""
# ______________________________________________________________________________________________________________________
# Imports
from enum import StrEnum

from ...core.enums import LineStyle, Orientation
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________


class Line(Widget):
    """Simple widget that displays a straight line separator
    
    NOTE: 
    To alter the line color, both `color` and `border_color` can be used,
    although `color` will not render a gradient, while `border_color` will.
    """

    _CSS_CLASS = 'tz-line'
    _STYLE_TYPE = LineStyle
    _DEFAULT_STYLE = LineStyle.SOLID

    def __init__(
        self,
        orientation: Orientation = Orientation.HORIZONTAL,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.orientation = orientation
        self.margin = kwargs.get('margin', 0)
        self.padding = kwargs.get('padding', 0)

    def _classes(self):
        classes = super()._classes()
        classes.append(f'tz-line-{self.orientation.value}')
        return classes

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='hr',
            classes=self._classes(),
            styles=self._styles(),
        )


class HLine(Line):
    """Convenience wrapper for a horizontal line"""

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(orientation=Orientation.HORIZONTAL, *args, **kwargs)


class VLine(Line):
    """Convenience wrapper for a vertical line"""

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(orientation=Orientation.VERTICAL, *args, **kwargs)

