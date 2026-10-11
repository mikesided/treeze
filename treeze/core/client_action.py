"""
Name:         client_action.py
Description:  Serializable commands executed by the browser.

"""
# ______________________________________________________________________________________________________________________
# Imports
from dataclasses import asdict, dataclass, field

from .exceptions import TreezeTypeError, TreezeValueError
from .validation import Validator

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True, slots=True)
class ClientAction:
    type: str = field(kw_only=True)

    def __post_init__(self) -> None:
        Validator.ensure(self.type, str)
        if not self.type.strip():
            raise TreezeValueError('ClientAction.type cannot be empty.')

    def serialize(self) -> dict:
        """Serialize all dataclass fields, including inherited and nested fields."""
        return asdict(self)
