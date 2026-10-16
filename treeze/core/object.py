"""
Name:         object.py
Description:  Base class for treeze objects

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
from typing import Any

from .exceptions import TreezeRuntimeError
from .signals import BoundSignal, Signal

# ______________________________________________________________________________________________________________________

class Object:

    def __init__(self):
        super().__init__()
        self._signals: dict[str, BoundSignal] = {}
        for signal_name, signal in type(self)._declared_signals().items():
            self._create_signal(signal_name, signal.arg_types)

    @property
    def signals(self) -> tuple[BoundSignal, ...]:
        return tuple(self._signals.values())

    def _signal_changed(self) -> None:
        """Notify subclasses when signal connections or bound actions change."""
        pass

    def _assign_dynamic_signal(self, name: str, signal: Signal) -> BoundSignal:
        if '_signals' not in self.__dict__:
            raise TreezeRuntimeError(f'Cannot assign signal {name!r} before Object.__init__() has run.')

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
                f'{type(self).__name__!r} has no signal named {name!r}.'
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

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, Signal):
            self._assign_dynamic_signal(name, value)
            self._signal_changed()
            return

        if '_signals' in self.__dict__ and self._has_signal(name):
            raise TreezeRuntimeError(f'Signal {name!r} already connected.')

        super().__setattr__(name, value)
