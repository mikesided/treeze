"""
Name:         clamp.py
Description:  CSS clamp value

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass

from ..exceptions import TreezeTypeError

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True, slots=True)
class Clamp:
    minimum: int | str
    preferred: int | str
    maximum: int | str

    def __post_init__(self):
        for name in ('minimum', 'preferred', 'maximum'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, str)):
                raise TreezeTypeError(f'Clamp.{name}: expected an integer or CSS length string.')

    def __str__(self) -> str:
        from ..widget import css_dimension

        return f'clamp({css_dimension(self.minimum)}, {css_dimension(self.preferred)}, {css_dimension(self.maximum)})'
