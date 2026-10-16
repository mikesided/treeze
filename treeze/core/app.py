"""
Name:         app.py
Description:  Main app class

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
import inspect
from pathlib import Path
from typing import TYPE_CHECKING
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from ..runtime.session import SessionManager
from ..runtime.connection import ConnectionContext
from ..runtime.network_simulator import NetworkSimulator
from ..widgets.primitives.window import Window, _allow_window_construction

from .enums import TreezeTheme
from .exceptions import TreezeTypeError, TreezeValueError
from .node import Node
from .server import Server
from .types.theme import Theme
from .validation import Validator


if TYPE_CHECKING:
    from ..widgets.primitives.window import Window

# ______________________________________________________________________________________________________________________


class App(Server):

    def __init__(
            self,
            window: type[Window] | None = None,
            theme_preset: TreezeTheme = TreezeTheme.TREEZE
        ):
        super().__init__()
        self._app_dir = Path(inspect.stack(context=0)[1].filename).resolve().parent
        self._id = uuid.uuid4().hex
        self._node_tree: Node | None = None
        self._window_class: type[Window] | None = None
        self._theme_preset: TreezeTheme = None
        self._theme = Theme()
        self._resources: dict[str] = {'resources': 'resources'}
        self._sessions: SessionManager = SessionManager(self)
        self._session_initializer: (Callable[[ConnectionContext], Awaitable[None]] | None) = None
        self._network_simulator: NetworkSimulator | None = None
        self._allowed_origins: list[str] | None = None

        self.theme_preset = theme_preset
        self.window = window

    # ==========================================================================
    #  Properties
    # ==========================================================================

    @property
    def id(self) -> str:
        return self._id

    @property
    def window(self) -> type[Window] | None:
        """
        The Window class used by the app.

        This must be a Window class, not a Window instance.
        """
        return self._window_class

    @window.setter
    def window(self, window: type[Window] | None):
        if window is None:
            self._window_class = None
            return

        Validator.ensure(window, type, attr_name='App.window')

        if not issubclass(window, Window):
            raise TreezeTypeError('App.window: must be a class inheriting from Window.')

        self._window_class = window

    @property
    def theme(self) -> Theme:
        """Read only"""
        return self._theme
    
    @property
    def theme_preset(self) -> TreezeTheme:
        return self._theme_preset
    
    @theme_preset.setter
    def theme_preset(self, theme: TreezeTheme):
        """
        Holds the theme to be used by the app.
        Override granularly through `self.theme`
        """
        self._theme_preset = Validator.ensure(theme, TreezeTheme, attr_name='App.theme_preset')

    @property
    def session_initializer(self) -> Callable[[ConnectionContext], Awaitable[None]] | None:
        return self._session_initializer

    @session_initializer.setter
    def session_initializer(self, initializer: Callable[[ConnectionContext], Awaitable[None]] | None):
        if initializer is not None and not callable(initializer):
            raise TreezeTypeError('App.session_initializer must be callable or None.')

        self._session_initializer = initializer

    @property
    def network_simulator(self) -> NetworkSimulator | None:
        return self._network_simulator

    @network_simulator.setter
    def network_simulator(self, network_simulator: NetworkSimulator | None) -> None:
        self._network_simulator = Validator.ensure(
            network_simulator, NetworkSimulator, None, attr_name='App.network_simulator'
        )

    @property
    def allowed_origins(self) -> tuple[str, ...] | None:
        return self._allowed_origins

    @allowed_origins.setter
    def allowed_origins(self, origins: list[str] | tuple[str, ...] | None) -> None:
        if origins is not None:
            Validator.ensure(origins, list, tuple, None, attr_name='App.allowed_origins')

            if not all(isinstance(origin, str) for origin in origins):
                raise TreezeTypeError('Every allowed origin must be a string.')

            origins = tuple(origins)

        self._allowed_origins = origins

    @property
    def resources(self) -> dict[str, str]:
        return self._resources

    @resources.setter
    def resources(self, resources: dict[str, str]):
        """
        Sets the available resource dirs and their name.

        The key represents the name of the resource. The name will explose http://my-app.com/{name}
        The value represents a relative path to the main file running the App()
        """
        Validator.ensure(resources, dict, attr_name='App.resources')
        for key, value in resources.items():
            Validator.ensure(key, str, attr_name=f'App.resources.keys[{key!r}]')
            Validator.ensure(value, str, attr_name=f'App.resources[{key!r}]')
        self._resources = resources


    # ==========================================================================
    #  Session methods
    # ==========================================================================

    def _create_session(self, state: dict[str, Any] | None = None, origin: str | None = None):
        """Create a runtime session for one connected client."""
        return self._sessions._create_session(state=state, origin=origin)

    def _close_session(self, session) -> None:
        """Close a runtime session."""
        self._sessions._close_session(session)


    # ==========================================================================
    #  Internal methods
    # ==========================================================================

    def _create_window(self) -> Window:
        """
        Create a new window instance.
        Apps are assigned a window class, and instanced through here.
        """
        if self.window is None:
            raise TreezeValueError('App has no window.')

        with _allow_window_construction():
            return self.window()

    # ==========================================================================
    #  Rendering methods
    # ==========================================================================

    def _styles(self) -> dict[str, str]:
        return self.theme._to_css_variables()

    def _classes(self) -> list[str]:
        return [
            'tz-app',
            f'tz-theme-{self.theme_preset.value}',
        ]

    def _build_window(self, window: Window) -> Node:
        """
        Build the app node tree around an existing window.

        This is used by the runtime so each websocket/session can keep its own
        window instance.
        """
        window = Validator.ensure(window, Window, attr_name='App._build_window(window=...)')

        node_tree = Node(
            id=self.id,
            tag='div',
            classes=self._classes(),
            styles=self._styles(),
        )

        node_tree.add_child(window._build())

        return node_tree
    
    # ==========================================================================
    #  Server methods
    # ==========================================================================

    def _create_asgi_app(self):
        from ..runtime.asgi import create_asgi_app

        return create_asgi_app(self)
