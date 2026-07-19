"""
Name:         session.py
Description:  Runtime session for one connected browser
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
import uuid

from .patch_engine import PatchEngine
from .patches import diff_nodes
from .protocol import ClientSignalMessage

from ..core.exceptions import TreezeRuntimeError
from ..core.node import Node
from ..core.validation import Validator

from ..utils.ids import create_id_scope, use_id_scope

if TYPE_CHECKING:
    from ..core.app import App
    from ..core.widget import Widget
    from ..widgets.primitives.window import Window

# ______________________________________________________________________________________________________________________
class SessionManager:

    def __init__(self, app: App):
        self._app = app
        self._sessions: dict[str, Session] = {}

    # ==========================================================================
    #  Internal methods
    # ==========================================================================

    def _create_session(self) -> Session:
        session = Session(self._app)
        self._sessions[session.id] = session

        return session

    def _close_session(self, session: Session) -> None:
        session._close()
        self._sessions.pop(session.id, None)

    def _get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def _clear(self) -> None:
        for session in tuple(self._sessions.values()):
            session._close()

        self._sessions.clear()


class Session:

    def __init__(self, app: App):
        self._id = uuid.uuid4().hex
        self._app = app
        self._widgets: dict[str, Widget] = {}  # Widgets are walked & stored here for lookup by events
        self._created_at = datetime.now(timezone.utc)
        self._closed = False

        self._dirty_widgets: set[Widget] = set()
        self._patch_engine = PatchEngine()

        self.id_scope = create_id_scope()

        with use_id_scope(self.id_scope):
            # Session contains one main initialized window (generated from the app)
            self._window = app._create_window()

    # ==========================================================================
    #  Properties
    # ==========================================================================

    @property
    def id(self) -> str:
        """Read only. Unique session ID."""
        return self._id

    @property
    def app(self) -> App:
        """Read only. Parent App."""
        return self._app

    @property
    def window(self) -> Window:
        """Read only. Session window instance."""
        return self._window

    @property
    def created_at(self) -> datetime:
        """Read only. Session creation time."""
        return self._created_at

    @property
    def closed(self) -> bool:
        """Read only. Has this session been closed?"""
        return self._closed

    # ==========================================================================
    #  Internal Methods
    # ==========================================================================

    def _build(self) -> Node:
        """Build this session's current node tree."""
        if self.closed:
            raise TreezeRuntimeError('Cannot build a closed session.')

        node_tree = self.app._build_window(self.window)

        self._index_widgets()
        self._patch_engine.capture_tree(node_tree)

        self._clear_dirty_state()

        return node_tree

    def _handle_message(self, message: dict[str, Any]) -> None:
        """
        Handle a client message for this session.

        For now, this works by:
        - serializing the current node tree
        - emitting the signal
        - rebuilding the new node tree
        - diffing old vs new
        - returning patches
        """
        if self.closed:
            raise TreezeRuntimeError('Cannot handle messages on a closed session.')

        message = Validator.ensure(message, dict)
        message_type = Validator.ensure(message.get('type'), str)
        payload = Validator.ensure(message.get('payload'), dict)

        with use_id_scope(self.id_scope):
            match message_type:
                case 'client.signal':
                    self._dirty_widgets.clear()

                    signal_message = ClientSignalMessage.from_payload(payload)
                    self._handle_signal_message(signal_message)

                    self._index_widgets()

                    patches = self._patch_engine.create_patches_for_dirty_widgets(
                        self._dirty_widgets,
                    )

                    import pprint
                    pprint.pprint(patches)

                    for widget in self._dirty_widgets:
                        widget._mark_clean()

                    self._clear_dirty_state()

                    return patches

                case _:
                    raise TreezeRuntimeError(
                        f'Unsupported client message type: {message_type!r}.'
                    )
            
    def _handle_signal_message(self, message: ClientSignalMessage) -> None:
        widget = self._widgets.get(message.widget_id)

        if widget is None:
            raise TreezeRuntimeError(
                f'Trying to find widget for client signal but no widget found for id {message.widget_id!r}.'
            )

        widget._emit_signal(
            message.signal,
            *message.args,
            **(message.kwargs or {}),
        )

    def _index_widgets(self) -> None:
        """Walk all widgets of the app and store them on self for reference"""
        self._widgets = {}

        for widget in self.window._walk_widgets():
            widget._set_session(self)
            self._widgets[widget.id] = widget

    def _close(self) -> None:
        """Close the session and release runtime references."""
        if self.closed:
            return

        self._closed = True

    def _mark_widget_dirty(self, widget: Widget) -> None:
        if self.closed:
            return

        self._dirty_widgets.add(widget)

    def _clear_dirty_state(self) -> None:
        for widget in self._widgets.values():
            widget._mark_clean()

        self._dirty_widgets.clear()