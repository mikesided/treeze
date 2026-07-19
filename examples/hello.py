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
from treeze.widgets import Button, HLayout, VLayout, Window

# ______________________________________________________________________________________________________________________



class MyWindow(Window):
    
    def __init__(self, *args, **kwargs):
        super().__init__(layout=HLayout(spacing=15), *args, **kwargs)
        layout = self.layout
        #self.layout.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        #self.layout.horizontal_alignment = LayoutAlignment.START
        #self.layout.vertical_alignment = LayoutAlignment.START
        #self.layout.minimum_size = Size(500, 1500)

        self.layout_1 = VLayout(parent=self.layout, spacing=10)
        self.layout_2 = VLayout(parent=self.layout)

        self.btn_1 = Button(text='Button1', parent=self.layout_1)
        self.btn_2 = Button(text='Button2', parent=self.layout_1)
        self.btn_3 = Button(text='Button3', parent=self.layout_2)
        self.btn_4 = Button(text='Button4', parent=self.layout_2)

        #self.layout_1.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        #self.layout_1.minimum_size = Size(300, 600)
        for btn in [self.btn_1]:
            btn.size_policy = (SizePolicy.FIXED, SizePolicy.EXPANDING)

        self.btn_1.parent_changed.connect(self._on_btn_1_parent_changed)
        self.btn_3.clicked.connect(self._on_btn_3_clicked)


    def _on_btn_1_parent_changed(self, old, new):
        self.btn_1.text = 'Button1 CHANGED'
        self.btn_1.variant = Button.SUCCESS

    def _on_btn_3_clicked(self):
        self.btn_3.text = 'clicked'
        self.btn_3.variant = Button.SUCCESS
        self.layout_2.add_widget(self.btn_1)

app = App()
app.window = MyWindow

if __name__ == '__main__':
    app.run()