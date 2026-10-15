"""
Name:         textfield.py
Description:  Base class for a Text Field widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import BrowserEvent, EchoMode, EventData, TextAlignment, TextFieldStyle, Variant
from ...core.events import EventBinding
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class TextField(Widget):
    """Input field (text), one-line."""

    _STYLE_TYPE = TextFieldStyle
    _DEFAULT_STYLE = TextFieldStyle.OUTLINED
    _CSS_CLASS = 'tz-textfield'
    _STYLE_PREFIX = None
    _VARIANT_PREFIX = None
    _ALLOW_DISABLED = True
    _SYNC_PROPERTY = 'value'
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

    text_changed = Signal(str)
    value_changed = Signal(str)
    editing_finished = Signal()
    submitted = Signal()
    def __init__(
        self, 
        text: str = '',
        *args, 
        placeholder_text: str | None = None,
        echo_mode: EchoMode = EchoMode.NORMAL,
        text_alignment: TextAlignment = TextAlignment.LEFT,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._text = ''
        self._placeholder_text = None
        self._echo_mode = EchoMode.NORMAL
        self._text_alignment = TextAlignment.LEFT

        self.text = text
        self.placeholder_text = placeholder_text
        self.echo_mode = echo_mode
        self.text_alignment = text_alignment


    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str | None) -> None:
        self._text = Validator.ensure(text, str, attr_name='TextField.text')
        
    @property
    def placeholder_text(self) -> str | None:
        return self._placeholder_text

    @placeholder_text.setter
    def placeholder_text(self, placeholder_text: str | None) -> None:
        self._placeholder_text = Validator.ensure(placeholder_text, str, None, attr_name='TextField.placeholder_text')

    @property
    def echo_mode(self) -> EchoMode:
        return self._echo_mode

    @echo_mode.setter
    def echo_mode(self, echo_mode: EchoMode) -> None:
        self._echo_mode = Validator.ensure(echo_mode, EchoMode, attr_name='TextField.echo_mode')

    @property
    def text_alignment(self) -> TextAlignment:
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, text_alignment: TextAlignment) -> None:
        self._text_alignment = Validator.ensure(text_alignment, TextAlignment, attr_name='TextField.text_alignment')

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='input',
            attributes={
                'type': 'password' if self.echo_mode == EchoMode.PASSWORD else 'text',
                'placeholder': self.placeholder_text,
                'disabled': not self.enabled,
            },
            properties={
                'value': self.text,
            },
            classes=self._classes(),
            styles={
                **self._styles(),
                'text-align': self.text_alignment,
            },
            events={
                BrowserEvent.INPUT: EventBinding(signal='text_changed', data=(EventData.VALUE,)),
                BrowserEvent.CHANGE: EventBinding(signal='value_changed', data=(EventData.VALUE,)),
                BrowserEvent.EDITING_FINISHED: EventBinding(signal='editing_finished'),
                BrowserEvent.RETURN_PRESSED: EventBinding(signal='submitted'),
            },
        )

    def _validate_sync_value(self, value):
        return Validator.ensure(value, str, attr_name='TextField synchronized value')

    def _apply_sync_value(self, value) -> None:
        self._text = value
