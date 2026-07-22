"""
Name:         button.py
Description:  Base class for a Button widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import BrowserEvent, ButtonStyle
from ...core.events import EventBinding
from ...core.node import Node
from ...core.signals import Signal
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class Button(Widget):

    _STYLE_TYPE = ButtonStyle
    _DEFAULT_STYLE = ButtonStyle.FILLED
    _CSS_CLASS = 'tz-button'

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
