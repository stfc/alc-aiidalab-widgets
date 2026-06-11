"""Select multiple buttons."""

from __future__ import annotations

from collections.abc import Iterable

import ipywidgets as ipw
from traitlets import HasTraits, Set, TraitError, Unicode


class MultiSelect(ipw.HBox, HasTraits):
    """Select multiple entries with buttons."""

    class _Set(Set):
        def validate(self, obj, trial):

            if trial and all(isinstance(elem, bool) for elem in trial):
                return super().validate(
                    obj,
                    {
                        label
                        for label, value in zip(obj.options, trial, strict=True)
                        if value
                    },
                )

            trial = set(trial)
            if extra := trial.difference(obj.options):
                raise TraitError(f"Invalid values in proposal ({extra}).")

            return super().validate(obj, trial)

    value = _Set(trait=Unicode())

    def __init__(
        self,
        options: Iterable[str],
        initial_value: Iterable[str] = frozenset(),
        **kwargs,
    ) -> None:
        self.options = tuple(options)

        self.buttons = {
            label: ipw.ToggleButton(value=False, description=label)
            for label in self.options
        }
        for button in self.buttons.values():
            button.observe(self._set_value, "value")
        self.observe(self._sync_buttons, "value")

        super().__init__([*self.buttons.values()], **kwargs)

        self.value = set(initial_value)

    def _set_value(self, _) -> None:
        self.value = {label for label, button in self.buttons.items() if button.value}

    def _sync_buttons(self, value):
        with self.hold_trait_notifications():
            for label, button in self.buttons.items():
                button.value = label in value["new"]
