"""
Name:         background_image.py
Description:  CSS background image value

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass

from ..enums import ImageStyle, Position
from ..validation import Validator

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True, slots=True)
class BackgroundImage:
    source: str
    style: ImageStyle = ImageStyle.FILL
    position: Position = Position.CENTER

    def __post_init__(self):
        Validator.ensure(self.source, str, attr_name='BackgroundImage.source')
        Validator.ensure(self.style, ImageStyle, attr_name='BackgroundImage.style')
        Validator.ensure(self.position, Position, attr_name='BackgroundImage.position')

    def _styles(self) -> dict[str, str]:
        source = self.source.replace('\\', '\\\\').replace('"', '\\"')
        source = source.replace('\n', '\\a ').replace('\r', '\\d ').replace('\f', '\\c ')
        return {
            'background-image': f'url("{source}")',
            'background-size': {
                ImageStyle.FILL: 'cover',
                ImageStyle.FIT: 'contain',
                ImageStyle.FIXED: 'auto',
            }[self.style],
            'background-position': self.position.value,
            'background-repeat': 'no-repeat',
        }
