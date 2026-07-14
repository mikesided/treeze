"""
Name:         asgi.py
Description:  ASGI application factory
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .protocol import ServerDialogMessage, ServerRenderMessage

from ..core.exceptions import TreezeError

if TYPE_CHECKING:
    from .session import Session
    from ..core.app import App


CLIENT_DIR = Path(__file__).parents[1] / 'client'


def create_asgi_app(app: App) -> FastAPI:
    asgi_app = FastAPI()

    asgi_app.mount(
        '/static',
        StaticFiles(directory=CLIENT_DIR),
        name='static',
    )

    @asgi_app.get('/')
    def index():
        return FileResponse(CLIENT_DIR / 'index.html')

    @asgi_app.websocket('/ws')
    async def websocket(ws: WebSocket):
        await ws.accept()

        session: Session | None = None

        try:

            session = app._create_session()
        
            node_tree = session._build()

            await ws.send_json(
                ServerRenderMessage(
                    root=node_tree.serialize(),
                ).to_protocol_message().to_dict()
            )

            while True:
                client_message = await ws.receive_json()

                try:
                    session._handle_message(client_message)

                    node_tree = session._build()

                    await ws.send_json(
                        ServerRenderMessage(
                            root=node_tree.serialize(),
                        ).to_protocol_message().to_dict()
                    )

                except TreezeError as error:
                    print(traceback.format_exc())
                    
                    await ws.send_json(
                        ServerDialogMessage(
                            level='error',
                            title=type(error).__name__,
                            message=str(error),
                        ).to_protocol_message().to_dict()
                    )

        except WebSocketDisconnect:
            return

        except TreezeError as error:
            print(traceback.format_exc())
            await ws.send_json(
                ServerDialogMessage(
                    level='error',
                    title=type(error).__name__,
                    message=str(error),
                ).to_protocol_message().to_dict()
            )

        except Exception as error:
            print(traceback.format_exc())
            await ws.send_json(
                ServerDialogMessage(
                    level='error',
                    title='Internal Treeze Error',
                    message='Treeze hit an internal error. Check the server logs.',
                    details=str(error),
                ).to_protocol_message().to_dict()
            )

        finally:
            if session is not None:
                app._close_session(session)

    return asgi_app