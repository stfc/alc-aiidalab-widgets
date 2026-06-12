"""Standard form for an optional argument which can be disabled by a check box."""

from collections.abc import Callable, Iterable
from typing import Generic, Protocol, TypeVar

import ipywidgets as ipw
from traitlets import Any, dlink

T = TypeVar("T")


class _DisableWidget(Protocol[T]):
    value: T
    disabled: bool

    def observe(
        self, handler: Callable[..., Any], names: str | Iterable[str], type: str = ...
    ) -> None: ...


class Optional(Generic[T], ipw.HBox):
    """Class to handle a disable-able argument."""

    value = Any(allow_none=True)

    def __init__(
        self,
        target: _DisableWidget[T],
        *,
        initial_value: T | None = None,
        msg: str = "Disable",
        **kwargs,
    ):

        self._target = target
        self._option = ipw.Checkbox(description=msg)

        super().__init__(children=[self._target, self._option], **kwargs)
        if initial_value is None:
            self._option.value = True
            self._target.disabled = True
        else:
            self._target.value = initial_value

        self._option.observe(self._set_value, "value")
        self._target.observe(self._set_value, "value")
        dlink((self, "value"), (self._option, "value"), lambda x: x is None)
        dlink(
            (self, "value"),
            (self._target, "value"),
            lambda x: x if x is not None else self._target.value,
        )
        print("Wek")
        self.value = initial_value

    def _set_value(self, change: dict[str, T | bool]):
        value = change["new"]

        if isinstance(value, bool):
            self._target.disabled = value
            self.value = None if value else self._target.value
            return

        self.value = value
