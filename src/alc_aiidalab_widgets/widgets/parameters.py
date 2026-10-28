"""Parameters block widget."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

import ipywidgets as ipw
from traitlets import Dict, HasTraits, Unicode

from alc_aiidalab_widgets.types import ValueWidget
from alc_aiidalab_widgets.widgets.download import Download

if TYPE_CHECKING:
    from alc_aiidalab_widgets.types import CallbackDict, FileUpload


class ParametersBlock(ipw.GridspecLayout):
    """Block containings parameters settings.

    Parameters
    ----------
    name : str
        Name of parameter block/tab.
    widget_ref : dict[str, ipw.ValueWidget]
        Dictionary mapping parameter names to widgets.
    default_args : dict[str, Any]
        Dictionary of settings blocks -> Parameter settings.

        The keys will form the labels in the parameters dropdown.
        e.g.
        default_args = {"low_precision": {
                             "n_samples": 10,
                             "precision": "low",
                        }}
    """

    def __init__(
        self,
        name: str,
        widget_ref: dict[str, ValueWidget],
        default_args: dict[str, dict[str, Any]],
        **kwargs,
    ):

        self.name = name
        self.widget_ref = widget_ref

        self.output = ipw.Output()
        self.save_button = Download(
            description="Save",
            filename=f"{name}.json",
            layout={"width": "auto"},
            icon="download",
            cb=self.get_json,
            output=self.output,
        )
        self.load_button = ipw.FileUpload(
            description="Load",
            accept=".json",
            multiple=False,
            layout={"width": "auto"},
        )
        self.load_button.observe(self._load, names="value")

        self.defaults = {
            key: self.get(all=True) | val for key, val in default_args.items()
        }
        self.defaults_box = ipw.Dropdown(
            options=default_args.items(),
            value=next(iter(default_args.values()), {}),
            layout={"width": "auto"},
            description="Defaults:",
        )
        self.defaults_box.observe(self._from_defaults, names="value")

        super().__init__(3, 2, **kwargs, layout={"height": "max-content"})
        self[0, :2] = self.defaults_box
        self[1, 0] = self.save_button
        self[1, 1] = self.load_button
        self[2, :2] = self.output

        self.set(self.defaults_box.value)

    def get(
        self, widgets: dict[str, ValueWidget] | None = None, *, all: bool = False
    ) -> dict[str, Any]:
        """Get parameters as dictionary.

        Parameters
        ----------
        widgets : dict[str, ipw.ValueWidget], optional
            Override default widget set.

        Returns
        -------
        dict[str, Any]
            Dictionary of current values.
        """
        if widgets is None:
            widgets = self.widget_ref

        return {
            name: widget.value
            for name, widget in widgets.items()
            if all
            or (
                not getattr(widget, "disabled", False)
                and getattr(widget, "layout", ipw.Layout()).visibility != "hidden"
            )
        }

    def get_json(self, widgets: dict[str, ValueWidget] | None = None) -> str:
        """Get parameters as JSON string.

        Parameters
        ----------
        widgets : dict[str, ipw.ValueWidget], optional
            Override default widget set.

        Returns
        -------
        str
            JSON of parameters.
        """
        return json.dumps(self.get(widgets, all=True))

    def set(
        self, values: dict[str, Any], widgets: dict[str, ValueWidget] | None = None
    ) -> None:
        """Set parameters from dictionary.

        Parameters
        ----------
        values : dict[str, Any]
            Values to set.
        widgets : dict[str, ipw.ValueWidget], optional
            Override default widget set.
        """
        if widgets is None:
            widgets = self.widget_ref

        for name, value in values.items():
            widgets[name].value = value

    def _from_defaults(self, change: CallbackDict[dict[str, Any]]) -> None:
        if not change["new"]:
            return

        self.set(change["new"])

    def _load(self, change: CallbackDict[dict[str, FileUpload]]) -> None:
        if not change["new"]:
            return

        uploaded = change["new"]
        filename: str = next(iter(uploaded.keys()))

        content = uploaded[filename]["content"].decode("ascii")
        params = json.loads(content)

        self.set(params)


class ParamEntry(ipw.GridBox, HasTraits):
    """Entry for arbitrary parameters in dict."""

    value = Dict(key_Trait=Unicode())

    def __init__(
        self,
        *,
        allowed_keys: Iterable[str] | None = None,
        type_map: dict[str, type] | None = None,
        **kwargs,
    ) -> None:
        self.plist = ipw.Select(layout={"width": "60%"})
        self.key = ipw.Text(layout={"width": "50%"})
        self.val = ipw.Text(layout={"width": "50%"})
        self.add_b = ipw.Button(
            description="Add",
            button_style="success",
            icon="plus",
            layout={"width": "50%"},
        )
        self.rem_b = ipw.Button(
            description="Remove",
            button_style="success",
            icon="minus",
            layout={"width": "50%"},
        )

        entry = ipw.HBox([self.key, self.val], layout={"width": "60%"})
        buttons = ipw.HBox([self.add_b, self.rem_b], layout={"width": "60%"})

        self.allowed_keys = set(allowed_keys) if allowed_keys is not None else None
        self.type_map: Mapping[str, type] = defaultdict(lambda: str, type_map or {})

        self.add_b.on_click(self.add)
        self.rem_b.on_click(self.rem)
        self.plist.observe(self.sel, "value")
        self.observe(self.sync, "value")

        super().__init__(
            [self.plist, entry, buttons],
            **kwargs,
        )

    def sync(self, *_) -> None:
        """Synchronise dict and display."""
        self.plist.options = self.value.keys()

    def add(self, _) -> None:
        """Add key/val to params."""
        key, val = self.key.value, self.val.value

        if not key or self.allowed_keys is not None and key not in self.allowed_keys:
            return

        try:
            self.value[key] = self.type_map[key](val)
        except ValueError:
            return
        self.sync()

    def rem(self, _) -> None:
        """Remove key/val from params."""
        key = self.plist.value
        self.value.pop(key)
        self.sync()

    def sel(self, value: CallbackDict[str]) -> None:
        """Synchronise key/val with selection."""
        if (key := value.get("new")) is None:
            return

        self.key.value = key
        self.val.value = str(self.value[key])

    def as_dict(self) -> dict[str, Any]:
        """Get params as dictionary."""
        return self.value
