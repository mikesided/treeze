"""
Name:         widget.py
Description:  A Widget is a high level UI element that renders into various nodes. (abstract)

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Any, ClassVar, TYPE_CHECKING
from abc import ABC, abstractmethod
from itertools import count

from .enums import Orientation, SizePolicy, Variant
from .exceptions import TreezeValueError, TreezeRuntimeError
from .signals import BoundSignal, Signal
from .types.size import Size
from .validation import Validator

from ..utils.ids import create_widget_id

# Forward Declarations
if TYPE_CHECKING:
    from .node import Node
    from ..runtime.session import Session
    from ..widgets.bases.container import Container

# ______________________________________________________________________________________________________________________

_widget_id_counter = count(1)

class Widget(ABC):
    """
    Base class for Widget.
    
    A Widget is the single source of UI elements in treeze. Everything subclasses a widget.
    

    NOTE: Dirty tracking
    |   
    |    Treeze uses dirty tracking to decide which widgets need to be re-rendered
    |   after a signal mutates Python widget state.
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
    |    Dirty widgets are collected by the active Session. After a client signal is
    |    handled, the runtime rebuilds/diffs only those dirty widgets and sends the
    |    resulting patches to the browser.
    |
    |    During initial widget construction, widgets usually have no active session yet.
    |    Dirty marks at that stage are harmless: they affect the initial render, not a
    |    browser patch. The session clears dirty state after capturing the initial tree.
    

    """
    # TODO: parent_changed signal (old, new)

    DEFAULT = Variant.DEFAULT
    PRIMARY = Variant.PRIMARY
    SECONDARY = Variant.SECONDARY
    TERTIARY = Variant.TERTIARY
    SUCCESS = Variant.SUCCESS
    WARNING = Variant.WARNING
    DANGER = Variant.DANGER
    INFO = Variant.INFO

    # DEFINTIONS
    _CSS_CLASS: ClassVar[str | None] = 'tz-widget'
    _CSS_CLASSES: ClassVar[tuple[str, ...]] = ()
    _SUPPORTED_VARIANTS: ClassVar[tuple[Variant, ...]] = (Variant.DEFAULT)
    _DIRTY_PRIVATE_ATTRIBUTES: set[str] = set()  # Attributes in here will mark the widget dirty on update

    # BEHAVIOR
    _CHILDHOST: bool = False  # Can this widget host children?
    _ORIENTATION: Orientation | None = None  # Orientation forced by this widget (mostly used by layouts)

    # SIGNALS
    parent_changed = Signal(Widget, Widget)

    def __init__(
            self, 
            variant: Variant = Variant.DEFAULT,
            parent: Container | None = None,
            classes: list[str] = []
        ):
                
        # Internal properties
        self._id = create_widget_id()
        self._node: Node | None = None
        self._session: Session = None
        self._dirty: bool = False
        self._suspend_dirty_tracking: bool = False

        # Framework properties
        self.variant = variant
        self._extra_classes : list[str] = []  # Holds user-defined classes
        self._parent: Container | None = None
        self._signals: dict[str, BoundSignal] = {}

        self._container_orientation: Orientation | None = None  # Maintained by `_set_parent`: holds the container's orientation
        self.horizontal_size_policy = SizePolicy.PREFERRED
        self.vertical_size_policy = SizePolicy.PREFERRED
        self.minimum_size = None
        self.maximum_size = None

        # Add classes
        for klass in classes:
            self.add_class(klass)

        # Add Signals
        for signal_name, signal in type(self)._declared_signals().items():
            self._create_signal(signal_name, signal.arg_types)

        # Set parent
        parent = Validator.ensure(parent, Widget, None)
        if parent is not None and parent._CHILDHOST is True:
            # Ugly - no direct link to a container, but will do as long as only containers can be child hosts
            parent.add_widget(self)

    # ==========================================================================
    #  Properties
    # ==========================================================================

    @property
    def classes(self) -> tuple[str, ...]:
        """Read only. CSS classes applied to this widget"""
        return tuple(self._extra_classes)

    @property
    def parent(self) -> Container | None:
        """Read only. The widget's parent"""
        return self._parent
    
    @property
    def id(self) -> str:
        """Read only. The widget's internal ID"""
        return self._id
    
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
        variant = Validator.ensure(variant, Variant)

        if variant == Variant.DEFAULT:
            self._variant = variant
            return

        if variant not in self._SUPPORTED_VARIANTS:
            raise TreezeValueError(
                f'{type(self).__name__} does not support variant: {variant!r}'
            )

        self._variant = variant

    @property
    def size_policy(self) -> tuple[SizePolicy, SizePolicy]:
        return (self.horizontal_size_policy, self.vertical_size_policy)

    @size_policy.setter
    def size_policy(self, size_policies: tuple[SizePolicy, SizePolicy]):
        """Convenience wrapper around horizontal & vertical size policies"""
        self.horizontal_size_policy = size_policies[0]
        self.vertical_size_policy = size_policies[1]
        
    @property
    def horizontal_size_policy(self) -> SizePolicy:
        return self._horizontal_size_policy

    @horizontal_size_policy.setter
    def horizontal_size_policy(self, size_policy: SizePolicy):
        self._horizontal_size_policy = Validator.ensure(size_policy, SizePolicy)
    
    @property
    def vertical_size_policy(self) -> SizePolicy:
        return self._vertical_size_policy

    @vertical_size_policy.setter
    def vertical_size_policy(self, size_policy: SizePolicy):
        self._vertical_size_policy = Validator.ensure(size_policy, SizePolicy)
    
    @property
    def minimum_size(self) -> Size | None:
        return self._minimum_size
    
    @minimum_size.setter
    def minimum_size(self, size: Size | None):
        self._minimum_size = Validator.ensure(size, Size, None)

    @property
    def fixed_size(self) -> Size | None:
        return self.minimum_size if self.minimum_size == self.maximum_size else None
    
    @fixed_size.setter
    def fixed_size(self, size: Size | None):
        self.minimum_size = Validator.ensure(size, Size, None)
        self.maximum_size = Validator.ensure(size, Size, None)
    
    @property
    def maximum_size(self) -> Size | None:
        return self._maximum_size
    
    @maximum_size.setter
    def maximum_size(self, size: Size| None):
        self._maximum_size = Validator.ensure(size, Size, None)

        
    # ==========================================================================
    #  Public API
    # ==========================================================================

    def add_class(self, class_name: str) -> None:
        """Adds a css class to the widget"""
        class_name = Validator.ensure(class_name, str)

        if class_name.startswith('tz-'):
            raise TreezeValueError('class cannot start with "tz-". The "tz-" prefix is reserved by Treeze.')

        if class_name not in self._extra_classes:
            self._extra_classes.append(class_name)
            self._mark_dirty()


    def remove_class(self, class_name: str) -> None:
        """Removes a css class from the widget"""
        class_name = Validator.ensure(class_name, str)
        
        if class_name.startswith('tz-'):
            raise TreezeValueError('class cannot start with "tz-". The "tz-" prefixed classes cannot be modified.')

        if class_name in self._extra_classes:
            self._extra_classes.remove(class_name)
            self._mark_dirty()
    

    # ==========================================================================
    #  Private
    # ==========================================================================

    def _set_parent(self, widget: Container | None = None):
        """
        Sets a new parent on the widget.
        Exposed for container to call when capturing ownership
        """
        widget = Validator.ensure(widget, Widget, None)
        self._parent = widget
        self._container_orientation = widget._ORIENTATION if widget else None

    def _walk_widgets(self):
        """Yield any widgets owned by this widget. Used for event callback."""
        yield self

    def _set_session(self, session: Session | None = None) -> None:
        self._session = session

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

        # Collect main classes + extra framework classes from base -> subclass.
        for cls in reversed(type(self).mro()):
            css_class = cls.__dict__.get('_CSS_CLASS')

            if css_class is not None and css_class not in classes:
                classes.append(css_class)

            css_classes = cls.__dict__.get('_CSS_CLASSES', ())

            for css_class in css_classes:
                if css_class not in classes:
                    classes.append(css_class)

        # Add variant class.
        if self.variant != Variant.DEFAULT:
            classes.append(f'{main_css_class}-{self.variant}')

        # Add user-defined classes.
        for css_class in self._extra_classes:
            if css_class not in classes:
                classes.append(css_class)

        return classes

    def _styles(self) -> dict[str, str]:
        styles = {}

        # Size policies
        styles.update(self._styles_size_policy())
            
        if self.minimum_size:
            styles['min-width'] = f'{self.minimum_size.width}px'
            styles['min-height'] = f'{self.minimum_size.height}px'

        if self.maximum_size:
            styles['max-width'] = f'{self.maximum_size.width}px'
            styles['max-height'] = f'{self.maximum_size.height}px'

        if self.fixed_size:
            styles['width'] = f'{self.fixed_size.width}px'
            styles['height'] = f'{self.fixed_size.height}px'

        return styles
    
    def _styles_size_policy(self) -> dict[str, str]:
        styles = {}

        # Get axis size policies
        match self._container_orientation:
            case Orientation.HORIZONTAL:
                main_axis_size_policy = self.horizontal_size_policy
                cross_axis_size_policy = self.vertical_size_policy
            case Orientation.VERTICAL:
                main_axis_size_policy = self.vertical_size_policy
                cross_axis_size_policy = self.horizontal_size_policy
            case None:
                return {}
            case _:
                raise ValueError(f'Unsupported container orientation: {self._container_orientation!r}')
        
        # Map main axis to flex data
        match main_axis_size_policy:
            case SizePolicy.FIXED:
                main = '0 0 auto'
            case SizePolicy.MINIMUM | SizePolicy.PREFERRED:
                main = '0 1 auto'
            case SizePolicy.EXPANDING:
                main = '1 1 0'
            case _:
                raise ValueError(f'Unsupported main axis size policy: {main_axis_size_policy!r}')

        # Map cross axis to align-self
        match cross_axis_size_policy:
            case SizePolicy.EXPANDING:
                cross = 'stretch'
            case SizePolicy.FIXED | SizePolicy.MINIMUM | SizePolicy.PREFERRED:
                cross = 'flex-start'
            case _:
                raise ValueError(f'Unsupported cross axis size policy: {cross_axis_size_policy!r}')
        
        # Update styles
        styles['flex'] = main
        styles['align-self'] = cross

        return styles
    
    @abstractmethod
    def _render(self) -> Node:
        """Render method to implement in each widget"""
        raise NotImplementedError


    def _build(self) -> Node:
        """Render as a node, retain and return"""
        # TODO: implement dirty flags to use caching
        #if self._node is None:
        #    self._node = self._render()
            
        self._node = self._render()

        return self._node


    # ==========================================================================
    #  Internal
    # ==========================================================================

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