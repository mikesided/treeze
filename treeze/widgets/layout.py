"""
Name:         layout.py
Description:  Base class for a Layout (abstract)

"""
# ______________________________________________________________________________________________________________________
# Imports
from abc import ABC, abstractmethod

from .container import Container

from ..core.enums import LayoutAlignment
from ..core.node import Node
from ..core.validation import Validator

# ______________________________________________________________________________________________________________________

class Layout(Container, ABC):

    _CSS_CLASS = 'tz-layout'
    def __init__(
            self, 
            spacing: int = 0,
            horizontal_alignment: LayoutAlignment = LayoutAlignment.CENTER,
            vertical_alignment: LayoutAlignment = LayoutAlignment.CENTER,
            *args,
            **kwargs
        ):
        super().__init__(*args, **kwargs)

        self.spacing = spacing
        self.horizontal_alignment = horizontal_alignment
        self.vertical_alignment = vertical_alignment

    @property
    def spacing(self) -> int:
        return self._spacing
    
    @spacing.setter
    def spacing(self, spacing: int):
        self._spacing = Validator.ensure(spacing, int)
    
    @property
    def horizontal_alignment(self) -> LayoutAlignment:
        return self._horizontal_alignment
    
    @horizontal_alignment.setter
    def horizontal_alignment(self, alignment: LayoutAlignment):
        self._horizontal_alignment = Validator.ensure(alignment, LayoutAlignment)
    
    @property
    def vertical_alignment(self) -> LayoutAlignment:
        return self._vertical_alignment
    
    @vertical_alignment.setter
    def vertical_alignment(self, alignment: LayoutAlignment):
        self._vertical_alignment = Validator.ensure(alignment, LayoutAlignment)

    def _styles(self) -> dict[str, str]:
        styles = super()._styles()
        styles.update({
            'display': 'flex',
            '--tz-spacing': f'{self.spacing}px',
            '--tz-vertical-alignment': self.vertical_alignment.value,
            '--tz-horizontal-alignment': self.horizontal_alignment.value,
        })
        return styles
    
    @abstractmethod
    def _render(self) -> Node:
        raise NotImplementedError