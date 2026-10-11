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
from ...core.validation import Validator

# ______________________________________________________________________________________________________________________

class Image(Widget):

    _STYLE_TYPE = ImageStyle
    _DEFAULT_STYLE = ImageStyle.FIXED
    _CSS_CLASS = 'tz-image'    
    _STYLE_PREFIX = None
    _VARIANT_PREFIX = None
    _SUPPORTED_VARIANTS = ()

    source_changed = Signal(str | None)

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

    @property
    def source(self) -> str | None:
        return self._source

    @source.setter
    def source(self, source: str | None) -> None:
        source = Validator.ensure(source, str, None, attr_name='Image.source')
        old_source = getattr(self, '_source', None)
        self._source = source
        if old_source != source:
            self.source_changed.emit(source)

    @property
    def alt(self) -> str:
        return self._alt

    @alt.setter
    def alt(self, alt: str) -> None:
        self._alt = Validator.ensure(alt, str, attr_name='Image.alt')

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
