"""
Name:         size.py
Description:  Dataclass reprensenting an (x, y) size

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..validation import Validator

if TYPE_CHECKING:
    from ..widget import CSSDimension

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True)
class Size:
    """2D Size"""
    width: CSSDimension
    height: CSSDimension

    def __post_init__(self):
        from ..widget import CSSDimension

        Validator.ensure(self.width, CSSDimension, attr_name='Size.width')
        Validator.ensure(self.height, CSSDimension, attr_name='Size.height')
        Validator.validate_dimension(self.width, attr_name='Size.width')
        Validator.validate_dimension(self.height, attr_name='Size.height')
    
