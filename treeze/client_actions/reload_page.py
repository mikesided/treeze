"""
Name:         reload_page.py
Description:  Reload the current browser page

"""
# ______________________________________________________________________________________________________________________
# Imports

from dataclasses import dataclass, field

from ..core.client_action import ClientAction

# ______________________________________________________________________________________________________________________


@dataclass(frozen=True, slots=True)
class ReloadPage(ClientAction):
    type: str = field(default='reload_page', init=False)
