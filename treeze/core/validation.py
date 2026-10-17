"""
Name:         validation.py
Description:  Validation checks

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Any, TYPE_CHECKING

from .exceptions import TreezeTypeError, TreezeValueError

if TYPE_CHECKING:
    from .widget import CSSDimension

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
    def validate_dimension(value: CSSDimension | None, *, attr_name: str) -> CSSDimension | None:
        """Validate nonnegative integer dimensions; preserve CSS strings and values."""
        from .widget import CSSDimension

        Validator.ensure(value, CSSDimension, None, attr_name=attr_name)
        if isinstance(value, bool):
            raise TreezeTypeError(f'{attr_name}: cannot be a boolean.')
        if isinstance(value, int) and value < 0:
            raise TreezeValueError(f'{attr_name}: cannot be negative.')
        return value

    @staticmethod
    def validate_spacing(
        spacing: CSSDimension | tuple[CSSDimension, CSSDimension] | None, *, attr_name: str,
    ) -> CSSDimension | tuple[CSSDimension, CSSDimension] | None:
        """Validate scalar or horizontal/vertical spacing without changing its form."""
        from .widget import CSSDimension

        Validator.ensure(spacing, CSSDimension, tuple, None, attr_name=attr_name)
        if isinstance(spacing, tuple):
            if len(spacing) != 2:
                raise TreezeValueError(f'{attr_name}: must contain exactly 2 values.')
            for index, value in enumerate(spacing):
                Validator.ensure(value, CSSDimension, attr_name=f'{attr_name}[{index}]')
                Validator.validate_dimension(value, attr_name=f'{attr_name}[{index}]')
        else:
            Validator.validate_dimension(spacing, attr_name=attr_name)
        return spacing

    @staticmethod
    def validate_box(
        value: CSSDimension | tuple[CSSDimension, CSSDimension, CSSDimension, CSSDimension] | None, *, attr_name: str,
    ) -> tuple[CSSDimension, CSSDimension, CSSDimension, CSSDimension] | None:
        """Normalize margin/padding to four nonnegative values; preserve None."""
        from .widget import CSSDimension

        Validator.ensure(value, CSSDimension, tuple, None, attr_name=attr_name)
        if value is None:
            return None
        if not isinstance(value, tuple):
            Validator.validate_dimension(value, attr_name=attr_name)
            return (value,) * 4
        if len(value) != 4:
            raise TreezeValueError(f'{attr_name}: must contain exactly 4 values.')
        for index, entry in enumerate(value):
            Validator.ensure(entry, CSSDimension, attr_name=f'{attr_name}[{index}]')
            Validator.validate_dimension(entry, attr_name=f'{attr_name}[{index}]')
        return value
