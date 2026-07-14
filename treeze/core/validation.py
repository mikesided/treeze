"""
Name:         validation.py
Description:  Validation checks

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Any

from .exceptions import TreezeTypeError

# ______________________________________________________________________________________________________________________

class Validator:

    @staticmethod
    def ensure(value: Any, *expected: type) -> Any:
        """Ensure a datatype is valid and return it, or raise
        
        Args:
            value: Value to be validated
            *expected: Any valid datatypes

        Returns:
            Validated value
            
        Raises:
            TreezeTypeError: Raised if value doesn't match expected datatypes
        """
        if not expected:
            raise ValueError('At least one expected type must be provided.')
        
        expected = tuple(
            type(None) if item is None else item
            for item in expected
        )

        if not isinstance(value, expected):
            names = ', '.join(
                'None' if t is type(None) else t.__name__
                for t in expected
            )
            raise TreezeTypeError(f'Expected {names}, got {type(value).__name__}')
        
        return value