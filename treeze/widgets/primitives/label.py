"""
Name:         label.py
Description:  Simple text label widget
"""
# ______________________________________________________________________________________________________________________
# Imports
from enum import StrEnum

from ...core.enums import LabelStyle, TextAlignment, Variant
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________


class Label(Widget):

    _CSS_CLASS = 'tz-label'
    _ALLOW_DISABLED = True
    _STYLE_TYPE = LabelStyle
    _DEFAULT_STYLE = LabelStyle.BODY
    _SUPPORTED_VARIANTS = (
        Variant.PRIMARY,
        Variant.SECONDARY,
        Variant.TERTIARY,
        Variant.SUCCESS,
        Variant.WARNING,
        Variant.DANGER,
        Variant.INFO,
        Variant.MUTED,
    )

    def __init__(
        self,
        text: str | None = None,
        *args,
        text_alignment: TextAlignment = TextAlignment.LEFT,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._text = Validator.ensure(text, str, None)
        self._text_alignment = text_alignment


    @property
    def text(self) -> str | None:
        return self._text

    @text.setter
    def text(self, text: str | None) -> None:
        self._text = Validator.ensure(text, str, None)

    @property
    def text_alignment(self) -> TextAlignment:
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, text_alignment: TextAlignment) -> None:
        self._text_alignment = Validator.ensure(text_alignment, TextAlignment)

    def _styles(self) -> dict[str, str]:
        styles = super()._styles()

        if self.text_alignment is not TextAlignment.LEFT:
            # Only add non-default values
            styles['text-align'] = self.text_alignment

        return styles

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='span',
            text=self.text,
            classes=self._classes(),
            styles=self._styles(),
        )
