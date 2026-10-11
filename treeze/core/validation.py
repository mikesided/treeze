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
    def ensure(value: Any, *expected: type, attr_name: str | None = None) -> Any:
        """Ensure a datatype is valid and return it, or raise
        
        Args:
            value: Value to be validated
            *expected: Any valid datatypes
            attr_name: Attribute name, added to the raised message

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
                'None' if t is type(None) else getattr(t, '__name__', str(t))
                for t in expected
            )
            if attr_name:
                raise TreezeTypeError(f'{attr_name}: expected {names}, got {type(value).__name__}')
            else:
                raise TreezeTypeError(f'Expected {names}, got {type(value).__name__}')
        
        return value

    @staticmethod
    def validate_dimension(value: int | None, *, attr_name: str) -> int | None:
        """Validate a nonnegative integer dimension, or None for an unset value."""
        Validator.ensure(value, int, None, attr_name=attr_name)
        if isinstance(value, bool):
            raise TreezeTypeError(f'{attr_name}: cannot be a boolean.')
        if value is not None and value < 0:
            raise TreezeValueError(f'{attr_name}: cannot be negative.')
        return value

    @staticmethod
    def validate_spacing(
        spacing: int | tuple[int, int] | None, *, attr_name: str,
    ) -> int | tuple[int, int] | None:
        """Validate scalar or horizontal/vertical spacing without changing its form."""
        Validator.ensure(spacing, int, tuple, None, attr_name=attr_name)
        if isinstance(spacing, tuple):
            if len(spacing) != 2:
                raise TreezeValueError(f'{attr_name}: must contain exactly 2 values.')
            for index, value in enumerate(spacing):
                Validator.ensure(value, int, attr_name=f'{attr_name}[{index}]')
                Validator.validate_dimension(value, attr_name=f'{attr_name}[{index}]')
        else:
            Validator.validate_dimension(spacing, attr_name=attr_name)
        return spacing

    @staticmethod
    def validate_box(
        value: int | tuple[int, int, int, int] | None, *, attr_name: str,
    ) -> tuple[int, int, int, int] | None:
        """Normalize margin/padding to four nonnegative values; preserve None."""
        Validator.ensure(value, int, tuple, None, attr_name=attr_name)
        if value is None:
            return None
        if isinstance(value, int):
            Validator.validate_dimension(value, attr_name=attr_name)
            return (value,) * 4
        if len(value) != 4:
            raise TreezeValueError(f'{attr_name}: must contain exactly 4 values.')
        for index, entry in enumerate(value):
            Validator.ensure(entry, int, attr_name=f'{attr_name}[{index}]')
            Validator.validate_dimension(entry, attr_name=f'{attr_name}[{index}]')
        return value
