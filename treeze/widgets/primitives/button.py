"""
Name:         button.py
Description:  Base class for a Button widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import BrowserEvent, EventData, Variant
from ...core.events import EventBinding
from ...core.node import Node
from ...core.signals import Signal
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class Button(Widget):

    _CSS_CLASS = 'tz-button'
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

    clicked = Signal()
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='button',
            text=self.text,
            attributes={
                'type': 'button',
            },
            classes=self._classes(),
            styles=self._styles(),
            events={
                BrowserEvent.CLICK: EventBinding(signal='clicked'),
            },
        )
