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
import secrets
import time

from starlette.responses import Response

from .patch_engine import PatchEngine
from .protocol import ClientSignalMessage, ServerActionsMessage, ServerPatchesMessage, ServerCookieMessage

from ..core.exceptions import TreezeError, TreezeRuntimeError
from ..core.enums import BrowserEvent
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

_COOKIE_OPERATION_TTL = 30.0
class SessionManager:

    def __init__(self, app: App):
        self._app = app
        self._sessions: dict[str, Session] = {}

    # ==========================================================================
    #  Internal methods
    # ==========================================================================

    def _create_session(self, state: dict[str, Any] | None = None, origin: str | None = None) -> Session:
        session = Session(self._app, state=state, origin=origin)
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

    def __init__(self, app: App, state: dict[str, Any] | None = None, origin: str | None = None):
        self._id = uuid.uuid4().hex
        self._app = app
        self._state = dict(state) if state is not None else {}
        self._origin = origin
        self._widgets: dict[str, Widget] = {}  # Widgets are walked & stored here for lookup by events
        self._created_at = datetime.now(timezone.utc)
        self._closed = False

        self._dirty_widgets: set[Widget] = set()
        self._patch_engine = PatchEngine()
        self._outgoing: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pending_actions: list[dict[str, Any]] = []
        self._cookie_operations: dict[str, tuple[float, bytes]] = {}
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
    def state(self) -> dict[str, Any]:
        """Application-defined state for this browser session."""
        return self._state

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
    # Public methods
    # ==========================================================================

    def set_cookie(self, key: str, value: str, **kwargs) -> None:
        """Request the browser to set a cookie."""
        response = Response()
        response.set_cookie(key, value, **kwargs)
        self._queue_cookie_response(response)

    def delete_cookie(self, key: str, **kwargs) -> None:
        """Request the browser to delete a cookie."""
        response = Response()
        response.delete_cookie(key, **kwargs)
        self._queue_cookie_response(response)

    # ==========================================================================
    #  Internal Methods
    # ==========================================================================

    def _build(self) -> Node:
        """Build this session's current node tree."""
        if self.closed:
            raise TreezeRuntimeError('Cannot build a closed session.')

        with use_session(self), use_id_scope(self.id_scope):
            self._index_widgets()
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
                self._index_widgets()
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

        if self.closed or widget._session is not self:
            raise TreezeRuntimeError('Cannot handle an event outside the active session.')
        if not widget._is_enabled_in_tree():
            return
        bindings = widget._node.events if widget._node is not None else {}
        if message.browser_event is not None:
            try:
                event = BrowserEvent(message.browser_event)
            except ValueError:
                raise TreezeRuntimeError('Unknown browser event.') from None
            binding = bindings.get(event)
        else:
            matches = [(event, binding) for event, binding in bindings.items() if binding.signal == message.signal]
            if not matches or (len(matches) > 1 and (
                message.sync is not None or any(widget._active_sync_targets(event) for event, _ in matches)
            )):
                raise TreezeRuntimeError('Client signal does not identify a unique browser event.')
            event, binding = matches[0]
        if binding is None or binding.signal != message.signal:
            raise TreezeRuntimeError('Signal is not exposed for this browser event.')

        if message.signal is not None:
            try:
                widget._get_signal(message.signal)._validate_emit_arguments(message.args, message.kwargs or {})
            except TreezeError:
                # Event arguments may contain password text; never include values.
                raise TreezeRuntimeError('Invalid browser signal arguments.') from None
        elif message.args or message.kwargs:
            raise TreezeRuntimeError('An event without a signal cannot supply signal arguments.')

        targets = widget._active_sync_targets(event)
        values = message.sync if message.sync is not None else {}
        if set(values) != set(targets):
            raise TreezeRuntimeError('Synchronization payload does not match registered widgets.')
        validated = [(target, target._validate_sync_value(values[target_id])) for target_id, target in targets.items()]

        # Validate every value before changing any state. Acknowledging the browser
        # values also prevents unrelated renders from echoing stale values back.
        for target, value in validated:
            target._apply_sync_value(value)
            properties = {target._SYNC_PROPERTY: value}
            if target._node is not None:
                target._node.properties.update(properties)
            self._patch_engine.acknowledge_properties(target.id, properties)

        if message.signal is not None:
            # Browser-bound actions already ran in the browser event handler.
            await widget._get_signal(message.signal)._emit_async(
                message.args, message.kwargs or {}, execute_actions=False,
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

    def _queue_cookie_response(self, response: Response) -> None:
        if self.closed:
            raise TreezeRuntimeError('Cannot modify cookies on a closed session.')

        header = next((value for name, value in response.raw_headers if name == b'set-cookie'), None)

        if header is None:
            raise TreezeRuntimeError('Cookie response has no Set-Cookie header.')

        now = time.monotonic()

        # Discard expired operations
        for operation_id, (expires_at, _) in tuple(self._cookie_operations.items()):
            if expires_at <= now:
                self._cookie_operations.pop(operation_id, None)

        if len(self._cookie_operations) >= 32:
            raise TreezeRuntimeError('Too many pending cookie operations.')

        operation_id = secrets.token_urlsafe(32)

        self._cookie_operations[operation_id] = (now + _COOKIE_OPERATION_TTL, header)

        message = ServerCookieMessage(
            session_id=self.id,
            operation_id=operation_id,
        )

        try:
            self._outgoing.put_nowait(message.to_protocol_message().to_dict())
        except BaseException:
            self._cookie_operations.pop(operation_id, None)
            raise

    def _consume_cookie_operation(self, operation_id: str) -> bytes | None:
        """Consume a one-time cookie operation."""

        operation = self._cookie_operations.pop(operation_id, None)

        if operation is None or self.closed:
            return None

        expires_at, header = operation

        if time.monotonic() >= expires_at:
            return None

        return header

    def _index_widgets(self) -> None:
        """Walk all widgets of the app and store them on self for reference"""
        previous = self._widgets
        self._widgets = {}

        for widget in self.window._walk_widgets():
            widget._set_session(self)
            self._widgets[widget.id] = widget

        for widget_id, widget in previous.items():
            if self._widgets.get(widget_id) is not widget:
                widget._clear_sync_registrations()
                widget._set_session(None)
                self._dirty_widgets.discard(widget)
        for widget in self._widgets.values():
            for event in widget._sync_targets:
                targets = widget._active_sync_targets(event)
                binding = widget._node.events.get(event) if widget._node is not None else None
                expected = {target.id: target._SYNC_PROPERTY for target in targets.values()}
                if expected != (binding.sync if binding is not None else {}):
                    widget._mark_dirty()

    def _close(self) -> None:
        """Close the session and release pending outgoing updates."""
        if self.closed:
            return
        self._closed = True
        for widget in tuple(self._widgets.values()):
            widget._clear_sync_registrations()
            widget._set_session(None)
        self._widgets.clear()
        self._dirty_widgets.clear()
        self._pending_actions.clear()
        self._cookie_operations.clear()
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
