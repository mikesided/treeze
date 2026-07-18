"""
Name:         app.py
Description:  Main app class

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import TYPE_CHECKING
import uuid

from .enums import TreezeTheme
from .exceptions import TreezeTypeError, TreezeValueError
from .node import Node
from .server import Server
from ..runtime.session import SessionManager
from .types.theme import Theme
from .validation import Validator
from ..widgets.primitives.window import Window, _allow_window_construction

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
        self._id = uuid.uuid4().hex
        self._node_tree: Node | None = None
        self._window_class: type[Window] | None = None
        self._theme_preset: TreezeTheme = None
        self._theme = Theme()
        self._sessions: SessionManager = SessionManager(self)

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

        if not isinstance(window, type):
            raise TreezeTypeError('App window must be a Window class, not a Window instance.')

        if not issubclass(window, Window):
            raise TreezeTypeError('App window must inherit from Window.')

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
        self._theme_preset = Validator.ensure(theme, TreezeTheme)

    # ==========================================================================
    #  Session methods
    # ==========================================================================

    def _create_session(self):
        """Create a runtime session for one connected client."""
        return self._sessions._create_session()

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
        window = Validator.ensure(window, Window)

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