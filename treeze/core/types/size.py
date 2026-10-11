"""
Name:         size.py
Description:  Dataclass reprensenting an (x, y) size

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass

from ..validation import Validator

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True)
class Size:
    """2D Size"""
    width: int
    height: int

    def __post_init__(self):
        Validator.ensure(self.width, int, attr_name='Size.width')
        Validator.ensure(self.height, int, attr_name='Size.height')
        Validator.validate_dimension(self.width, attr_name='Size.width')
        Validator.validate_dimension(self.height, attr_name='Size.height')
    
