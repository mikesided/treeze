"""
Name:         signals.py
Description:  Signals base classes

"""

# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
import inspect
from collections.abc import Callable
from typing import Any, Protocol, overload, TYPE_CHECKING

from .client_action import ClientAction
from .exceptions import TreezeRuntimeError
from .validation import Validator

if TYPE_CHECKING:
    from .widget import Widget


# ______________________________________________________________________________________________________________________

class SignalOwner(Protocol):
    """Typing helper. Not a real concept."""
    def _get_signal(self, name: str) -> BoundSignal:
        ...

    def _mark_dirty(self) -> None:
        ...

    def execute(self, action: ClientAction) -> None:
        ...

class Signal:
    """
    Class-level signal.
    """
    def __init__(self, *arg_types: type):
        self.arg_types = arg_types
        self._name = None

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        if self._name is None:
            raise RuntimeError('Signal has not been bound to an instance.')

        return self._name

    def _bind_name(self, name: str) -> None:
        if self._name is None:
            self._name = name
            return

        if self._name != name:
            raise TreezeRuntimeError(
                f'Signal name mismatch: signal is named {self._name!r}, '
                f'but was assigned as {name!r}.'
            )

    @overload
    def __get__(self, instance: None, owner: type[Any]) -> Signal:
        ...

    @overload
    def __get__(self, instance: SignalOwner, owner: type[Any]) -> BoundSignal:
        ...

    def __get__(
        self,
        instance: SignalOwner | None,
        owner: type[Any],
    ) -> Signal | BoundSignal:
        if instance is None:
            return self

        return instance._get_signal(self.name)
    
    def __set__(self, instance: Any, value: Any) -> None:
        raise TreezeRuntimeError(
            f'Cannot assign to declared signal {self.name!r}. '
            f'Use {self.name}.connect(...) instead.'
        )


