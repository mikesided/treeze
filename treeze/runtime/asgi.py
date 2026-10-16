"""
Name:         asgi.py
Description:  ASGI application factory
"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import traceback
import asyncio

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .protocol import (
    ServerDialogMessage,
    ServerRenderMessage,
)

from ..client.assets import STATIC_DIRECTORY
from ..client.index import render_index
from ..core.exceptions import TreezeError

from .connection import ConnectionContext
from .security import is_same_origin_websocket

if TYPE_CHECKING:
    from .session import Session
    from ..core.app import App

# ______________________________________________________________________________________________________________________


CLIENT_DIR = Path(__file__).parents[1] / 'client'

class CookieOperationRequest(BaseModel):
    session_id: str
    operation_id: str

def create_asgi_app(app: App) -> FastAPI:
    asgi_app = FastAPI()

    # Mount internal treeze static files
    asgi_app.mount(
        '/_treeze_static',
        StaticFiles(directory=STATIC_DIRECTORY),
        name='_treeze_static',
    )

    # Mount user-provided resources
    for name, rel_path in app.resources.items():
        abs_path = (app._app_dir / rel_path).resolve()
        if not abs_path.is_dir():
            continue

        asgi_app.mount(
            f'/{name}',
            StaticFiles(directory=abs_path),
            name=name,
        )


    @asgi_app.get('/', response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(
            content=render_index(),
        )

    @asgi_app.websocket('/ws')
    async def websocket(ws: WebSocket):

        session: Session | None = None
        sender: asyncio.Task | None = None
        accepted = False

        simulator = app.network_simulator
        send_lock = asyncio.Lock()

        async def simulated_receive():
            message = await ws.receive_json()
            if simulator is not None:
                await simulator.delay_one_way()

            return message

        async def simulated_send(message):
            async with send_lock:
                if simulator is not None:
                    await simulator.delay_one_way()

                await ws.send_json(message)

        try:
            if not is_same_origin_websocket(ws.headers):
                await ws.close(code=1008)
                return
            
            connection = ConnectionContext(ws)
            if app.session_initializer is not None:
                await app.session_initializer(connection)

            origin = ws.headers['origin']
            session = app._create_session(state=connection.state, origin=origin)
        
            node_tree = session._build()

            await ws.accept(headers=connection._accept_headers())

            accepted = True

            await simulated_send(
                ServerRenderMessage(
                    root=node_tree.serialize(),
                ).to_protocol_message().to_dict()
            )

            async def send_updates():
                while True:
                    await simulated_send(await session._outgoing.get())

            sender = asyncio.create_task(send_updates())

            while True:
                client_message = await simulated_receive()
                try:
                    patches = await session._handle_message(client_message)
                    session._publish_update(patches)
                except TreezeError as error:
                    session._pending_actions.clear()
                    print(traceback.format_exc())
                    await simulated_send(ServerDialogMessage(
                        level='error', title=type(error).__name__, message=str(error),
                    ).to_protocol_message().to_dict())

        except WebSocketDisconnect:
            return

        except TreezeError as error:
            print(traceback.format_exc())

            if accepted:
                await simulated_send(
                    ServerDialogMessage(
                        level='error',
                        title=type(error).__name__,
                        message=str(error),
                    ).to_protocol_message().to_dict()
                )
            else:
                await ws.close(code=1011)

        except Exception as error:
            print(traceback.format_exc())

            if accepted:
                await simulated_send(
                    ServerDialogMessage(
                        level='error',
                        title='Internal Treeze Error',
                        message='Treeze hit an internal error. Check the server logs.',
                        details=str(error),
                    ).to_protocol_message().to_dict()
                )
            else:
                await ws.close(code=1011)

        finally:
            if sender is not None:
                sender.cancel()
                await asyncio.gather(sender, return_exceptions=True)
            if session is not None:
                app._close_session(session)

    @asgi_app.post('/_treeze/session/cookie', include_in_schema=False)
    async def apply_cookie(payload: CookieOperationRequest, request: Request) -> Response:
        """
        HTTP endpoint to apply cookies

        NOTE: For multiple server workers, the HTTP Request must reach the same worker that owns the websocket
        """
        session = app._sessions._get_session(payload.session_id)
        if session is None or session.closed:
            raise HTTPException(status_code=404, detail='Unknown session.')
        
        # Reject cross-origin requests
        if (not session._origin or request.headers.get('origin') != session._origin):
            raise HTTPException(status_code=403, detail='Invalid request origin.')

        fetch_site = request.headers.get('sec-fetch-site')
        if fetch_site is not None and fetch_site != 'same-origin':
            raise HTTPException(status_code=403, detail='Cross-origin request rejected.')

        header = session._consume_cookie_operation(payload.operation_id)
        if header is None:
            raise HTTPException(status_code=404, detail='Invalid or expired cookie operation.')

        response = Response(status_code=204, headers={'Cache-Control': 'no-store'})
        response.raw_headers.append((b'set-cookie', header))
        return response

    return asgi_app
