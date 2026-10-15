"""
Name:         reconnect.py
Description:  Reconnects the websocket

"""
# ______________________________________________________________________________________________________________________
# Imports

from dataclasses import dataclass, field

from ..core.client_action import ClientAction
from ..core.validation import Validator

# ______________________________________________________________________________________________________________________


@dataclass(frozen=True, slots=True)
class Reconnect(ClientAction):

    type: str = field(default='reconnect', init=False)
    query_params: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        ClientAction.__post_init__(self)

        Validator.ensure(self.query_params, dict, attr_name='Reconnect.query_params')

        for key, value in self.query_params.items():
            Validator.ensure(key, str)
            Validator.ensure(value, str)