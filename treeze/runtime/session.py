"""
Name:         session.py
Description:  Runtime session for one connected browser
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
import uuid

from .patch_engine import PatchEngine
from .patches import diff_nodes
from .protocol import ClientSignalMessage, ServerActionsMessage, ServerPatchesMessage

from ..core.exceptions import TreezeRuntimeError
from ..core.node import Node
from ..core.client_action import ClientAction
from ..core.validation import Validator

from ..utils.ids import create_id_scope, use_id_scope
from ..utils.session_context import use_session

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
        self._outgoing: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pending_actions: list[dict[str, Any]] = []
        self._handling_message = False

        self.id_scope = create_id_scope()

        with use_session(self), use_id_scope(self.id_scope):
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

        with use_session(self), use_id_scope(self.id_scope):
            node_tree = self.app._build_window(self.window)
            self._index_widgets()
            self._patch_engine.capture_tree(node_tree)
            self._clear_dirty_state()

        return node_tree

    def _handle_message(self, message: dict[str, Any]) -> list[dict[str, Any]]:
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

        with use_session(self), use_id_scope(self.id_scope):
            match message_type:
                case 'client.signal':
                    signal_message = ClientSignalMessage.from_payload(payload)
                    self._handling_message = True
                    try:
                        self._handle_signal_message(signal_message)
                    except BaseException:
                        self._pending_actions.clear()
                        raise
                    finally:
                        self._handling_message = False

                    self._index_widgets()

                    patches = self._patch_engine.create_patches_for_dirty_widgets(
                        self._dirty_widgets,
                    )

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

        # Browser-bound actions already ran in the browser event handler.
        browser_bound = widget._node is not None and any(
            binding.signal == message.signal for binding in widget._node.events.values()
        )
        widget._get_signal(message.signal)._emit(
            message.args,
            message.kwargs or {},
            execute_actions=not browser_bound,
        )

    def _queue_client_action(self, action: ClientAction) -> None:
        if self.closed:
            raise TreezeRuntimeError('Cannot execute a client action on a closed session.')
        payload = action.serialize()
        if self._handling_message:
            self._pending_actions.append(payload)
        else:
            self._outgoing.put_nowait(
                ServerActionsMessage(actions=(payload,)).to_protocol_message().to_dict()
            )

    def _publish_update(self, patches: list[dict[str, Any]]) -> None:
        """Send patches and their one-time actions together, in execution order."""
        actions = tuple(self._pending_actions)
        self._pending_actions.clear()
        if patches or actions:
            self._outgoing.put_nowait(
                ServerPatchesMessage(patches=patches, actions=actions).to_protocol_message().to_dict()
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
        self._pending_actions.clear()
        while not self._outgoing.empty():
            self._outgoing.get_nowait()

    def _mark_widget_dirty(self, widget: Widget) -> None:
        if self.closed:
            return

        self._dirty_widgets.add(widget)

    def _clear_dirty_state(self) -> None:
        for widget in self._widgets.values():
            widget._mark_clean()

        self._dirty_widgets.clear()
