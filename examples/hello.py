"""
Name:         hello.py
Description:  Example

"""
# ______________________________________________________________________________________________________________________
# Imports
import sys
from pathlib import Path

# Make sure treeze is in the environment
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from treeze.core import App
from treeze.core.enums import *
from treeze.core.exceptions import TreezeError
from treeze.core import *
from treeze.widgets import Button, VLayout, Window

# ______________________________________________________________________________________________________________________



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

        btn1.clicked.connect(on_clicked)

def on_clicked(*args, **kwargs):
    print(args)
    print(kwargs)

app = App()
app.window = MyWindow

if __name__ == '__main__':
    app.run()