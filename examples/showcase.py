"""
Name:         showcase.py
Description:  Treeze feature showcase / demo application.

This example intentionally uses only APIs currently present on the public
`main` branch of mikesided/treeze.
"""
# ______________________________________________________________________________________________________________________
# Imports
import sys
from pathlib import Path
from functools import partial
from textwrap import dedent
import random

# Make sure treeze is in the environment when running this file directly
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from treeze.core import App
from treeze.core.enums import (
    ButtonStyle,
    Color,
    InsertPosition,
    LabelStyle,
    LayoutAlignment,
    LayoutStyle,
    LineStyle,
    SizePolicy,
    TreezeTheme,
    Variant,
)
from treeze.core.signals import Signal
from treeze.core.types.size import Size
from treeze.core.types.gradients import LinearGradient
from treeze.widgets import (
    Button,
    HLayout,
    HSpacer,
    Label,
    VLine,
    HLine,
    Image,
    Spacer,
    VLayout,
    VSpacer,
    Window,
)

# ______________________________________________________________________________________________________________________

class ShowcaseWindow(Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = VLayout()

        # Header Widgets
        self.lbl_title = Label(text='Treeze', style=LabelStyle.HEADING_1, variant=Variant.PRIMARY)
        self.lbl_subtitle = Label(text='Python-first retained-mode UI rendered in the browser', style=LabelStyle.CAPTION)
        self.btn_profile = Button(text='Profile', style=ButtonStyle.SOFT, variant=Variant.INFO, fixed_width=150)

        # Navigation Widgets
        self.btn_home = Button('Home', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_layouts = Button('Layouts', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_patches = Button('Patches', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_signals = Button('Signals', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_styles = Button('Styles', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_variants = Button('Variants', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_button = Button('Button', horizontal_size_policy=SizePolicy.EXPANDING)
        self.btn_label = Button('Label', horizontal_size_policy=SizePolicy.EXPANDING)

        # Content Widgets
        self.container_content = HLayout(size_policy=(SizePolicy.EXPANDING, SizePolicy.EXPANDING), maximum_width=1000)

        # Footer Widgets

        # Constructors
        self._build_header(parent=self.layout)
        self._build_body(parent=self.layout)
        self._build_footer(parent=self.layout)

        # Connections
        #for widget in self.layout_sidebar.children:
        #    if isinstance(widget, Button):
        #        widget.horizontal_size_policy = SizePolicy.EXPANDING
        #        widget.clicked.connect(partial(self._on_nav_button_clicked, widget))

        # Init
        self.btn_home.clicked.emit()

    # ==================================================================================================================
    #  Constructors
    # ==================================================================================================================
    
    def _build_header(self, parent=None):
        self.layout_header = HLayout(
            spacing=8,
            padding=(10, 50, 10, 50),
            variant=Variant.TERTIARY,
            horizontal_size_policy=SizePolicy.EXPANDING,
            parent=parent,
        )
        self.layout_header.add_widget(self.lbl_title)
        self.layout_header.add_widget(Spacer(fixed_width=50))
        self.layout_header.add_widget(self.lbl_subtitle)
        self.layout_header.add_widget(VLine())
        self.layout_header.add_widget(HSpacer())
        self.layout_header.add_widget(self.btn_profile)

        return self.layout_header

    def _build_body(self, parent=None):
        self.layout_body = HLayout(
            spacing=25,
            padding=(15, 25, 15, 25),
            size_policy=(SizePolicy.EXPANDING, SizePolicy.EXPANDING),
            horizontal_alignment=LayoutAlignment.CENTER,
            parent=parent,
        )

        self._build_sidebar(parent=self.layout_body)

        self.layout_body.add_widget(self.container_content)


        return self.layout_body

    def _build_sidebar(self, parent=None) -> VLayout:
        self.layout_sidebar = VLayout(spacing=8, padding=10, style=LayoutStyle.PANEL, parent=parent)
        self.layout_sidebar.size_policy = (SizePolicy.FIXED, SizePolicy.EXPANDING)
        self.layout_sidebar.fixed_width = 220
        self.layout_sidebar.minimum_height = 500

        self.layout_sidebar.add_widget(Label(text='Navigation', style=LabelStyle.HEADING_3, variant=Variant.MUTED))
        self.layout_sidebar.add_widget(self.btn_home)
        self.layout_sidebar.add_widget(Spacer(fixed_height=15))
        self.layout_sidebar.add_widget(Label(text='Features', style=LabelStyle.BODY_SMALL, variant=Variant.MUTED))
        self.layout_sidebar.add_widget(self.btn_layouts)
        self.layout_sidebar.add_widget(self.btn_patches)
        self.layout_sidebar.add_widget(self.btn_signals)
        self.layout_sidebar.add_widget(self.btn_styles)
        self.layout_sidebar.add_widget(self.btn_variants)
        self.layout_sidebar.add_widget(Spacer(fixed_height=15))
        self.layout_sidebar.add_widget(Label(text='Primitive Widgets', style=LabelStyle.BODY_SMALL, variant=Variant.MUTED))
        self.layout_sidebar.add_widget(self.btn_button)
        self.layout_sidebar.add_widget(self.btn_label)
        self.layout_sidebar.add_widget(Spacer(fixed_height=15))
        self.layout_sidebar.add_widget(Label(text='Complex Widgets', style=LabelStyle.BODY_SMALL, variant=Variant.MUTED))
        self.layout_sidebar.add_widget(Label(text='Coming soon..', style=LabelStyle.CAPTION, variant=Variant.MUTED))
        self.layout_sidebar.add_widget(VSpacer())

        for widget in self.layout_sidebar.children:
            if isinstance(widget, Button):
                widget.horizontal_size_policy = SizePolicy.EXPANDING
                widget.clicked.connect(partial(self._on_nav_button_clicked, widget, LabelWidget))

        return self.layout_sidebar
    
    def _build_footer(self, parent=None):        
        self.layout_footer = HLayout(
            spacing=8,
            padding=(8, 50, 8, 50),
            variant=Variant.MUTED,
            horizontal_size_policy=SizePolicy.EXPANDING,
            parent=parent,
        )

        self.layout_footer.add_widget(Label(text='Treeze is currently under development', variant=Variant.MUTED))
        self.layout_footer.add_widget(HSpacer())
        self.layout_footer.add_widget(Button(text='https://github.com/mikesided/treeze', style=ButtonStyle.LINK))
        return self.layout_footer

    # ==================================================================================================================
    #   Callbacks
    # ==================================================================================================================

    def _on_nav_button_clicked(self, button, widget_class):
        # Reset button states
        for child in self.layout_sidebar.children:
            if isinstance(child, Button):
                child.variant = Variant.DEFAULT

        button.variant = Variant.PRIMARY

        # Clear content widget
        for child in reversed(self.container_content.children):
            self.container_content.remove_widget(child)

        # Add new content widget
        widget_class = globals()[f'{button.text}Widget']
        widget_class(parent=self.container_content)


class ContentWidget(VLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size_policy = (SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        self.style = LayoutStyle.PANEL
        self.padding = 25
        self.spacing = 5
        self.horizontal_alignment = LayoutAlignment.START
        self.vertical_alignment = LayoutAlignment.START


class HomeWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.horizontal_alignment = LayoutAlignment.CENTER

        self.add_widget(Label('Welcome to treeze\'s showcase page!', style=LabelStyle.HEADING_1))


class LayoutsWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_widget(Label('Widget -> Container -> HLayout', style=LabelStyle.HEADING_1))
        self.add_widget(Label('Widget -> Container -> VLayout', style=LabelStyle.HEADING_1))

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Layouts can contain other widgets.'))
        self.add_widget(Label('They are mainly controlled with bi-axis sizepolicies and alignments'))

        # Signals
        self.add_widget(Label('Signals', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('None'))
        
        # Styles
        self.add_widget(Label('Styles', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        layout_dark = VLayout(
            size_policy=(SizePolicy.EXPANDING, SizePolicy.PREFERRED), 
            horizontal_alignment=LayoutAlignment.CENTER, 
            padding=10, 
            variant=Variant.MUTED,
            spacing=5,
            parent=self
        )
        for style in LayoutStyle:
            HLayout(style=style, parent=layout_dark, minimum_size=Size(250, 50)).add_widget(Label(style.name))


class PatchesWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Patches are how the framework retains its data. Only the required changes are patched on the rendered application.'))

        # Example
        self.add_widget(Label('Examples', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Here\'s an example of a dynamic system that relies on patching to not override previous widget states.'))
        self.add_widget(Label('Note that once a widget is created/modified/removed, no other widgets receive a fresh render'))
        self.add_widget(Spacer(fixed_width=25))

        self.layout_example_header = HLayout(spacing=5, parent=self)
        self.btn_add = Button('Add new widget', parent=self.layout_example_header)
        self.btn_transfer = Button('Move the first widget', parent=self.layout_example_header)
        self.btn_remove = Button('Remove a random widget', parent=self.layout_example_header)
        self.btn_rename = Button('Transform a random widget', parent=self.layout_example_header)
        self.btn_clear = Button('Clear all widgets', parent=self.layout_example_header)

        self.layout_example = HLayout(spacing=15, style=LayoutStyle.PANEL, horizontal_size_policy=SizePolicy.EXPANDING, parent=self)
        self.layout_left = VLayout(spacing=5, horizontal_size_policy=SizePolicy.EXPANDING, parent=self.layout_example)
        self.layout_right = VLayout(spacing=5, horizontal_size_policy=SizePolicy.EXPANDING, parent=self.layout_example)

        # Connections
        self.btn_add.clicked.connect(self._on_btn_add_clicked)
        self.btn_clear.clicked.connect(self._on_btn_clear_clicked)
        self.btn_remove.clicked.connect(self._on_btn_remove_clicked)
        self.btn_rename.clicked.connect(self._on_btn_rename_clicked)
        self.btn_transfer.clicked.connect(self._on_btn_transfer_clicked)

    def get_random_widget(self):        
        count = len(self.layout_left.children) + len(self.layout_right.children)
        if count == 0:
            return
        
        number = random.randint(1, count)
        if number > len(self.layout_left.children):
            index = number - len(self.layout_left.children) - 1
            layout = self.layout_right
        else:
            index = number - 1
            layout = self.layout_left

        widget = layout.children[index]
        return widget


    def _on_btn_add_clicked(self):
        button = Button(text='Hello world', parent=self.layout_left)

    def _on_btn_remove_clicked(self):
        widget = self.get_random_widget()
        if widget:
            widget.parent.remove_widget(widget)

    def _on_btn_clear_clicked(self):
        for child in reversed(self.layout_left.children):
            self.layout_left.remove_widget(child)
        for child in reversed(self.layout_right.children):
            self.layout_right.remove_widget(child)

    def _on_btn_rename_clicked(self):
        widget = self.get_random_widget()
        if not widget:
            return

        widget.text = 'Transformed!'
        widget.style = ButtonStyle.GHOST
        widget.variant = Variant.WARNING

    def _on_btn_transfer_clicked(self):
        if self.layout_left.children:
            widget = self.layout_left.children[0]
            self.layout_right.add_widget(widget)


class SignalsWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Widgets
        self.btn_example_1 = Button('Push me')
        self.lbl_example_1 = Label('Clicks: 0')

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Signals can either be built-in, or defined by the end-user.'))
        self.add_widget(Label('Each widget holds its own set of signals.'))
        self.add_widget(Label('They can all be subscribed to and emitted manually.'))

        # Example
        self.add_widget(Label('Examples', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Built-in', variant=Variant.MUTED, style=LabelStyle.HEADING_3))
        layout_code = HLayout(
            padding=(5, 15, 5, 15), 
            horizontal_size_policy=SizePolicy.EXPANDING, 
            variant=Variant.MUTED, 
            horizontal_alignment=LayoutAlignment.START, 
            style=LayoutStyle.OUTLINED, 
            parent=self,
        )
        example_1_code = dedent("""
            button = Button(text="Push me")
            label = Label("Clicks: 0")

            button.clicked.connect(_on_button_clicked)

            def _on_button_clicked():
                prefix, count = label.split(" ")
                new_count = int(count) + 1
                button.text = f"{prefix} {str(new_count)}"
        """).strip()
        layout_code.add_widget(Label(example_1_code, style=LabelStyle.CODE))
        self.add_widget(Label('Result', variant=Variant.MUTED, style=LabelStyle.HEADING_3))
        layout_example_1 = HLayout(spacing=20, parent=self)
        layout_example_1.add_widget(self.btn_example_1)
        layout_example_1.add_widget(self.lbl_example_1)

        # Connections
        self.btn_example_1.clicked.connect(self._on_btn_example_1_clicked)

    def _on_btn_example_1_clicked(self):
        prefix, count = self.lbl_example_1.text.split(' ')
        new_count = int(count) + 1
        self.lbl_example_1.text = f'{prefix} {str(new_count)}'
        

class StylesWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        info_text = dedent("""
            Styles are unique to each widget - they modify the way it communicates to the user.
            Each widget's styles are visible in their respective documentation page.

            Styles usually do not modify colors, that is the Variant's job.
            A combination of styles & variants can be used to produce a specific widget.
        """).strip()
        self.add_widget(Label(info_text))

        
class VariantsWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        info_text = dedent("""
            Variants offer a way to modify the look of your widgets. They mainly affect color, based on the theme.
            By default, most widget ssupport all variants, but some widgets may not support all of them, or they may not be implemented.

            Note that the theme is fully editable through the app itself, therefore all variants share the same look when using variants.
        """).strip()
        self.add_widget(Label(info_text))

        # Examples
        self.add_widget(Label('Examples', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('As an example, heres a list of all the variants for a button, using the default style'))
        for variant in Variant:
            button = Button(text=variant.name, variant=variant, parent=self)


class ButtonWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_widget(Label('Widget -> Button', style=LabelStyle.HEADING_1))

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Buttons are clickable widgets that emit a clicked signal.'))

        # Signals
        self.add_widget(Label('Signals', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('clicked: Emitted when the button is clicked.'))

        # Styles
        self.add_widget(Label('Styles', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        for style in ButtonStyle:
            self.add_widget(Button(text=style.name, style=style))

        # Examples
        self.add_widget(Label('Examples', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        layout_code = HLayout(
            padding=(5, 15, 5, 15), 
            horizontal_size_policy=SizePolicy.EXPANDING, 
            variant=Variant.MUTED, 
            horizontal_alignment=LayoutAlignment.START, 
            style=LayoutStyle.OUTLINED, 
            parent=self,
        )
        layout_code.add_widget(Label('Button(text="my_button")', style=LabelStyle.CODE))
        self.add_widget(Label('Result', variant=Variant.MUTED, style=LabelStyle.HEADING_3))
        self.add_widget(Button('my_button'))


class LabelWidget(ContentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_widget(Label('Widget -> Label', style=LabelStyle.HEADING_1))

        # Info
        self.add_widget(Label('Info', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('Labels are simple widgets that display text.'))

        # Signals
        self.add_widget(Label('Signals', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        self.add_widget(Label('None'))

        # Styles
        self.add_widget(Label('Styles', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        for style in LabelStyle:
            self.add_widget(Label(style.name, style=style))

        # Examples
        self.add_widget(Label('Examples', variant=Variant.MUTED, style=LabelStyle.HEADING_2, padding=(25, 5, 10, 5)))
        layout_code = HLayout(
            padding=(5, 15, 5, 15), 
            horizontal_size_policy=SizePolicy.EXPANDING, 
            variant=Variant.MUTED, 
            horizontal_alignment=LayoutAlignment.START, 
            style=LayoutStyle.OUTLINED, 
            parent=self,
        )
        layout_code.add_widget(Label('Label(text="my_label")', style=LabelStyle.CODE))
        self.add_widget(Label('Result', variant=Variant.MUTED, style=LabelStyle.HEADING_3))
        self.add_widget(Label('my_label'))


# ______________________________________________________________________________________________________________________
# App
app = App(
    window=ShowcaseWindow,
    theme_preset=TreezeTheme.TREEZE,
)

# Granular theme overrides: these become CSS custom properties on the app root.
# app.theme.font_family = 'Consolas'
# app.theme.font_size = 14
# app.theme.spacing = 8
# app.theme.radius_md = 10
# app.theme.radius_lg = 14

# Color enum values can be used anywhere Theme accepts a color.
#app.theme.primary = Color.BLUE_600
app.theme.tertiary = Color.DARK_SLATE
app.theme.on_tertiary = Color.LIME_500

if __name__ == "__main__":
    app.run()
