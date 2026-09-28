"""
Name:         label.py
Description:  Simple text label widget
"""
# ______________________________________________________________________________________________________________________
# Imports
from enum import StrEnum

from ...core.enums import LabelStyle
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________


class Label(Widget):

    _CSS_CLASS = 'tz-label'
    _STYLE_TYPE = LabelStyle
    _DEFAULT_STYLE = LabelStyle.BODY

    def __init__(
        self,
        text: str = '',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._text = Validator.ensure(text, str)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = Validator.ensure(text, str)

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='span',
            text=self.text,
            classes=self._classes(),
            styles=self._styles(),
        )
