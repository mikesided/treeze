"""
Name:         gradients.py
Description:  Color gradient types
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Mapping, Sequence
from math import isfinite


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
        self.stops = stops
        self.angle = angle

    @property
    def angle(self) -> int | float:
        return self._angle

    @angle.setter
    def angle(self, angle: int | float) -> None:
        Validator.ensure(angle, int, float, attr_name='LinearGradient.angle')
        if isinstance(angle, bool):
            raise TreezeTypeError('LinearGradient.angle: cannot be a boolean.')
        if isinstance(angle, float) and not isfinite(angle):
            raise TreezeValueError('LinearGradient.angle: must be finite.')
        self._angle = angle

    @property
    def stops(self) -> Sequence[str | Color] | Mapping[int | float, str | Color]:
        # Return a copy of mappings so callers cannot bypass the setter.
        return dict(self._stops) if isinstance(self._stops, Mapping) else self._stops

    @stops.setter
    def stops(self, stops: Sequence[str | Color] | Mapping[int | float, str | Color]) -> None:
        Validator.ensure(stops, Mapping, Sequence, attr_name='LinearGradient.stops')
        if isinstance(stops, Mapping):
            for percentage, color in stops.items():
                name = f'LinearGradient.stops.keys[{percentage!r}]'
                Validator.ensure(percentage, int, float, attr_name=name)
                if isinstance(percentage, bool):
                    raise TreezeTypeError(f'{name}: cannot be a boolean.')
                if isinstance(percentage, float) and not isfinite(percentage):
                    raise TreezeValueError(f'{name}: must be finite.')
                Validator.ensure(color, str, Color, attr_name=f'LinearGradient.stops[{percentage!r}]')
            validated = dict(stops)
        elif not isinstance(stops, str):
            for index, color in enumerate(stops):
                Validator.ensure(color, str, Color, attr_name=f'LinearGradient.stops[{index}]')
            validated = tuple(stops)
        else:
            raise TreezeTypeError('LinearGradient.stops: must be a color sequence or percentage-to-color mapping.')
        self._stops = validated

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

class RadialGradient:
    pass

class ConeGradient:
    pass
