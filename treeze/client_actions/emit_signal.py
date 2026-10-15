"""
Name:         emit_signal.py
Description:  Emit a browser-backed signal with positional arguments

"""
# ______________________________________________________________________________________________________________________
# Imports
from dataclasses import dataclass, field

from ..core.client_action import ClientAction
from ..core.signals import BoundSignal

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True, slots=True, init=False)
class EmitSignal(ClientAction):
    type: str = field(default='emit_signal', init=False)
    widget_id: str
    browser_event: str
    args: tuple

    def __init__(self, signal: BoundSignal, /, *args):
        event = next(event for event, binding in signal.owner._render().events.items() if binding.signal == signal.name)
        object.__setattr__(self, 'type', 'emit_signal')
        object.__setattr__(self, 'widget_id', signal.owner.id)
        object.__setattr__(self, 'browser_event', event.value)
        object.__setattr__(self, 'args', args)
