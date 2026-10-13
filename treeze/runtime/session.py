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
        self._message_lock = asyncio.Lock()

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
            processed_widgets = self._dirty_widgets
            self._dirty_widgets = set()
            try:
                node_tree = self.app._build_window(self.window)
                self._index_widgets()
                self._patch_engine.capture_tree(node_tree)
            except BaseException:
                self._dirty_widgets.update(processed_widgets)
                raise
            # A full initial render also covers widgets built outside this session.
            self._clear_dirty_state(processed_widgets | set(self._widgets.values()))

        return node_tree

    async def _handle_message(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        """Await a client's callbacks in session context and return its UI patches."""
        message = Validator.ensure(message, dict, attr_name='Session._handle_message(message=...)')
        message_type = Validator.ensure(message.get('type'), str, attr_name='client.signal.type')
        payload = Validator.ensure(message.get('payload'), dict, attr_name='client.signal.payload')

        # One session is sequential; other sessions have their own lock.
        async with self._message_lock:
            if self.closed:
                raise TreezeRuntimeError('Cannot handle messages on a closed session.')
            with use_session(self), use_id_scope(self.id_scope):
                if message_type != 'client.signal':
                    raise TreezeRuntimeError(f'Unsupported client message type: {message_type!r}.')
                signal_message = ClientSignalMessage.from_payload(payload)
                self._handling_message = True
                try:
                    await self._handle_signal_message(signal_message)
                except BaseException:
                    self._pending_actions.clear()
                    raise
                finally:
                    self._handling_message = False

                self._index_widgets()
                processed_widgets = self._dirty_widgets
                self._dirty_widgets = set()
                try:
                    patches = self._patch_engine.create_patches_for_dirty_widgets(processed_widgets)
                except BaseException:
                    self._dirty_widgets.update(processed_widgets)
                    self._pending_actions.clear()
                    raise
                self._clear_dirty_state(processed_widgets)
                return patches

    async def _handle_signal_message(self, message: ClientSignalMessage) -> None:
        widget = self._widgets.get(message.widget_id)

        if widget is None:
            raise TreezeRuntimeError(
                f'Trying to find widget for client signal but no widget found for id {message.widget_id!r}.'
            )

        # Check server-owned state; browser attributes cannot authorize a signal.
        owner = widget
        while owner is not None:
            if owner.enabled is False:
                return
            owner = owner.parent

        browser_bound = widget._node is not None and any(
            binding.signal == message.signal for binding in widget._node.events.values()
        )
        if not browser_bound:
            raise TreezeRuntimeError(
                f'Signal {message.signal!r} on widget {message.widget_id!r} '
                'is not exposed to browser events.'
            )

        # Browser-bound actions already ran in the browser event handler.
        await widget._get_signal(message.signal)._emit_async(
            message.args,
            message.kwargs or {},
            execute_actions=False,
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
        """Close the session and release pending outgoing updates."""
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

    def _clear_dirty_state(self, processed_widgets: set[Widget]) -> None:
        """Clean the completed batch without discarding changes made during rendering."""
        for widget in processed_widgets:
            if widget not in self._dirty_widgets:
                widget._mark_clean()
