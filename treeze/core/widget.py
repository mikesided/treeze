"""
Name:         widget.py
Description:  A Widget is a high level UI element that renders into various nodes. (abstract)

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from dataclasses import replace
from enum import StrEnum
from typing import Any, ClassVar, TYPE_CHECKING
from abc import ABC, ABCMeta, abstractmethod
from itertools import count
from math import isfinite
from weakref import WeakKeyDictionary, WeakSet

from .enums import BrowserEvent, Color, InitMode, Orientation, SizePolicy, Variant
from .events import EventBinding
from .exceptions import TreezeValueError, TreezeRuntimeError, TreezeTypeError
from .signals import BoundSignal, Signal
from .client_action import ClientAction
from .types.size import Size
from .types.gradients import ConeGradient, LinearGradient, RadialGradient
from .validation import Validator

from ..utils.ids import create_widget_id
from ..utils.session_context import get_current_session

# Forward Declarations
if TYPE_CHECKING:
    from .node import Node
    from ..runtime.session import Session
    from ..widgets.bases.container import Container
    from ..widgets.primitives.window import Window

# ______________________________________________________________________________________________________________________

ColorValue = str | Color | ConeGradient | LinearGradient | RadialGradient

_widget_id_counter = count(1)

class _WidgetMeta(ABCMeta):
    def __call__(cls, *args: Any, **kwargs: Any):
        widget = super().__call__(*args, **kwargs)
        widget._init_ready = True
        parent = widget.__dict__.pop('_pending_parent', None)
        if parent is not None and parent._CHILDHOST is True:
            parent._add_widget(widget)
        widget._schedule_init()
        return widget


class Widget(ABC, metaclass=_WidgetMeta):
    """
    Base class for Widget.
    
    A Widget is the single source of UI elements in treeze. Everything subclasses a widget.
    

    NOTE: Dirty tracking
    |   
    |    Treeze uses dirty tracking to decide which widgets need to be re-rendered
    |   after a signal or initialization hook mutates Python widget state.
    |
    |   Convention:
    |    - Public attributes are treated as render-affecting state. Changing them marks
    |    the widget dirty automatically through __setattr__.
    |    Example: widget.text, widget.variant, widget.size_policy.
    |
    |    - Private attributes are treated as framework/internal state. Changing them does
    |    not mark the widget dirty unless the attribute is explicitly allow-listed by
    |    the widget class.
    |    Example: widget._node, widget._parent, widget._session.
    |
    |
    |    - In-place mutations are not detected by __setattr__. Methods that mutate
    |    internal lists, dictionaries, sets, or widget structure must call
    |    _mark_dirty() themselves.
    |    Example: add_widget(), remove_widget(), add_class(), remove_class().
    |
    |    Dirty widgets are collected by the active Session. The runtime schedules
    |    updates, rebuilds/diffs only those dirty widgets, and sends the resulting
    |    patches to the browser. Client callbacks finish before their update runs.
    |
    |    During initial widget construction, widgets usually have no active session yet.
    |    Dirty marks at that stage are harmless: they affect the initial render, not a
    |    browser patch. The session clears dirty state after capturing the initial tree.
    

    """

    # DEFINTIONS
    _CSS_CLASS: ClassVar[str | None] = 'tz-widget'
    _CSS_CLASSES: ClassVar[tuple[str, ...]] = ()
    _DIRTY_PRIVATE_ATTRIBUTES: set[str] = set()  # Attributes in here will mark the widget dirty on update
    _STYLE_TYPE: ClassVar[type[StrEnum] | None] = None 
    _DEFAULT_STYLE: ClassVar[StrEnum | None] = None  # If a style type is set, we must declare a default
    _STYLE_PREFIX: ClassVar[str | None] = None  # Defaults to using the _CSS_CLASS as prefix
    _VARIANT_PREFIX: ClassVar[str | None] = None  # Defaults to using the _CSS_CLASS as prefix
    _SUPPORTED_VARIANTS: ClassVar[tuple[Variant, ...]] = ()  # Widgets opt in to CSS-backed variants

    # RUNTIME
    _ALLOW_DISABLED: bool = False

    # BEHAVIOR
    _CHILDHOST: bool = False  # Can this widget host children?
    _ORIENTATION: Orientation | None = None  # Orientation forced by this widget (mostly used by layouts)
    _SYNC_PROPERTY: ClassVar[str | None] = None

    # SIGNALS
    parent_changed = Signal(object, object)  # (Old parent container widget, New parent container widget)
    visibility_changed = Signal(bool)  # (isVisible?)
    collapsed_changed = Signal(bool)  # (isCollapsed?)
    enabled_changed = Signal(bool)  # (isEnabled?)

    # PUBLIC
    INIT_MODE = InitMode.ASYNCHRONOUS

    def __init__(
        self, 

        # Behavior & Look
        variant: Variant = Variant.DEFAULT,
        style: StrEnum | None = None,  # Default lives in cls._DEFAULT_STYLE

        # Spacing
        margin: int | tuple[int, int, int, int] | None = None,
        padding: int | tuple[int, int, int, int] | None = None,

        # Size Policies
        size_policy: tuple[SizePolicy, SizePolicy] = (SizePolicy.PREFERRED, SizePolicy.PREFERRED),
        horizontal_size_policy: SizePolicy | None = None,
        hsp: SizePolicy | None = None,  # Short code
        vertical_size_policy: SizePolicy | None = None,
        vsp: SizePolicy | None = None,  # Short code

        # Sizes
        minimum_size: Size | None = None,
        minimum_width: int | None = None,
        minimum_height: int | None = None,
        maximum_size: Size | None = None,
        maximum_width: int | None = None,
        maximum_height: int | None = None,
        fixed_size: Size | None = None,
        fixed_width: int | None = None,
        fixed_height: int | None = None,

        # CSS Wrappers
        color: str | Color | None = None,
        background_color: ColorValue | None = None,
        border: str | None = None,
        border_width: int | str | None = None,
        border_style: str | None = None,
        border_color: ColorValue | None = None,
        border_radius: int | str | None = None,
        opacity: int | float | str | None = None,

        # Runtime
        visible: bool = True,
        collapsed: bool = False,
        enabled: bool = True,
        classes: list[str] | None = None,
        parent: Container | None = None,
        p: Container | None = None,  # Short code

        # Framework
        init_mode: InitMode | None = None,
    ):
        # Establish ownership before setters run, without tracking partial initialization.
        object.__setattr__(self, '_suspend_dirty_tracking', True)
        session = get_current_session()
        if session is not None and session.closed:
            raise TreezeRuntimeError('Cannot create widgets in a closed session.')
        object.__setattr__(self, '_session', session)

        # Setup on_init
        self._init_ready = False
        self._init_started = False
        self._init_task = None
        if init_mode is not None:
            self._init_mode = Validator.ensure(init_mode, InitMode, attr_name='Widget(init_mode=...)')
        else:
            self._init_mode = Validator.ensure(type(self).INIT_MODE, InitMode, attr_name='Widget.INIT_MODE')

        for name, value in (('horizontal_size_policy', horizontal_size_policy),
                            ('vertical_size_policy', vertical_size_policy), ('hsp', hsp), ('vsp', vsp)):
            Validator.ensure(value, SizePolicy, None, attr_name=f'Widget({name}=...)')
        Validator.ensure(classes, list, None, attr_name='Widget(classes=...)')
        for index, klass in enumerate(classes or ()):
            Validator.ensure(klass, str, attr_name=f'Widget(classes=...)[{index}]')

        # Map short codes to their original values
        if hsp is not None and horizontal_size_policy is None:
            horizontal_size_policy = hsp
        if vsp is not None and vertical_size_policy is None:
            vertical_size_policy = vsp
        if p is not None and parent is None:
            parent = p
        
        # Internal properties
        # Unowned widgets keep distinct IDs when later attached to a session.
        self._id = self._session.id_scope.create_widget_id() if self._session is not None else f'u{create_widget_id()}'
        self._node: Node | None = None
        self._dirty: bool = False
        
        self._signals: dict[str, BoundSignal] = {}
        self._sync_targets: dict[BrowserEvent, WeakSet[Widget]] = {}
        self._sync_triggers: WeakKeyDictionary[Widget, set[BrowserEvent]] = WeakKeyDictionary()
        self._sync_dependents: WeakSet[Widget] = WeakSet()  # Sync targets affected by this ancestor's enabled state
        self._container_orientation: Orientation | None = None  # Maintained by `_set_parent`: holds the container's orientation
        self._composite_classes: list[str] = []
        self._extra_classes: list[str] = []  # Holds user-defined classes
        self._parent: Container | Window | None = None

        # Private properties
        self._variant: Variant = Variant.DEFAULT
        self._style: StrEnum | None = None

        self._margin: int | tuple[int, int, int, int] | None = None
        self._padding: int | tuple[int, int, int, int] | None = None

        self._horizontal_size_policy: SizePolicy = SizePolicy.PREFERRED
        self._vertical_size_policy: SizePolicy = SizePolicy.PREFERRED

        self._minimum_width: int | None = None
        self._minimum_height: int | None = None
        self._maximum_width: int | None = None
        self._maximum_height: int | None = None
        self._fixed_width: int | None = None
        self._fixed_height: int | None = None

        self._color: ColorValue | None = None
        self._background_color: ColorValue | None = None
        self._border_width: int | str | None = None
        self._border_style: str | None = None
        self._border_color: ColorValue | None = None
        self._border_radius: int | str | None = None
        self._opacity: int | float | str | None = None

        self._visible: bool = True
        self._collapsed: bool = False
        self._enabled: bool = True

        # Create signals
        for signal_name, signal in type(self)._declared_signals().items():
            self._create_signal(signal_name, signal.arg_types)

        # Assign framework properties
        self.variant = variant
        self.style = style

        self.margin = margin
        self.padding = padding

        self.size_policy = size_policy
        if horizontal_size_policy is not None:
            self.horizontal_size_policy = horizontal_size_policy
        if vertical_size_policy is not None:
            self.vertical_size_policy = vertical_size_policy

        self.minimum_width = minimum_width
        self.minimum_height = minimum_height
        if minimum_size is not None:
            self.minimum_size = minimum_size
        self.maximum_width = maximum_width
        self.maximum_height = maximum_height
        if maximum_size is not None:
            self.maximum_size = maximum_size
        self.fixed_width = fixed_width
        self.fixed_height = fixed_height
        if fixed_size is not None:
            self.fixed_size = fixed_size

        self.color = color
        self.background_color = background_color
        self.border = border
        self.border_width = border_width
        self.border_style = border_style
        self.border_color = border_color
        self.border_radius = border_radius
        self.opacity = opacity

        self.visible = visible
        self.collapsed = collapsed
        self.enabled = enabled
        
        # Add classes
        for klass in classes or ():
            self.add_class(klass)

        # Attach parent only after the most-derived constructor has finished.
        self._pending_parent = Validator.ensure(parent, Widget, None, attr_name='Widget(parent=...)')

        self._suspend_dirty_tracking = False
        self._mark_dirty()

    # ==========================================================================
    #  Properties
    # ==========================================================================

    @property
    def session(self) -> Session | None:
        """Session owning this widget."""
        return self._session

    @property
    def classes(self) -> tuple[str, ...]:
        """Read only. CSS classes applied to this widget"""
        return tuple(self._extra_classes)

    @property
    def parent(self) -> Container | Window | None:
        """Read only. The widget's parent"""
        return self._parent
    
    @property
    def id(self) -> str:
        """Read only. The widget's internal ID"""
        return self._id

    @property
    def init_mode(self) -> InitMode:
        """Read only. Returns the widget's init mode"""
        return self._init_mode
    
    @property
    def _is_dirty(self) -> bool:
        return self._dirty
    
    @property
    def signals(self) -> tuple[BoundSignal, ...]:
        return tuple(self._signals.values())
    
    @property
    def variant(self) -> Variant:
        return self._variant

    @variant.setter
    def variant(self, variant: Variant):
        """Holds the widget's style variant"""
        variant = Validator.ensure(variant, Variant, attr_name='Widget.variant')

        if variant == Variant.DEFAULT:
            self._variant = variant
            return

        if variant not in self._SUPPORTED_VARIANTS:
            raise TreezeValueError(
                f'Widget.variant: {type(self).__name__} does not support {variant!r}.'
            )

        self._variant = variant

    @property
    def style(self) -> StrEnum | None:
        return self._style

    @style.setter
    def style(self, style: StrEnum) -> None:            
        style = self._resolve_widget_style(style)

        if self._style is style:
            return

        self._style = style

    @property
    def margin(self) -> tuple[int, int, int, int]:
        return self._margin
    
    @margin.setter
    def margin(self, margin: int | tuple[int, int, int, int] | None):
        self._margin = Validator.validate_box(margin, attr_name='Widget.margin')

    @property
    def padding(self) -> tuple[int, int, int, int]:
        return self._padding
    
    @padding.setter
    def padding(self, padding: int | tuple[int, int, int, int] | None):
        self._padding = Validator.validate_box(padding, attr_name='Widget.padding')

    @property
    def size_policy(self) -> tuple[SizePolicy, SizePolicy]:
        return (self.horizontal_size_policy, self.vertical_size_policy)

    @size_policy.setter
    def size_policy(self, size_policies: tuple[SizePolicy, SizePolicy]):
        """Convenience wrapper around horizontal & vertical size policies"""
        Validator.ensure(size_policies, tuple, list, attr_name='Widget.size_policy')
        if len(size_policies) != 2:
            raise TreezeValueError('Widget.size_policy: must contain exactly 2 values.')
        Validator.ensure(size_policies[0], SizePolicy, attr_name='Widget.size_policy[0]')
        Validator.ensure(size_policies[1], SizePolicy, attr_name='Widget.size_policy[1]')
        self.horizontal_size_policy = size_policies[0]
        self.vertical_size_policy = size_policies[1]

    @property
    def horizontal_size_policy(self) -> SizePolicy:
        return self._horizontal_size_policy

    @horizontal_size_policy.setter
    def horizontal_size_policy(self, size_policy: SizePolicy):
        self._horizontal_size_policy = Validator.ensure(size_policy, SizePolicy, attr_name='Widget.horizontal_size_policy')
    
    @property
    def vertical_size_policy(self) -> SizePolicy:
        return self._vertical_size_policy

    @vertical_size_policy.setter
    def vertical_size_policy(self, size_policy: SizePolicy):
        self._vertical_size_policy = Validator.ensure(size_policy, SizePolicy, attr_name='Widget.vertical_size_policy')

    @property
    def minimum_width(self) -> int | None:
        return self._minimum_width

    @minimum_width.setter
    def minimum_width(self, width: int | None):
        self._minimum_width = Validator.validate_dimension(width, attr_name='Widget.minimum_width')

    @property
    def minimum_height(self) -> int | None:
        return self._minimum_height

    @minimum_height.setter
    def minimum_height(self, width: int | None):
        self._minimum_height = Validator.validate_dimension(width, attr_name='Widget.minimum_height')

    @property
    def minimum_size(self) -> Size | None:
        if isinstance(self.minimum_width, int) and isinstance(self.minimum_height, int):
            return Size(self.minimum_width, self.minimum_height)
        return None
    
    @minimum_size.setter
    def minimum_size(self, size: Size | None):
        size = Validator.ensure(size, Size, None, attr_name='Widget.minimum_size')
        if size:
            width = Validator.ensure(size.width, int, attr_name='Widget.minimum_size.width')
            height = Validator.ensure(size.height, int, attr_name='Widget.minimum_size.height')
        else:
            width = None
            height = None

        self.minimum_width = width
        self.minimum_height = height

    @property
    def fixed_width(self) -> int | None:
        """Overrides minimum_width and maximum_width"""
        return self._fixed_width

    @fixed_width.setter
    def fixed_width(self, width: int | None):
        self._fixed_width = Validator.validate_dimension(width, attr_name='Widget.fixed_width')

    @property
    def fixed_height(self) -> int | None:
        """Overrides minimum_height and maximum_height"""
        return self._fixed_height

    @fixed_height.setter
    def fixed_height(self, width: int | None):
        self._fixed_height = Validator.validate_dimension(width, attr_name='Widget.fixed_height')

    @property
    def fixed_size(self) -> Size | None:
        """Overrides minimum_size and maximum_size"""
        if isinstance(self.fixed_width, int) and isinstance(self.fixed_height, int):
            return Size(self.fixed_width, self.fixed_height)
    
    @fixed_size.setter
    def fixed_size(self, size: Size | None):
        size = Validator.ensure(size, Size, None, attr_name='Widget.fixed_size')
        if size:
            width = Validator.ensure(size.width, int, attr_name='Widget.fixed_size.width')
            height = Validator.ensure(size.height, int, attr_name='Widget.fixed_size.height')
        else:
            width = None
            height = None

        self.fixed_width = width
        self.fixed_height = height

    @property
    def maximum_width(self) -> int | None:
        return self._maximum_width

    @maximum_width.setter
    def maximum_width(self, width: int | None):
        self._maximum_width = Validator.validate_dimension(width, attr_name='Widget.maximum_width')

    @property
    def maximum_height(self) -> int | None:
        return self._maximum_height

    @maximum_height.setter
    def maximum_height(self, width: int | None):
        self._maximum_height = Validator.validate_dimension(width, attr_name='Widget.maximum_height')
    
    @property
    def maximum_size(self) -> Size | None:
        if isinstance(self.maximum_width, int) and isinstance(self.maximum_height, int):
            return Size(self.maximum_width, self.maximum_height)
        return None
    
    @maximum_size.setter
    def maximum_size(self, size: Size| None):
        size = Validator.ensure(size, Size, None, attr_name='Widget.maximum_size')
        if size:
            width = Validator.ensure(size.width, int, attr_name='Widget.maximum_size.width')
            height = Validator.ensure(size.height, int, attr_name='Widget.maximum_size.height')
        else:
            width = None
            height = None

        self.maximum_width = width
        self.maximum_height = height

    @property
    def visible(self) ->  bool:
        return self._visible

    @visible.setter
    def visible(self, visible):
        """Set the visibility of the widget. Still takes layout space."""
        old_state = self.visible
        self._visible = Validator.ensure(visible, bool, attr_name='Widget.visible')

        if old_state != self.visible:
            self.visibility_changed.emit(self.visible)

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    @collapsed.setter
    def collapsed(self, collapsed):
        """Collapse the widget. Does not take layout space."""
        old_state = self.collapsed
        self._collapsed = Validator.ensure(collapsed, bool, attr_name='Widget.collapsed')

        if old_state != self.collapsed:
            self.collapsed_changed.emit(self.collapsed)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool):
        """Enables/Disables the widget."""
        enabled = Validator.ensure(enabled, bool, attr_name='Widget.enabled')
        if enabled is False and self._ALLOW_DISABLED is False:
            raise TreezeRuntimeError(f'{self.__class__.__name__} widgets cannot be disabled')

        old_state = self.enabled
        self._enabled = enabled

        if old_state != self.enabled:
            for target in self._sync_dependents:
                for source in target._sync_triggers:
                    source._mark_dirty()
            self.enabled_changed.emit(self.enabled)

    @property
    def color(self) -> ColorValue:
        return self._color

    @color.setter
    def color(self, color: ColorValue):
        self._color = Validator.ensure(color, ColorValue, None, attr_name='Widget.color')

    @property
    def background_color(self) -> ColorValue:
        return self._background_color

    @background_color.setter
    def background_color(self, background_color: ColorValue):
        self._background_color = Validator.ensure(background_color, ColorValue, None, attr_name='Widget.background_color')

    @property
    def border(self) -> str | None:
        return self._border

    @border.setter
    def border(self, border: str | None):
        if isinstance(border, str):
            if not len(border.split(' ')) == 3:
                raise TreezeValueError('Widget.border: must match "<width> <style> <color>".')
        self._border = Validator.ensure(border, str, None, attr_name='Widget.border')

    @property
    def border_width(self) -> int | str | None:
        return self._border_width

    @border_width.setter
    def border_width(self, border_width: int | str | None):
        self._border_width = Validator.ensure(border_width, int, str, None, attr_name='Widget.border_width')

    @property
    def border_style(self) -> str | None:
        return self._border_style

    @border_style.setter
    def border_style(self, border_style: str | None):
        self._border_style = Validator.ensure(border_style, str, None, attr_name='Widget.border_style')

    @property
    def border_color(self) -> ColorValue | None:
        return self._border_color

    @border_color.setter
    def border_color(self, border_color: ColorValue | None):
        self._border_color = Validator.ensure(border_color, ColorValue, None, attr_name='Widget.border_color')

    @property
    def border_radius(self) -> int | str | None:
        return self._border_radius

    @border_radius.setter
    def border_radius(self, border_radius: int | str | None):
        self._border_radius = Validator.ensure(border_radius, int, str, None, attr_name='Widget.border_radius')

    @property
    def opacity(self) -> int | float | str | None:
        return self._opacity

    @opacity.setter
    def opacity(self, opacity: int | float | str | None):
        Validator.ensure(opacity, int, float, str, None, attr_name='Widget.opacity')
        if isinstance(opacity, (int, float)):
            if isinstance(opacity, bool):
                raise TreezeTypeError('Widget.opacity: cannot be a boolean.')
            if isinstance(opacity, float) and not isfinite(opacity):
                raise TreezeValueError('Widget.opacity: must be finite.')
            if not 0 <= opacity <= 1:
                raise TreezeValueError('Widget.opacity: must be between 0 and 1.')
        self._opacity = opacity

        
    # ==========================================================================
    #  Public API
    # ==========================================================================

    async def on_init(self) -> None:
        """Initialize this widget once, after its complete constructor finishes."""
        pass

    def execute(self, action: ClientAction) -> None:
        """Queue a one-time browser action on this widget"""
        if self._session is None:
            raise TreezeRuntimeError(
                'Cannot execute a client action without an active session.'
            )
        self._session._queue_client_action(Validator.ensure(action, ClientAction, attr_name='Widget.execute(action=...)'))

    def unparent(self) -> None:
        """Remove this widget from its parent"""
        if not self.parent:
            return

        self.parent._remove_widget(widget=self)
        
        # Not sure if mark dirty is required here. 
        # If the widget no longer has a parent, it shouldn't be rendered anyways
        self._mark_dirty()


    def add_class(self, class_name: str) -> None:
        """Adds a css class to the widget"""
        class_name = Validator.ensure(class_name, str, attr_name='Widget.add_class(class_name=...)')

        if class_name.startswith('tz-'):
            raise TreezeValueError('Widget.add_class(class_name=...): cannot start with "tz-"; the prefix is reserved by Treeze.')

        if class_name not in self._extra_classes:
            self._extra_classes.append(class_name)
            self._mark_dirty()


    def remove_class(self, class_name: str) -> None:
        """Removes a css class from the widget"""
        class_name = Validator.ensure(class_name, str, attr_name='Widget.remove_class(class_name=...)')
        
        if class_name.startswith('tz-'):
            raise TreezeValueError('Widget.remove_class(class_name=...): cannot modify classes starting with "tz-".')

        if class_name in self._extra_classes:
            self._extra_classes.remove(class_name)
            self._mark_dirty()
    

    # ==========================================================================
    #  Private
    # ==========================================================================

    def _set_parent(self, widget: Container | Window | None = None):
        """
        Sets a new parent on the widget.
        Exposed for container to call when capturing ownership
        """
        old_parent = self._parent

        widget = Validator.ensure(widget, Widget, None, attr_name='Widget._set_parent(widget=...)')
        if old_parent is widget:
            return
        session = self._session
        if session is not None and session._widgets.get(self.id) is self:
            session._unregister_subtree(self)
        ancestor = old_parent
        while ancestor is not None:
            ancestor._sync_dependents.difference_update(self._sync_dependents)
            ancestor = ancestor.parent
        self._parent = widget
        self._container_orientation = widget._ORIENTATION if widget else None
        ancestor = widget
        while ancestor is not None:
            ancestor._sync_dependents.update(self._sync_dependents)
            ancestor = ancestor.parent
        if widget is not None and widget._session is not None:
            session = widget._session
            if session._widgets.get(widget.id) is widget:
                session._register_subtree(self)
            else:
                for child in self._walk_widgets():
                    child._set_session(session)

        # Emit parent_changed signal
        self.parent_changed.emit(old_parent, self._parent)

    def _walk_widgets(self):
        """Yield any widgets owned by this widget. Used for event callback."""
        yield self

    def _validate_session(self, session: Session) -> None:
        if session.closed:
            raise TreezeRuntimeError('Cannot attach widgets to a closed session.')
        if self._session is session:
            return
        if self._session is not None:
            raise TreezeValueError('A widget cannot move between sessions.')
        for related in (*self._sync_triggers, *(target for targets in self._sync_targets.values() for target in targets)):
            if related._session is not None and related._session is not session:
                raise TreezeValueError('Synchronization widgets must belong to the same session.')

    def _validate_parent(self, parent: Widget | None) -> None:
        if parent is None:
            return
        session = parent._session
        if session is not None:
            for widget in self._walk_widgets():
                widget._validate_session(session)
        elif self._session is not None:
            ancestor = parent
            while ancestor is not None:
                ancestor._validate_session(self._session)
                ancestor = ancestor.parent

    def _set_session(self, session: Session) -> None:
        self._validate_session(session)
        if self._session is None:
            self._session = session
            self._schedule_init()

    def _schedule_init(self) -> None:
        """Schedule once after construction, deferring only until a session exists."""
        if not self._init_ready or self._init_started:
            return
        if type(self).on_init is Widget.on_init:
            self._init_started = True
        elif self._session is not None:
            self._session._initialize_widget(self)

    def sync_on(self, *triggers: Signal | BoundSignal | BrowserEvent) -> None:
        """Synchronize this widget's browser value before a trigger's callbacks."""
        if self._SYNC_PROPERTY is None:
            raise TreezeRuntimeError(f'{type(self).__name__} does not support synchronization.')
        if not triggers:
            raise TreezeValueError('Widget.sync_on(): provide at least one browser event or signal.')
        registrations = set()
        for trigger in triggers:
            owner = self
            if isinstance(trigger, BrowserEvent):
                events = (trigger,)
            else:
                if isinstance(trigger, Signal):
                    names = [name for name, signal in self._declared_signals().items() if signal is trigger]
                    if not names:
                        raise TreezeValueError('Widget.sync_on(): unbound signal does not belong to this widget.')
                    trigger = self._get_signal(names[0])
                if not isinstance(trigger, BoundSignal) or not isinstance(trigger.owner, Widget):
                    raise TreezeTypeError('Widget.sync_on(): expected a BrowserEvent or browser-backed signal.')
                owner = trigger.owner
                events = tuple(event for event, binding in owner._render().events.items() if binding.signal == trigger.name)
                if not events:
                    raise TreezeValueError(f'Widget.sync_on(): signal {trigger.name!r} is not browser-backed.')
            for widget in (self, owner):
                if widget._session is not None and widget._session.closed:
                    raise TreezeRuntimeError('Cannot register synchronization on a closed session.')
            if self._session is not None and owner._session is not None and self._session is not owner._session:
                raise TreezeValueError('Synchronization widgets must belong to the same session.')
            registrations.update((owner, event) for event in events)
        for owner, event in registrations:
            targets = owner._sync_targets.setdefault(event, WeakSet())
            if self not in targets:
                targets.add(self)
                self._sync_triggers.setdefault(owner, set()).add(event)
                ancestor = self
                while ancestor is not None:
                    ancestor._sync_dependents.add(self)
                    ancestor = ancestor.parent
                owner._mark_dirty()

    def _is_enabled_in_tree(self) -> bool:
        owner = self
        while owner is not None:
            if not owner.enabled:
                return False
            owner = owner.parent
        return True

    def _active_sync_targets(self, event: BrowserEvent) -> dict[str, Widget]:
        session = self._session
        if session is None or session.closed or session._widgets.get(self.id) is not self:
            return {}
        return {
            target.id: target for target in self._sync_targets.get(event, ())
            if target._session is session and session._widgets.get(target.id) is target
            and target._is_enabled_in_tree()
        }

    def _validate_sync_value(self, value: Any) -> Any:
        raise TreezeRuntimeError(f'{type(self).__name__} does not support synchronization.')

    def _apply_sync_value(self, value: Any) -> None:
        raise TreezeRuntimeError(f'{type(self).__name__} does not support synchronization.')

    def _mark_dirty(self) -> None:
        if getattr(self, '_suspend_dirty_tracking', False):
            return

        self._dirty = True

        session = getattr(self, '_session', None)
        if session is not None:
            session._mark_widget_dirty(self)

    def _mark_clean(self) -> None:
        self._dirty = False


    # ==========================================================================
    #  Signals
    # ==========================================================================

    def _assign_dynamic_signal(self, name: str, signal: Signal) -> BoundSignal:
        if '_signals' not in self.__dict__:
            raise TreezeRuntimeError(f'Cannot assign signal {name!r} before Widget.__init__() has run.')

        if name.startswith('_'):
            raise TreezeRuntimeError(f'Signal name {name!r} cannot start with an underscore.')

        if name in type(self)._declared_signals():
            raise TreezeRuntimeError(
                f'{type(self).__name__} already has a declared signal named '
                f'{name!r}. Use self.{name}.connect(...) instead.'
            )

        if name in self._signals:
            raise TreezeRuntimeError(
                f'{type(self).__name__} already has a signal named {name!r}.'
            )

        if name in self.__dict__:
            raise TreezeRuntimeError(
                f'{type(self).__name__} already has an instance attribute named '
                f'{name!r}.'
            )

        if hasattr(type(self), name):
            raise TreezeRuntimeError(
                f'{type(self).__name__} already has a class attribute named '
                f'{name!r}.'
            )

        signal._bind_name(name)

        bound_signal = self._create_signal(name, signal.arg_types)

        super().__setattr__(name, bound_signal)

        return bound_signal

    def _create_signal(self, name: str, arg_types: tuple[type, ...] = ()) -> BoundSignal:
        existing = self._signals.get(name)

        if existing is not None:
            raise TreezeRuntimeError(f'{type(self).__name__} already has a signal named {name!r}.')

        signal = BoundSignal(self, name, arg_types)
        self._signals[name] = signal

        return signal
        
    def _get_signal(self, name: str) -> BoundSignal:
        signal = self._signals.get(name)

        if signal is None:
            raise TreezeRuntimeError(f'{type(self).__name__} has no signal named {name!r}.')

        return signal
    
    def _has_signal(self, name: str) -> bool:
        return name in self._signals

    def _emit_signal(self, name: str, *args: Any, **kwargs: Any) -> None:
        declared_signal = self._declared_signals().get(name)

        if declared_signal is None:
            raise TreezeRuntimeError(
                f'Widget {type(self).__name__!r} has no signal named {name!r}.'
            )

        self._get_signal(name).emit(*args, **kwargs)

    @classmethod
    def _declared_signals(cls) -> dict[str, Signal]:
        """Returns any declared signals on the class"""
        signals: dict[str, Signal] = {}

        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, Signal):
                    signals[name] = value

        return signals

    # ==========================================================================
    #  Rendering
    # ==========================================================================
    

    def _classes(self) -> list[str]:
        main_css_class = type(self)._CSS_CLASS
        if main_css_class is None:
            raise RuntimeError(f'{type(self).__name__} widget has no _CSS_CLASS.')
    
        classes: list[str] = []

        # Collect main classes + extra framework classes from base -> subclass
        for cls in reversed(type(self).mro()):
            css_class = cls.__dict__.get('_CSS_CLASS')

            if css_class is not None and css_class not in classes:
                classes.append(css_class)

            css_classes = cls.__dict__.get('_CSS_CLASSES', ())

            for css_class in css_classes:
                if css_class not in classes:
                    classes.append(css_class)

        # Add disabled class
        if self.enabled is False:
            classes.append('tz-disabled')

        # Add variant class
        if self.variant != Variant.DEFAULT:
            if type(self)._VARIANT_PREFIX:
                prefix = type(self)._VARIANT_PREFIX
            else:
                prefix = main_css_class
            classes.append(f'{prefix}-{self.variant}')

        # Add style class
        if self._style is not None:
            if type(self)._STYLE_PREFIX:
                prefix = type(self)._STYLE_PREFIX
            else:
                prefix = main_css_class
            classes.append(f'{prefix}-{self._style}')

        # Add composite classes
        for css_class in self._composite_classes:
            if css_class not in classes:
                classes.append(css_class)

        # Add user-defined classes
        for css_class in self._extra_classes:
            if css_class not in classes:
                classes.append(css_class)

        return classes

    def _styles(self) -> dict[str, str]:
        styles = {}

        # Size policies
        styles.update(self._styles_size_policy())

        if self.fixed_width is not None:
            styles['width'] = f'{self.fixed_width}px'
        else:
            if self.minimum_width is not None:
                styles['min-width'] = f'{self.minimum_width}px'
            if self.maximum_width is not None:
                styles['max-width'] = f'{self.maximum_width}px'

        if self.fixed_height is not None:
            styles['height'] = f'{self.fixed_height}px'
        else:
            if self.minimum_height is not None:
                styles['min-height'] = f'{self.minimum_height}px'
            if self.maximum_height is not None:
                styles['max-height'] = f'{self.maximum_height}px'

        if self.margin is not None:
            top, right, bottom, left = self.margin
            styles['margin'] = f'{top}px {right}px {bottom}px {left}px'

        if self.padding is not None:
            top, right, bottom, left = self.padding
            styles['padding'] = f'{top}px {right}px {bottom}px {left}px'

        if self.collapsed is True:
            styles['display'] = 'none'

        if self.visible is False:
            styles['visibility'] = 'hidden'

        if self.color is not None:
            styles['color'] = str(self.color)

        if self.background_color is not None:
            property_name = 'background' if isinstance(
                self.background_color, (ConeGradient, LinearGradient, RadialGradient)
            ) else 'background-color'
            styles[property_name] = str(self.background_color)

        if self.border:
            styles['border'] = self.border

        if self.border_width is not None:
            styles['border-width'] = (
                f'{self.border_width}px' if isinstance(self.border_width, int)
                else self.border_width
            )

        if self.border_style:
            styles['border-style'] = self.border_style

        if self.border_color is not None:
            if isinstance(self.border_color, (ConeGradient, LinearGradient, RadialGradient)):
                styles['border-image-source'] = str(self.border_color)
                styles['border-image-slice'] = '1'
            else:
                styles['border-color'] = str(self.border_color)

        if self.border_radius is not None:
            styles['border-radius'] = (
                f'{self.border_radius}px' if isinstance(self.border_radius, int)
                else self.border_radius
            )

        if self.opacity is not None:
            styles['opacity'] = str(self.opacity)

        return styles
    
    def _styles_size_policy(self) -> dict[str, str]:
        styles = {}

        # Get axis size policies
        match self._container_orientation:
            case Orientation.HORIZONTAL:
                main_axis_size_policy = self.horizontal_size_policy
                cross_axis_size_policy = self.vertical_size_policy
                cross_axis_property = 'height'
            case Orientation.VERTICAL:
                main_axis_size_policy = self.vertical_size_policy
                cross_axis_size_policy = self.horizontal_size_policy
                cross_axis_property = 'width'
            case None:
                return {}
            case _:
                raise ValueError(f'Unsupported container orientation: {self._container_orientation!r}')
        
        # Map main axis to flex data
        styles['flex'] = main_axis_size_policy.value

        # Map cross axis to align-self
        match cross_axis_size_policy:
            case SizePolicy.EXPANDING:
                styles[cross_axis_property] = '100%'
            case SizePolicy.FIXED | SizePolicy.MINIMUM | SizePolicy.PREFERRED:
                pass
            case _:
                raise ValueError(f'Unsupported cross axis size policy: {cross_axis_size_policy!r}')
        
        return styles

    
    @abstractmethod
    def _render(self) -> Node:
        """Render method to implement in each widget"""
        raise NotImplementedError

    def _build(self) -> Node:
        """Render as a node, retain and return"""
        # TODO: implement dirty flags to use caching
        # NOTE: do we still need this? investigate. Does the patch engine solve this requirement?
        #if self._node is None:
        #    self._node = self._render()
            
        self._node = self._render()

        for browser_event in self._sync_targets:
            if self._active_sync_targets(browser_event):
                self._node.events.setdefault(browser_event, EventBinding())

        for browser_event, binding in tuple(self._node.events.items()):
            targets = self._active_sync_targets(browser_event)
            if binding.signal is not None:
                signal = self._get_signal(binding.signal)
                binding = replace(
                    binding,
                    signal=binding.signal if signal.has_callbacks() or targets else None,
                    actions=(*binding.actions, *signal.actions),
                )
            binding = replace(binding, sync={target.id: target._SYNC_PROPERTY for target in targets.values()})
            if binding.signal is None and not binding.actions and not binding.sync:
                del self._node.events[browser_event]
            else:
                self._node.events[browser_event] = binding

        return self._node


    # ==========================================================================
    #  Internal
    # ==========================================================================

    def _resolve_widget_style(self, style: StrEnum | None) -> StrEnum | None:
        style_type = type(self)._STYLE_TYPE
        default_style = type(self)._DEFAULT_STYLE

        if style_type is None:
            if style is not None:
                raise TreezeTypeError(f'Widget.style: {type(self).__name__} does not support styles.')

            return None

        if style is None:
            return default_style

        Validator.ensure(style, style_type, attr_name='Widget.style')

        return style

    @classmethod
    def _dirty_private_attributes(cls) -> set[str]:
        attributes: set[str] = set()

        for base in reversed(cls.mro()):
            attributes.update(
                getattr(base, '_DIRTY_PRIVATE_ATTRIBUTES', set())
            )

        return attributes

    def _is_dirty_attribute(self, name: str) -> bool:
        if not name.startswith('_'):
            return True

        return name in type(self)._dirty_private_attributes()

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, Signal):
            self._assign_dynamic_signal(name, value)

            if self._is_dirty_attribute(name):
                self._mark_dirty()

            return

        if '_signals' in self.__dict__ and self._has_signal(name):
            raise TreezeRuntimeError(f'Signal {name!r} already connected.')

        try:
            old_value = object.__getattribute__(self, name)
        except AttributeError:
            old_value = None

        super().__setattr__(name, value)

        if old_value == value:
            return

        if not self._is_dirty_attribute(name):
            return

        if '_session' not in self.__dict__:
            return

        self._mark_dirty()
