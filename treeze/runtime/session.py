"""
Name:         session.py
Description:  Runtime session for one connected browser
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from functools import partial
from typing import Any, TYPE_CHECKING
from weakref import WeakSet, finalize, ref
import uuid
import secrets
import time
import traceback

from starlette.responses import Response

from .patch_engine import PatchEngine
from .protocol import ClientSignalMessage, ServerDialogMessage, ServerPatchesMessage, ServerCookieMessage

from ..core.exceptions import TreezeError, TreezeRuntimeError
from ..core.enums import BrowserEvent, InitMode
from ..core.node import Node
from ..core.client_action import ClientAction
from ..core.validation import Validator

from ..utils.ids import create_id_scope
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
        self._widgets: dict[str, Widget] = {}  # Only mounted widgets receive browser events
        self._created_at = datetime.now(timezone.utc)
        self._closed = False

        self._dirty_widgets: set[Widget] = set()
        self._patch_engine = PatchEngine()
        self._outgoing: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pending_actions: list[dict[str, Any]] = []
        self._cookie_operations: dict[str, tuple[float, bytes]] = {}
        self._message_lock = asyncio.Lock()
        self._window: Window | None = None
        self._pending_inits: WeakSet[Widget] = WeakSet()
        self._init_tasks: set[asyncio.Task] = set()
        self._sync_init_tasks: set[asyncio.Task] = set()
        self._init_changed = asyncio.Event()
        self._published = False
        self._update_task: asyncio.Task | None = None

        self.id_scope = create_id_scope()

        with use_session(self):
            # Session contains one main initialized window (generated from the app)
            self._window = app._create_window()
            self._register_subtree(self._window)
            self._start_initializations()

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

    async def _build(self) -> Node:
        """Build this session's current node tree."""
        if self.closed:
            raise TreezeRuntimeError('Cannot build a closed session.')

        with use_session(self):
            await self._wait_for_initialization()
            if self.closed:
                raise TreezeRuntimeError('Cannot build a closed session.')
            processed_widgets = self._dirty_widgets
            self._dirty_widgets = set()
            try:
                node_tree = self.app._build_window(self.window)
                self._patch_engine.capture_tree(node_tree)
            except BaseException:
                self._dirty_widgets.update(processed_widgets)
                raise
            self._clear_dirty_state(processed_widgets)

        return node_tree

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Await a client's callbacks; dirty changes schedule their own updates."""
        message = Validator.ensure(message, dict, attr_name='Session._handle_message(message=...)')
        message_type = Validator.ensure(message.get('type'), str, attr_name='client.signal.type')
        payload = Validator.ensure(message.get('payload'), dict, attr_name='client.signal.payload')

        # One session is sequential; other sessions have their own lock.
        async with self._message_lock:
            if self.closed:
                raise TreezeRuntimeError('Cannot handle messages on a closed session.')
            with use_session(self):
                if message_type != 'client.signal':
                    raise TreezeRuntimeError(f'Unsupported client message type: {message_type!r}.')
                signal_message = ClientSignalMessage.from_payload(payload)
                try:
                    await self._handle_signal_message(signal_message)
                except BaseException:
                    self._pending_actions.clear()
                    raise

    def _initialize_widget(self, widget: Widget) -> None:
        """Schedule construction's one-time hook, including for parentless widgets."""
        widget._init_started = True
        if self.closed:
            return
        self._pending_inits.add(widget)
        if self._window is not None:
            self._start_initializations()

    def _start_initializations(self) -> None:
        if not self._pending_inits:
            return
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # Sessions constructed outside the event loop start hooks at _build().
            return
        for widget in tuple(self._pending_inits):
            self._pending_inits.discard(widget)
            task = asyncio.create_task(self._run_init(ref(widget)))
            widget._init_task = task
            self._init_tasks.add(task)
            finalizer = finalize(widget, task.cancel)
            task.add_done_callback(partial(self._finish_init, finalizer=finalizer))
            if widget.init_mode is InitMode.SYNCHRONOUS and self._widgets.get(widget.id) is widget:
                self._sync_init_tasks.add(task)

    async def _run_init(self, widget_ref: ref[Widget]) -> None:
        widget = widget_ref()
        if widget is None:
            return
        with use_session(self):
            try:
                await widget.on_init()
            except Exception as error:
                self._report_error(error)
            finally:
                widget._init_task = None

    def _finish_init(self, task: asyncio.Task, *, finalizer: finalize) -> None:
        finalizer.detach()
        self._init_tasks.discard(task)
        if task in self._sync_init_tasks:
            self._sync_init_tasks.remove(task)
            self._init_changed.set()

    async def _wait_for_initialization(self) -> None:
        """Only unfinished synchronous initializers in the published tree can delay it."""
        self._start_initializations()
        while self._sync_init_tasks:
            self._init_changed.clear()
            await self._init_changed.wait()

    def _start(self) -> None:
        """Allow patches only after the initial render has been sent."""
        self._published = True
        self._publish_update([])
        if self._dirty_widgets:
            self._request_update()

    def _request_update(self) -> None:
        if self.closed or not self._published or self._update_task is not None:
            return
        self._update_task = asyncio.create_task(self._flush_updates())

    async def _flush_updates(self) -> None:
        try:
            async with self._message_lock:
                with use_session(self):
                    await self._wait_for_initialization()
                    if self.closed:
                        return
                    processed_widgets = self._dirty_widgets
                    self._dirty_widgets = set()
                    try:
                        patches = self._patch_engine.create_patches_for_dirty_widgets(processed_widgets)
                    except BaseException:
                        self._dirty_widgets.update(processed_widgets)
                        raise
                    self._clear_dirty_state(processed_widgets)
                    self._publish_update(patches)
        except Exception as error:
            self._pending_actions.clear()
            self._report_error(error)
            return
        finally:
            self._update_task = None
        if self._dirty_widgets:
            self._request_update()

    def _report_error(self, error: Exception) -> None:
        """Report background failures through the existing error dialog protocol."""
        print(traceback.format_exc())
        if not self.closed:
            self._outgoing.put_nowait(ServerDialogMessage(
                level='error',
                title=type(error).__name__ if isinstance(error, TreezeError) else 'Internal Treeze Error',
                message=str(error) if isinstance(error, TreezeError) else 'Treeze hit an internal error. Check the server logs.',
                details=None if isinstance(error, TreezeError) else str(error),
            ).to_protocol_message().to_dict())

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
        self._pending_actions.append(payload)
        self._request_update()

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

    def _register_subtree(self, root: Widget) -> None:
        """Mount only this subtree; session ownership never transfers."""
        widgets = tuple(root._walk_widgets())
        for widget in widgets:
            widget._set_session(self)
        for widget in widgets:
            self._widgets[widget.id] = widget
            if widget._is_dirty:
                self._dirty_widgets.add(widget)
            task = widget._init_task
            if widget.init_mode is InitMode.SYNCHRONOUS and task is not None and not task.done():
                self._sync_init_tasks.add(task)
        for widget in widgets:
            for source in widget._sync_triggers:
                source._mark_dirty()

    def _unregister_subtree(self, root: Widget) -> None:
        widgets = tuple(root._walk_widgets())
        for widget in widgets:
            self._widgets.pop(widget.id, None)
            self._dirty_widgets.discard(widget)
            task = widget._init_task
            if task in self._sync_init_tasks:
                self._sync_init_tasks.remove(task)
                self._init_changed.set()
        for widget in widgets:
            for source in widget._sync_triggers:
                source._mark_dirty()

    def _close(self) -> None:
        """Close the session and release pending outgoing updates."""
        if self.closed:
            return
        self._closed = True
        if self._update_task is not None:
            self._update_task.cancel()
        for task in self._init_tasks:
            task.cancel()
        self._init_tasks.clear()
        self._sync_init_tasks.clear()
        self._pending_inits.clear()
        self._init_changed.set()
        self._widgets.clear()
        self._window = None
        self._patch_engine = PatchEngine()
        self._dirty_widgets.clear()
        self._pending_actions.clear()
        self._cookie_operations.clear()
        while not self._outgoing.empty():
            self._outgoing.get_nowait()

    def _mark_widget_dirty(self, widget: Widget) -> None:
        if self.closed or self._widgets.get(widget.id) is not widget:
            return

        self._dirty_widgets.add(widget)
        self._request_update()

    def _clear_dirty_state(self, processed_widgets: set[Widget]) -> None:
        """Clean the completed batch without discarding changes made during rendering."""
        for widget in processed_widgets:
            if widget not in self._dirty_widgets:
                widget._mark_clean()
