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
from treeze.widgets import Button, HLayout, VLayout, Window, Spacer, VSpacer, HSpacer, Label

# ______________________________________________________________________________________________________________________



class MyWindow(Window):
    
    def __init__(self, *args, **kwargs):
        super().__init__(layout=VLayout(spacing=15, size_policy=(SizePolicy.EXPANDING, SizePolicy.EXPANDING)), *args, **kwargs)
        self.layout.padding = 15

        self.header_layout = HLayout(parent=self.layout)
        self.header_layout.style = LayoutStyle.TRANSPARENT
        self.header_layout.size_policy = (SizePolicy.EXPANDING, SizePolicy.FIXED)

        self.main_layout = HLayout(parent=self.layout)
        self.main_layout.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)

        self.nav_layout = VLayout(parent=self.main_layout)
        self.nav_layout.size_policy = (SizePolicy.FIXED, SizePolicy.EXPANDING)
        self.nav_layout.vertical_alignment = LayoutAlignment.START

        self.body_layout = VLayout(parent=self.main_layout)
        self.body_layout.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)

        # Header Layout
        self.header_layout.add_widget(Button('Logo', classes=['my-button', 'my-button2']))
        self.header_layout.add_widget(Button('tab 1', style=ButtonStyle.GHOST))
        self.header_layout.add_widget(Button('tab 2', style=ButtonStyle.LINK))
        self.header_layout.add_widget(Button('tab 3', style=ButtonStyle.OUTLINED))
        self.header_layout.add_widget(Button('tab 4', style=ButtonStyle.FILLED))
        self.header_layout.add_widget(Button('tab 5', style=ButtonStyle.SOFT))
        self.header_layout.add_widget(HSpacer())
        self.header_layout.add_widget(Button('Refresh'))
        self.header_layout.add_widget(Button('Profile'))

        # Nav Layout
        self.nav_layout.add_widget(Button('Amazing list'))

        # Body layout
        btn = Button('Button 1')
        self.body_layout.add_widget(btn)
        self.body_layout.add_widget(Button('Button 2', style=ButtonStyle.OUTLINED))
        self.body_layout.add_widget(Button('Button 3'))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.BODY))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.BODY_SMALL))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.CAPTION))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.HEADING_1))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.HEADING_2))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.HEADING_3))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.OVERLINE))
        self.body_layout.add_widget(Label('hello world', style=LabelStyle.CODE))



app = App()
app.window = MyWindow

if __name__ == '__main__':
    app.run()