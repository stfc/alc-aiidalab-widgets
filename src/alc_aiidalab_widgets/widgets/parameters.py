"""Parameters block widget."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import ipywidgets as ipw

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
