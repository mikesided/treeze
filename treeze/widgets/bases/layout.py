"""
Name:         layout.py
Description:  Base class for a Layout (abstract)

"""
# ______________________________________________________________________________________________________________________
# Imports
from abc import ABC, abstractmethod

from .container import Container

from ...core.enums import LayoutAlignment, LayoutStyle, InsertPosition, Variant
from ...core.exceptions import TreezeValueError
from ...core.node import Node
from ...core.validation import Validator
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class Layout(Container, ABC):

    _CSS_CLASS = 'tz-layout'
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
            spacing: int | tuple[int, int] | None = None,
            alignment: tuple[LayoutAlignment, LayoutAlignment] = (LayoutAlignment.CENTER, LayoutAlignment.CENTER),
            horizontal_alignment: LayoutAlignment | None = None,
            ha: LayoutAlignment | None = None,  # Short code
            vertical_alignment: LayoutAlignment | None = None,
            va: LayoutAlignment | None = None,  # Short code
            *args,
            **kwargs
        ):
        # Map short codes to their original values
        if ha and horizontal_alignment is None:
            horizontal_alignment = ha
        if va and vertical_alignment is None:
            vertical_alignment = va

        super().__init__(*args, **kwargs)

        self.add_widget = self._add_widget
        self.remove_widget = self._remove_widget

        self.spacing = spacing
        self.alignment = alignment
        if horizontal_alignment:
            self.horizontal_alignment = horizontal_alignment
        if vertical_alignment:
            self.vertical_alignment = vertical_alignment

    @property
    def spacing(self) -> int | tuple[str, str]:
        return self._spacing
    
    @spacing.setter
    def spacing(self, spacing: int | tuple[int, int] | None):
        """Spacing can be an int or tuple(horizontal spacing, vertical spacing)"""
        self._spacing = None if spacing is None else Validator.validate_spacing(spacing=spacing)
    
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

    @property
    def alignment(self) -> tuple[LayoutAlignment, LayoutAlignment]:
        return (self.horizontal_alignment, self.vertical_alignment)

    @alignment.setter
    def alignment(self, layout_alignments: tuple[LayoutAlignment, LayoutAlignment]):
        """Convenience wrapper around horizontal & vertical layout alignments"""
        self.horizontal_alignment = layout_alignments[0]
        self.vertical_alignment = layout_alignments[1]

    def _styles(self) -> dict[str, str]:
        styles = super()._styles()

        if isinstance(self.spacing, int):
            styles['gap'] = f'{self.spacing}px'
        elif isinstance(self.spacing, tuple):
            # NOTE: row-gap maps to "vertical spacing", and column-gap maps to "horizontal spacing"
            styles['gap'] = f'{self.spacing[1]}px {self.spacing[0]}px'

        return styles
    
    @abstractmethod
    def _render(self) -> Node:
        raise NotImplementedError
