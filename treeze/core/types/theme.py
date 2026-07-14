"""
Name:         theme.py
Description:  Dataclass representing theme override variables
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Any, TypeAlias
from dataclasses import dataclass, field, fields
from enum import StrEnum

from ..exceptions import TreezeTypeError, TreezeValueError

# ______________________________________________________________________________________________________________________

CssColor: TypeAlias = str | StrEnum | None  # Converted to raw string
CssLength: TypeAlias = str | int | float | None  # Converted to raw string or suffixed with 'px'
CssNumber: TypeAlias = str | int | float | None  # Converted to raw string
CssText: TypeAlias = str | None  # Converted to raw string

CssValue: TypeAlias = str | int | float | StrEnum | None  # Combination of all values


# ______________________________________________________________________________________________________________________
# Field helpers

def color_field() -> Any:
    """Attribute prefixed with --tz-color-{attr}"""
    metadata={'css_kind': 'color', 'css_prefix': '--tz-color-'}
    return field(default=None, metadata=metadata)


def length_field() -> Any:
    """Attribute prefixed with --tz-{attr}"""
    metadata={'css_kind': 'length', 'css_prefix': '--tz-'}
    return field(default=None, metadata=metadata)


def number_field() -> Any:
    """Attribute prefixed with --tz-{attr}"""
    metadata = {'css_kind': 'number', 'css_prefix': '--tz-'}
    return field(default=None, metadata=metadata)


def text_field() -> Any:
    """Attribute prefixed with --tz-{attr}"""
    metadata = {'css_kind': 'text', 'css_prefix': '--tz-'}
    return field(default=None, metadata=metadata)


# ______________________________________________________________________________________________________________________

@dataclass(slots=True)
class Theme:

    # ==========================================================================
    # Typography
    # ==========================================================================

    font_family: CssText = text_field()
    font_size: CssLength = length_field()
    line_height: CssNumber = number_field()

    # ==========================================================================
    # Spacing / shape
    # ==========================================================================

    spacing: CssLength = length_field()
    radius_sm: CssLength = length_field()
    radius_md: CssLength = length_field()
    radius_lg: CssLength = length_field()
    radius_full: CssLength = length_field()

    # ==========================================================================
    # Background / surfaces
    # ==========================================================================

    background: CssColor = color_field()

    surface: CssColor = color_field()
    surface_hover: CssColor = color_field()
    surface_active: CssColor = color_field()
    surface_raised: CssColor = color_field()
    surface_sunken: CssColor = color_field()

    # ==========================================================================
    # Text
    # ==========================================================================

    text: CssColor = color_field()
    text_muted: CssColor = color_field()
    text_disabled: CssColor = color_field()
    text_inverse: CssColor = color_field()

    # ==========================================================================
    # Borders / focus
    # ==========================================================================

    border: CssColor = color_field()
    border_hover: CssColor = color_field()
    border_strong: CssColor = color_field()

    focus: CssColor = color_field()

    # ==========================================================================
    # Primary
    # ==========================================================================

    primary: CssColor = color_field()
    primary_hover: CssColor = color_field()
    primary_active: CssColor = color_field()
    on_primary: CssColor = color_field()

    # ==========================================================================
    # Secondary
    # ==========================================================================

    secondary: CssColor = color_field()
    secondary_hover: CssColor = color_field()
    secondary_active: CssColor = color_field()
    on_secondary: CssColor = color_field()

    # ==========================================================================
    # Tertiary
    # ==========================================================================

    tertiary: CssColor = color_field()
    tertiary_hover: CssColor = color_field()
    tertiary_active: CssColor = color_field()
    on_tertiary: CssColor = color_field()

    # ==========================================================================
    # Success
    # ==========================================================================

    success: CssColor = color_field()
    success_hover: CssColor = color_field()
    success_active: CssColor = color_field()
    on_success: CssColor = color_field()

    # ==========================================================================
    # Warning
    # ==========================================================================

    warning: CssColor = color_field()
    warning_hover: CssColor = color_field()
    warning_active: CssColor = color_field()
    on_warning: CssColor = color_field()

    # ==========================================================================
    # Danger
    # ==========================================================================

    danger: CssColor = color_field()
    danger_hover: CssColor = color_field()
    danger_active: CssColor = color_field()
    on_danger: CssColor = color_field()

    # ==========================================================================
    # Info
    # ==========================================================================

    info: CssColor = color_field()
    info_hover: CssColor = color_field()
    info_active: CssColor = color_field()
    on_info: CssColor = color_field()

    # ==========================================================================
    # Disabled
    # ==========================================================================

    disabled: CssColor = color_field()
    disabled_border: CssColor = color_field()
    on_disabled: CssColor = color_field()

    # ==========================================================================
    # Conversion
    # ==========================================================================

    def _to_css_variables(self) -> dict[str, str]:
        """
        Convert theme overrides to CSS custom properties.

        Only values that are not None are emitted.
        """
        css_variables: dict[str, str] = {}

        for theme_field in fields(self):
            name = theme_field.name
            value = getattr(self, name)

            css_kind = theme_field.metadata.get('css_kind')
            css_prefix = theme_field.metadata.get('css_prefix')

            if not isinstance(css_kind, str):
                raise RuntimeError(f'Missing CSS kind for theme field: {name!r}')

            if not isinstance(css_prefix, str):
                raise RuntimeError(f'Missing CSS prefix for theme field: {name!r}')

            css_value = self._css_value(name, value, css_kind)

            if css_value is None:
                continue

            css_variables[self._css_variable_name(name, css_prefix)] = css_value

        return css_variables

    @staticmethod
    def _css_variable_name(name: str, css_prefix: str) -> str:
        css_name = name.replace('_', '-')
        return f'{css_prefix}{css_name}'

    @classmethod
    def _css_value(cls, name: str, value: CssValue, css_kind: str) -> str | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise TreezeTypeError(f'Theme value {name!r} cannot be a boolean.')

        match css_kind:
            case 'color':
                if not isinstance(value, str | StrEnum):
                    raise TreezeTypeError(f'Theme color {name!r} must be a string, Color, or None.')

                return str(value)

            case 'length':
                if isinstance(value, int | float):
                    return f'{value}px'

                if isinstance(value, str):
                    return value

                raise TreezeTypeError(f'Theme length {name!r} must be a string, number, or None.')

            case 'number':
                if isinstance(value, int | float):
                    return str(value)

                if isinstance(value, str):
                    return value

                raise TreezeTypeError(f'Theme number {name!r} must be a string, number, or None.')

            case 'text':
                if not isinstance(value, str):
                    raise TreezeTypeError(f'Theme text value {name!r} must be a string or None.')

                return value

            case _:
                raise RuntimeError(f'Unsupported CSS kind: {css_kind!r}')
            