"""
Name:         image.py
Description:  Base class for an Image widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import BrowserEvent, ImageStyle
from ...core.events import EventBinding
from ...core.node import Node
from ...core.signals import Signal
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class Image(Widget):

    _STYLE_TYPE = ImageStyle
    _DEFAULT_STYLE = ImageStyle.FIT
    _CSS_CLASS = 'tz-image'    
    _SUPPORTED_VARIANTS = ()

    def __init__(
        self, 
        source: str | None = None,
        alt: str = 'Image not found',
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.source = source
        self.alt = alt

    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='img',
            attributes={
                'src': self.source,
                'alt': self.alt,
            },
            classes=self._classes(),
            styles=self._styles(),
            events={},
        )
