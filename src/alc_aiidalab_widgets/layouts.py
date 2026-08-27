"""Basic step layout."""
from aiidalab_widgets_base import WizardAppWidgetStep

from collections.abc import Collection, Iterable
from typing import Any

import ipywidgets as ipw

from alc_aiidalab_widgets.widgets.parameters import ParametersBlock
from alc_aiidalab_widgets.widgets.status import Status


class Step(ipw.AppLayout):
    """General step base layout."""

    def __init__(
        self,
        *,
        title: str,
        info: str,
        widgets: Iterable[ipw.Widget],
        submittable: bool = True,
        **kwargs: Any,
    ) -> None:
        self.title = ipw.HTML(f"<h3>{title}</h3>", layout={"margin": "auto"})
        self.info = ipw.HTML(f"<p>{info}</p>", layout={"margin": "auto"})
        self.status = Status(layout={"margin": "auto"})
        self.logspace = ipw.Output(layout={"margin": "auto"})

        if submittable:
            self.submit_btn = ipw.Button(
                description="Submit",
                button_style="success",
                tooltip="Submit the data to the workflow",
                icon="check",
                layout={"margin": "auto", "width": "60%"},
            )
            self.submit_btn.on_click(self.submit)
        else:
            self.submit_btn = ipw.HBox()

        super().__init__(
            header=ipw.VBox(
                [self.title, self.info], layout={"margin": "auto", "width": "100%"}
            ),
            center=ipw.VBox([*widgets], layout={"margin": "auto", "width": "100%"}),
            footer=ipw.VBox(
                [self.submit_btn, self.status, self.logspace],
                layout={"margin": "auto", "width": "100%"},
            ),
            **kwargs,
        )

    def submit(self, _):
        """Submit data."""
        if self.status.status is Status._Stat.SUCCESS:
            self.submit_btn.disabled = True
            self.submit_btn.description = "Submitted"


class ParameterStep(Step):
    """Step layout with parameters settings."""

    def __init__(
        self,
        *,
        default_args: dict[str, dict[str, Any]] | None = None,
        title: str,
        info: str,
        widgets: dict[str, ipw.ValueWidget],
        structure: Iterable[ipw.Widget] | None = None,
        exclude: Collection[str] = (),
        **kwargs: Any,
    ) -> None:
        if default_args is None:
            default_args = {}

        filtered = {
            name: widget for name, widget in widgets.items() if name not in exclude
        }
        self.param_block = ParametersBlock(title, filtered, default_args)

        self.widgets_map = widgets

        if structure is None:
            structure = widgets.values()

        super().__init__(
            title=title,
            info=info,
            widgets=structure,
            right_sidebar=self.param_block,
            **kwargs,
        )

    def get(self, *, all: bool = False) -> dict[str, Any]:
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
        return self.param_block.get(all=all)


class WizardStep(Step, WizardAppWidgetStep):
    """Combined wizard step and step for convenience."""
    def __init__(self, *args, **kwargs):
        self.state = self.State.INIT

        super().__init__(*args, **kwargs)
        self.submit_btn.disabled = True
        self.ready()

    def ready(self):
        self.state = self.State.READY

    def fail(self, message: str = ""):
        self.submit_btn.disabled = True
        if message:
            self.status.failure(message)
        self.state = self.State.FAIL

    def ok(self, message: str = ""):
        self.submit_btn.disabled = False
        if message:
            self.status.success(message)
        self.state = self.State.READY

    def running(self):
        self.state = self.State.ACTIVE

    def submit(self, b):
        super().submit(b)
        self.state = self.State.SUCCESS
