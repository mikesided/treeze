"""
Name:         server.py
Description:  Base class for runnable ASGI servers
"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

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