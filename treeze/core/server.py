"""
Name:         server.py
Description:  Base class for runnable ASGI servers
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from .validation import Validator
from .exceptions import TreezeTypeError, TreezeValueError

# ______________________________________________________________________________________________________________________


class Server(ABC):

    def __init__(self):
        self._asgi_app: Any | None = None

    async def __call__(self, scope, receive, send):
        """
        Allows this object to be used directly as an ASGI app.

        Example:
            uvicorn main:app --reload
        """
        await self._get_asgi_app()(scope, receive, send)

    def run(
            self,
            host: str = '127.0.0.1',
            port: int = 8000,
        ) -> None:
        """Run the server directly."""
        Validator.ensure(host, str, attr_name='Server.run(host=...)')
        Validator.ensure(port, int, attr_name='Server.run(port=...)')
        if isinstance(port, bool):
            raise TreezeTypeError('Server.run(port=...): cannot be a boolean.')
        if not 0 <= port <= 65535:
            raise TreezeValueError('Server.run(port=...): must be between 0 and 65535.')
        import uvicorn

        uvicorn.run(
            self,
            host=host,
            port=port,
        )

    def _get_asgi_app(self):
        if self._asgi_app is None:
            self._asgi_app = self._create_asgi_app()

        return self._asgi_app

    @abstractmethod
    def _create_asgi_app(self):
        """Create the internal ASGI app."""
        raise NotImplementedError