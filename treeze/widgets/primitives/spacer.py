"""
Name:         button.py
Description:  Base class for a Button widget

"""
# ______________________________________________________________________________________________________________________
# Imports
from ...core.enums import SizePolicy
from ...core.node import Node
from ...core.widget import Widget

# ______________________________________________________________________________________________________________________

class Spacer(Widget):

    _SUPPORTED_VARIANTS = ()
    _CSS_CLASS = 'tz-spacer'
    def _render(self) -> Node:
        return Node(
            id=self.id,
            tag='div',
            classes=self._classes(),
            styles=self._styles(),
        )


class HSpacer(Spacer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.size_policy = (
            SizePolicy.EXPANDING,
            SizePolicy.FIXED,
        )


class VSpacer(Spacer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.size_policy = (
            SizePolicy.FIXED,
            SizePolicy.EXPANDING,
        )