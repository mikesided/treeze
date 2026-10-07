"""
Name:         card.py
Description:  Base class for a Card widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import BrowserEvent, CardStyle, Variant
from ...core.events import EventBinding
from ...core.node import Node
from ...core.signals import Signal
from ...core.validation import Validator
from ...core.widget import Widget

from ..bases.container import Container
from ..containers.h_layout import HLayout
from ..containers.v_layout import VLayout
from ..primitives.lines import HLine

# ______________________________________________________________________________________________________________________

class Card(VLayout):

    _STYLE_TYPE = CardStyle
    _DEFAULT_STYLE = CardStyle.FLAT
    _CSS_CLASS = 'tz-card'

    clicked = Signal()
    def __init__(
        self, 
        header: Container | None = None,
        body: Container | None = None,
        footer: Container | None = None,
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        # Init widgets
        self._upper_separator = HLine(variant=Variant.STRONG)
        self._lower_separator = HLine(variant=Variant.STRONG)
        self._header = Validator.ensure(header, Container, None) or HLayout()
        self._body = Validator.ensure(body, Container, None) or VLayout()
        self._footer = Validator.ensure(footer, Container, None) or HLayout()

        # Add Composite classes
        self.upper_separator._composite_classes.append('card-separator')
        self.upper_separator._composite_classes.append('card-separator-upper')
        self.lower_separator._composite_classes.append('card-separator')
        self.lower_separator._composite_classes.append('card-separator-lower')
        self.header._composite_classes.append('tz-card-header')
        self.body._composite_classes.append('tz-card-body')
        self.footer._composite_classes.append('tz-card-footer')

        # Build layout
        self.add_widget(self.header)
        self.add_widget(self.separators[0])
        self.add_widget(self.body)
        self.add_widget(self.separators[1])
        self.add_widget(self.footer)

    @property
    def separators(self) -> tuple[HLine, HLine]:
        return (self._upper_separator, self._lower_separator)

    @property
    def upper_separator(self) -> HLine:
        return self._upper_separator

    @property
    def lower_separator(self) -> HLine:
        return self._lower_separator

    @property
    def header(self) -> Container:
        """Holds the Container located at the top of the card"""
        return self._header

    @property
    def body(self) -> Container:
        """Holds the Container located in the center of the card"""
        return self._body

    @property
    def footer(self) -> Container:
        """Holds the Container located at the bottm of the card"""
        return self._footer