"""
Name:         server.py
Description:  HTTP Server

"""
# ______________________________________________________________________________________________________________________
# Imports
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from treeze.core import App
from treeze.core.enums import *
from treeze.core.exceptions import TreezeError
from treeze.core import *
from treeze.widgets import Button, VLayout, Window

# ______________________________________________________________________________________________________________________

CLIENT_DIR = Path(__file__).parent / "treeze" / "client"

server = FastAPI()
server.mount("/static", StaticFiles(directory=CLIENT_DIR), name='static')




class MyWindow(Window):
    
    def __init__(self, *args, **kwargs):
        super().__init__(layout=VLayout(), *args, **kwargs)
        layout = self.layout
        btn1 = Button(text='Click me', classes=['my_button'])
        btn1.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        btn1.variant = Variant.SECONDARY
        layout.add_widget(btn1)
        btn2 = Button(text='Don\'t click here')
        layout.add_widget(btn2, position=InsertPosition.FIRST)
        btn3 = Button(text='Click there')
        btn3.variant = Variant.MUTED
        layout.add_widget(btn3, index=1)
        layout.size_policy =(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        layout.minimum_size = Size(500, 500)
        layout.spacing = 10

app = App()
app.window = MyWindow

@server.get("/")
def index():
    return FileResponse(
        "treeze/client/index.html"
    )


@server.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    node_tree = app._build()
    await ws.send_json(node_tree.serialize())

    try:
        while True:
            message = await ws.receive_json()
            # Handle message
            node_tree = app._build()
            await ws.send_json(node_tree.serialize())        
            
    except TreezeError as e:
        print(e)
        await ws.send_json({
            'type': 'error',
            'message': str(e)
        })

    except Exception as e:
        print(e)
        await ws.send_json({
            'type': 'error',
            'message': 'Internal Treeze error'
        })