class BoundSignal:
    """
    Instance-level signal.

    This is what `widget.clicked` returns.
    Callback lists are stored here, not on the class-level Signal.
    """

    def __init__(
            self, 
            owner: SignalOwner, 
            name: str, 
            arg_types: tuple[type, ...] = (),
        ):
        self._owner = owner
        self._name = name
        self._arg_types = arg_types
        self._callbacks: list[tuple[Callable[..., Any], bool]] = []
        self._actions: list[ClientAction] = []

    @property
    def owner(self) -> SignalOwner:
        return self._owner

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def arg_types(self) -> tuple[type, ...]:
        return self._arg_types
    
    def connect(self, callback: Callable[..., Any]) -> None:
        """Connect a public callback to be called when this signal emits."""
        self._connect(callback, internal=False)

    def bind(self, action: ClientAction) -> None:
        """Bind a browser action, independently of Python callbacks."""
        Validator.ensure(action, ClientAction)
        self._actions.append(action)
        self._owner._mark_dirty()

    def unbind(self, action: ClientAction | None = None) -> None:
        """Remove one bound action, or all bound actions if None."""
        if action is None:
            if not self._actions:
                return
            self._actions.clear()
        else:
            try:
                self._actions.remove(action)
            except ValueError:
                raise TreezeRuntimeError(f'Action is not bound to signal {self._name!r}.') from None
        self._owner._mark_dirty()

    @property
    def actions(self) -> tuple[ClientAction, ...]:
        return tuple(self._actions)
        
    def disconnect(self, callback: Callable[..., Any] | None = None) -> None:
        """Disconnect a public callback, or all public callbacks if None."""
        self._disconnect(callback, internal=False)

    def _internal_connect(self, callback: Callable[..., Any]) -> None:
        """Connect a callback protected from disconnect()."""
        self._connect(callback, internal=True)

    def _connect(
        self,
        callback: Callable[..., Any],
        *,
        internal: bool,
    ) -> None:
        """Validate and store a public or internal connection."""
        if not callable(callback):
            raise TreezeRuntimeError(f'Signal callback for {self._name!r} must be callable.')

        self._validate_callback_accepts_declared_args(callback)

        self._callbacks.append((callback, internal))


    def _internal_disconnect(self, callback: Callable[..., Any] | None = None) -> None:
        """Disconnect an internal callback, or all internal callbacks if None."""
        self._disconnect(callback, internal=True)

    def _disconnect(
        self,
        callback: Callable[..., Any] | None,
        *,
        internal: bool,
    ) -> None:
        """Remove connections only from the requested public or internal group."""
        if callback is None:
            self._callbacks[:] = [
                connection for connection in self._callbacks if connection[1] != internal
            ]
            return

        for index, (connected, is_internal) in enumerate(self._callbacks):
            if is_internal == internal and connected == callback:
                del self._callbacks[index]
                return

        connection_type = 'internally' if internal else 'publicly'
        raise TreezeRuntimeError(
            f'Callback is not {connection_type} connected to signal {self._name!r}.'
        )

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """Trigger Python callbacks and queue bound actions for the browser."""
        self._emit(args, kwargs, execute_actions=True)

    def _emit(self, args: tuple[Any, ...], kwargs: dict[str, Any], *, execute_actions: bool) -> None:
        self._validate_emit_arguments(args, kwargs)
        actions = tuple(self._actions)

        for callback, _ in tuple(self._callbacks):
            self._validate_callback_signature(callback, args, kwargs)

            callback(*args, **kwargs)

        if execute_actions:
            for action in actions:
                self._owner.execute(action)

    def has_connections(self) -> bool:
        return bool(self._callbacks or self._actions)
    
    def _validate_emit_arguments(
            self,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> None:
        if kwargs:
            raise TreezeRuntimeError(
                f'Signal {self._name!r} only accepts positional arguments. '
                f'Got kwargs: {kwargs!r}.'
            )

        expected_count = len(self._arg_types)

        if len(args) != expected_count:
            raise TreezeRuntimeError(
                f'Signal {self._name!r} expected {expected_count} argument(s), '
                f'but got {len(args)}. '
                f'Expected types: {self._format_arg_types()}. '
                f'Emitted args: {args!r}.'
            )

        for index, expected_type in enumerate(self._arg_types):
            value = args[index]

            if not isinstance(value, expected_type):
                raise TreezeRuntimeError(
                    f'Signal {self._name!r} expected argument {index} to be '
                    f'{self._format_type(expected_type)}, '
                    f'but got {type(value).__name__}. '
                    f'Value: {value!r}.'
                )
            
    def _validate_callback_accepts_declared_args(
            self,
            callback: Callable[..., Any],
        ) -> None:
        try:
            signature = inspect.signature(callback)
        except (TypeError, ValueError):
            # Some builtins/callables do not expose a signature.
            # Let Python raise naturally if it cannot be called.
            return

        dummy_args = tuple(None for _ in self._arg_types)

        try:
            signature.bind(*dummy_args)
        except TypeError as error:
            raise TreezeRuntimeError(
                f'Callback {self._callback_name(callback)!r} connected to '
                f'signal {self._name!r} cannot accept the declared signal arguments. '
                f'Signal emits {len(self._arg_types)} argument(s): {self._format_arg_types()}. '
                f'Expected callback signature: {signature}.'
            ) from error
    
    def _validate_callback_signature(
        self,
        callback: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        try:
            signature = inspect.signature(callback)
        except (TypeError, ValueError):
            # Some builtins/callables do not expose a signature.
            # Let Python raise naturally if it cannot be called.
            return

        try:
            signature.bind(*args, **kwargs)
        except TypeError as error:
            raise TreezeRuntimeError(
                f'Callback {self._callback_name(callback)!r} connected to '
                f'signal {self._name!r} cannot accept the emitted arguments. '
                f'Emitted args: {args!r}, kwargs: {kwargs!r}. '
                f'Expected callback signature: {signature}.'
                f'In most cases, accepting at least (*args, **kwargs) in your callback solves this.'
            ) from error

    def _callback_name(self, callback: Callable[..., Any]) -> str:
        module = getattr(callback, '__module__', None)
        qualname = getattr(callback, '__qualname__', None)

        if module and qualname:
            return f'{module}.{qualname}'

        name = getattr(callback, '__name__', None)

        if name:
            return name

        return repr(callback)
    
    def _format_arg_types(self) -> str:
        if not self._arg_types:
            return '()'

        return '(' + ', '.join(
            self._format_type(arg_type)
            for arg_type in self._arg_types
        ) + ')'

    def _format_type(self, arg_type: type) -> str:
        return getattr(arg_type, '__name__', repr(arg_type))

    def _callback_name(self, callback: Callable[..., Any]) -> str:
        module = getattr(callback, '__module__', None)
        qualname = getattr(callback, '__qualname__', None)

        if module and qualname:
            return f'{module}.{qualname}'

        name = getattr(callback, '__name__', None)

        if name:
            return name

        return repr(callback)
