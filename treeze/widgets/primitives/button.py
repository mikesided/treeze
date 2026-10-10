"""
Name:         button.py
Description:  Base class for a Button widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import BrowserEvent, ButtonStyle, InsertPosition, Variant
from ...core.events import EventBinding
from ...core.node import Node
from ...core.types.size import Size
from ...core.signals import Signal
from ...core.validation import Validator

from ..bases.container import Container

from .label import Label
from .image import Image

# ______________________________________________________________________________________________________________________

class Button(Container):
    """
    Clickable button.
    Contains a Label and an optional Image (icon).

    NOTE: Label color is inherited from the button, unless specified as an attribute
    """

    _STYLE_TYPE = ButtonStyle
    _DEFAULT_STYLE = ButtonStyle.FILLED
    _CSS_CLASS = 'tz-button'
    _ALLOW_DISABLED = True
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
    def __init__(
        self, 
        text: str | None = None,
        icon: str | None = None,
        *args, 
        icon_position: InsertPosition = InsertPosition.FIRST,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._icon_position = icon_position
        self._label: Label = Label(parent=self)
        self._image: Image = Image(margin=(0, 5, 0, 5), parent=self)

        if text:
            self.text = text
        if icon:
            self.icon = icon


    @property
    def text(self) -> str | None:
        return self._label.text

    @text.setter
    def text(self, text: str | None) -> None:
        self.label.text = Validator.ensure(text, str, None)

    @property
    def icon(self) -> str | None:
        return self._image.source

    @icon.setter
    def icon(self, icon: str | None) -> None:
        self.image.source = icon

    @property
    def icon_position(self) -> InsertPosition:
        return self._icon_position

    @icon_position.setter
    def icon_position(self,  icon_position: InsertPosition) -> None:
        # Implementation in _render()
        self._icon = Validator.ensure(icon_position, InsertPosition)

    @property
    def label(self) -> Label:
        return self._label

    @property
    def image(self) -> Image:
        return self._image

    def _render(self) -> Node:
        node = Node(
            id=self.id,
            tag='button',
            attributes={
                'type': 'button',
            },
            classes=self._classes(),
            styles=self._styles(),
            events={
                BrowserEvent.CLICK: EventBinding(signal='clicked'),
            },
        )

        if self.enabled is False:
            node.attributes['disabled'] = True

        # Conditional node build
        if self.text:
            node.add_child(self.label._build())
        if self.icon:
            node.add_child(self.image._build(), insert_index=0 if self.icon_position == InsertPosition.FIRST else None)

        return node
