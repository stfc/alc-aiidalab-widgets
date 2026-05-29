"""Basic step layout."""

from collections.abc import Iterable
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
        **kwargs: Any,
    ) -> None:
        self.title = ipw.HTML(f"<h3>{title}</h3>")
        self.info = ipw.HTML(f"<p>{info}</p>")
        self.status = Status()
        self.logspace = ipw.Output()

        super().__init__(
            header=ipw.VBox([self.title, self.info]),
            center=ipw.VBox([*widgets]),
            footer=ipw.VBox([self.status, self.logspace]),
            **kwargs,
        )


class ParameterStep(Step):
    """Step layout with parameters settings."""

    def __init__(
        self,
        *,
        default_args: dict[str, dict[str, Any]] | None = None,
        title: str,
        info: str,
        widgets: dict[str, ipw.ValueWidget],
        exclude: set[str] = frozenset(),
        **kwargs: Any,
    ) -> None:
        if default_args is None:
            default_args = {}

        filtered = {
            name: widget for name, widget in widgets.items() if name not in exclude
        }
        param_block = ParametersBlock(title, filtered, default_args)

        self.widgets_map = widgets

        super().__init__(
            title=title,
            info=info,
            widgets=widgets.values(),
            right_sidebar=param_block,
            **kwargs,
        )
