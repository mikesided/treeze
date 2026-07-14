"""
Name:         size.py
Description:  Dataclass reprensenting an (x, y) size

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass

from ..exceptions import TreezeTypeError, TreezeValueError

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True)
class Size:
    """2D Size"""
    width: int
    height: int

    def __post_init__(self):
        if not isinstance(self.width, int):
            raise TreezeTypeError('width must be an int')
        if not isinstance(self.height, int):
            raise TreezeTypeError('height must be an int')
        if self.width < 0 or self.height < 0:
            raise TreezeValueError('width and height cannot be negative')
    
