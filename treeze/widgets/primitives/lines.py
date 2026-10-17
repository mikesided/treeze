"""
Name:         label.py
Description:  Simple text label widget
"""
# ______________________________________________________________________________________________________________________
# Imports
from enum import StrEnum

from ...core.enums import LineStyle, Orientation, Variant
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________


class Line(Widget):
    """Simple widget that displays a straight line separator
    
    NOTE: 
    Use `background_color` (including gradients) or `color` to set the stroke.
    The line is drawn using its background, without a border.
    """

    _STYLE_TYPE = LineStyle
    _DEFAULT_STYLE = LineStyle.SOLID
    _CSS_CLASS = 'tz-line'
    _STYLE_PREFIX = None
    _VARIANT_PREFIX = None
    _SUPPORTED_VARIANTS = (
        Variant.PRIMARY,
        Variant.SECONDARY,
        Variant.TERTIARY,
        Variant.SUCCESS,
        Variant.WARNING,
        Variant.DANGER,
        Variant.INFO,
        Variant.MUTED,
        Variant.STRONG,
    )

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

    @property
    def orientation(self) -> Orientation:
        return self._orientation

    @orientation.setter
    def orientation(self, orientation: Orientation) -> None:
        self._orientation = Validator.ensure(orientation, Orientation, attr_name='Line.orientation')

    def _classes(self):
        classes = super()._classes()
        classes.append(f'tz-line-{self.orientation.value}')
        return classes

    def _styles(self):
        styles = super()._styles()
        if 'background-color' in styles:
            styles['background'] = styles.pop('background-color')
        if self.color is not None and self.background_color is None:
            styles.pop('color', None)
            styles['background'] = str(self.color)
        return styles

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
