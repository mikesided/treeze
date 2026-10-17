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
from ...core.widget import Widget, CSSDimension, css_dimension

# ______________________________________________________________________________________________________________________

class Layout(Container, ABC):

    _CSS_CLASS = 'tz-layout'
    _STYLE_PREFIX = None
    _VARIANT_PREFIX = None
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
            spacing: CSSDimension | tuple[CSSDimension, CSSDimension] | None = None,
            alignment: tuple[LayoutAlignment, LayoutAlignment] = (LayoutAlignment.CENTER, LayoutAlignment.CENTER),
            horizontal_alignment: LayoutAlignment | None = None,
            ha: LayoutAlignment | None = None,  # Short code
            vertical_alignment: LayoutAlignment | None = None,
            va: LayoutAlignment | None = None,  # Short code
            *args,
            **kwargs
        ):
        for name, value in (('horizontal_alignment', horizontal_alignment),
                            ('vertical_alignment', vertical_alignment), ('ha', ha), ('va', va)):
            Validator.ensure(value, LayoutAlignment, None, attr_name=f'Layout({name}=...)')
        # Map short codes to their original values
        if ha is not None and horizontal_alignment is None:
            horizontal_alignment = ha
        if va is not None and vertical_alignment is None:
            vertical_alignment = va

        super().__init__(*args, **kwargs)

        self.add_widget = self._add_widget
        self.remove_widget = self._remove_widget

        self.spacing = spacing
        self.alignment = alignment
        if horizontal_alignment is not None:
            self.horizontal_alignment = horizontal_alignment
        if vertical_alignment is not None:
            self.vertical_alignment = vertical_alignment

    @property
    def spacing(self) -> CSSDimension | tuple[CSSDimension, CSSDimension] | None:
        return self._spacing
    
    @spacing.setter
    def spacing(self, spacing: CSSDimension | tuple[CSSDimension, CSSDimension] | None):
        """Spacing is a CSS dimension or tuple(horizontal spacing, vertical spacing)."""
        self._spacing = Validator.validate_spacing(spacing, attr_name='Layout.spacing')
    
    @property
    def horizontal_alignment(self) -> LayoutAlignment:
        return self._horizontal_alignment
    
    @horizontal_alignment.setter
    def horizontal_alignment(self, alignment: LayoutAlignment):
        self._horizontal_alignment = Validator.ensure(alignment, LayoutAlignment, attr_name='Layout.horizontal_alignment')
    
    @property
    def vertical_alignment(self) -> LayoutAlignment:
        return self._vertical_alignment
    
    @vertical_alignment.setter
    def vertical_alignment(self, alignment: LayoutAlignment):
        self._vertical_alignment = Validator.ensure(alignment, LayoutAlignment, attr_name='Layout.vertical_alignment')

    @property
    def alignment(self) -> tuple[LayoutAlignment, LayoutAlignment]:
        return (self.horizontal_alignment, self.vertical_alignment)

    @alignment.setter
    def alignment(self, layout_alignments: tuple[LayoutAlignment, LayoutAlignment]):
        """Convenience wrapper around horizontal & vertical layout alignments"""
        Validator.ensure(layout_alignments, tuple, list, attr_name='Layout.alignment')
        if len(layout_alignments) != 2:
            raise TreezeValueError('Layout.alignment: must contain exactly 2 values.')
        Validator.ensure(layout_alignments[0], LayoutAlignment, attr_name='Layout.alignment[0]')
        Validator.ensure(layout_alignments[1], LayoutAlignment, attr_name='Layout.alignment[1]')
        self.horizontal_alignment = layout_alignments[0]
        self.vertical_alignment = layout_alignments[1]

    def _styles(self) -> dict[str, str]:
        styles = super()._styles()

        if isinstance(self.spacing, tuple):
            # NOTE: row-gap maps to "vertical spacing", and column-gap maps to "horizontal spacing"
            styles['gap'] = f'{css_dimension(self.spacing[1])} {css_dimension(self.spacing[0])}'
        elif self.spacing is not None:
            styles['gap'] = css_dimension(self.spacing)

        return styles
    
    @abstractmethod
    def _render(self) -> Node:
        raise NotImplementedError
