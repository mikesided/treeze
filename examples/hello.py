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
        self.btn1 = Button(text='Click me', classes=['my_button'])
        self.btn1.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        self.btn1.variant = Variant.SECONDARY
        layout.add_widget(self.btn1)
        self.btn2 = Button(text='Don\'t click here')
        layout.add_widget(self.btn2, position=InsertPosition.FIRST)
        self.btn3 = Button(text='Click there')
        self.btn3.variant = Variant.MUTED
        layout.add_widget(self.btn3, index=1)
        layout.size_policy =(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        layout.minimum_size = Size(500, 500)
        layout.spacing = 10
        self.btn_4 = Button(text='hello', classes=['--class-hello'])

        self.btn1.clicked.connect(lambda: self.on_btn1_clicked(self.btn1))
        #self.btn2.clicked.connect(self.on_btn2_clicked)
        #self.btn3.clicked.connect(self.on_btn3_clicked)

    def on_btn1_clicked(self, btn):
        btn.text = 'asdf'
        btn.variant = Variant.SUCCESS

        self.btn_4.text = 'hello world'
        self.layout.add_widget(self.btn_4)
        self.btn_4.text = 'hello world2'
        #self.btn_4.remove_class('--class-hello')

    def on_btn2_clicked(self):
        pass

    def on_btn3_clicked(self):
        self.btn3.test_signal.emit('asdf')

app = App()
app.window = MyWindow

if __name__ == '__main__':
    app.run()