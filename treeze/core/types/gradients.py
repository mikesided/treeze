"""
Name:         gradients.py
Description:  Color gradient types
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Mapping, Sequence


from ..enums import Color
from ..exceptions import TreezeTypeError, TreezeValueError
from ..validation import Validator

# ______________________________________________________________________________________________________________________


class LinearGradient:

    def __init__(
        self,
        stops: Sequence[str | Color] | Mapping[int | float, str | Color],
        angle: int | float = 90,
    ):
        if isinstance(stops, Mapping):
            for percentage, color in stops.items():
                Validator.ensure(percentage, int, float)
                Validator.ensure(color, str, Color)
        elif isinstance(stops, Sequence) and not isinstance(stops, str):
            for color in stops:
                Validator.ensure(color, str, Color)
        else:
            raise TreezeTypeError('Gradient stops must be a color sequence or percentage-to-color mapping.')

        self.stops = stops
        self.angle = angle

    def __str__(self) -> str:
        if isinstance(self.stops, Mapping):
            stops = ', '.join(
                f'{color} {percentage:g}%'
                for percentage, color 
                in self.stops.items()
            )
        else:
            stops = ', '.join(self.stops)

        return f'linear-gradient({self.angle}deg, {stops})'
