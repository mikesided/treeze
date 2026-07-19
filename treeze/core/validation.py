"""
Name:         validation.py
Description:  Validation checks

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Any

from .exceptions import TreezeTypeError, TreezeValueError

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
    
    @staticmethod
    def validate_spacing(spacing: int) -> int:
        """Spacing cannot be negative"""
        spacing = Validator.ensure(spacing, int)

        if spacing < 0:
            raise TreezeValueError('Spacing cannot be negative.')

        return spacing
    
    @staticmethod
    def validate_margin(margin: int | tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Margins must return a tuple[int, int, int, int] but supports a single int"""
        if isinstance(margin, tuple):
            if len(margin) != 4:
                raise TreezeValueError('Margin must contain 4 values')
        elif isinstance(margin, int):
            margin = (margin, margin, margin, margin)

        margin = Validator.ensure(margin, tuple)

        if not all(
            isinstance(_, int) for _ in margin
        ):
            raise TreezeTypeError('Margin must be integers')
        
        if not all(
            _ >= 0 for _ in margin
        ):
            raise TreezeValueError('Margin cannot be negative')

        return margin
    
    @staticmethod
    def validate_padding(padding: int | tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Paddings must return a tuple[int, int, int, int] but supports a single int"""
        if isinstance(padding, tuple):
            if len(padding) != 4:
                raise TreezeValueError('Padding must contain 4 values')
        elif isinstance(padding, int):
            padding = (padding, padding, padding, padding)

        padding = Validator.ensure(padding, tuple)

        if not all(
            isinstance(_, int) for _ in padding
        ):
            raise TreezeTypeError('Padding must be integers')
        
        if not all(
            _ >= 0 for _ in padding
        ):
            raise TreezeValueError('Padding cannot be negative')

        return padding

