"""
Name:         exceptions.py
Description:  Exceptions raised by treeze

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations

# ______________________________________________________________________________________________________________________


class TreezeError(Exception):
    """
    Base exception for all User-related errors
    """
    pass


class TreezeTypeError(TreezeError, TypeError):
    """
    Raised when a Treeze object receives an invalid type.
    """
    pass


class TreezeValueError(TreezeError, ValueError):
    """
    Raised when a Treeze object receives an invalid value.
    """
    pass


class TreezeRuntimeError(TreezeError, RuntimeError):
    """
    Raised when a Treeze runtime operation fails.
    """
    pass

class WidgetError(TreezeError):
    """
    Raised when a Treeze runtime operation fails.
    """
    pass

class RenderError(TreezeError):
    """
    Raised when a Treeze runtime operation fails.
    """
    pass