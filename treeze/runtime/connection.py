"""
Name:         connection.py
Description:  Connection Context Class to handle cookies

"""

# ______________________________________________________________________________________________________________________
# Imports

from typing import Any

from starlette.responses import Response
from starlette.websockets import WebSocket

# ______________________________________________________________________________________________________________________


class ConnectionContext:

    def __init__(self, websocket: WebSocket):
        self._websocket = websocket
        self._response = Response()
        self.state: dict[str, Any] = {}

    @property
    def cookies(self):
        return self._websocket.cookies

    @property
    def headers(self):
        return self._websocket.headers

    @property
    def query_params(self):
        return self._websocket.query_params

    def set_cookie(self, key: str, value: str, **kwargs) -> None:
        self._response.set_cookie(key, value, **kwargs)

    def delete_cookie(self, key: str, **kwargs) -> None:
        self._response.delete_cookie(key, **kwargs)

    def _accept_headers(self) -> list[tuple[bytes, bytes]]:
        return [
            (name, value)
            for name, value in self._response.raw_headers
            if name == b'set-cookie'
        ]