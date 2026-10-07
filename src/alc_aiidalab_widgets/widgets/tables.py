"""Widgets used for displaying tabular information."""

from collections.abc import Iterable
from itertools import zip_longest
from pathlib import Path
from typing import TextIO

import numpy as np
from aiida.orm import ArrayData
from ipywidgets import HTML, Button, Dropdown, HBox, Layout, VBox
from numpy import floating as npfloat
from numpy.typing import NDArray

from alc_aiidalab_widgets.widgets.multiselect import MultiSelect
from alc_aiidalab_widgets.widgets.plots import PlotWidget


class XYZArrayDataTableWidget(VBox):
    """
    Custom widget to display array data associated with XYZ coordinates.

    Create a table based widget for displaying different arrays within
    an ArrayData object assuming that all the data is XYZ based i.e
    atomic positions of forces.
    """

    DEFAULT_STYLE = """
    <style>
    table {border-collapse: collapse;}
    table, th, td { border: 1px solid #ddd; }
    tr:nth-child(odd) { background-color: #f9f9f9; }
    tr:nth-child(odd):hover { background-color:   #f5b7b1; }
    tr:nth-child(even):hover { background-color:  #f5b7b1; }
    th, td { padding: 10px; }
    td { min-width: 100px; text-align: center; border: none }
    th { text-align: center; border: none;  border-bottom: 1px solid black;}

    </style>
    """

    def __init__(self, array: ArrayData, **kwargs):
        """AiidaArrayDataViewWidget Constructor.

        Parameters
        ----------
        array : ArrayData
            The AiiDA ArrayData object to display.
        """
        super().__init__(**kwargs)
        self.array = array
        self.array_names = array.get_arraynames()

        self.array_selector = Dropdown(
            options=self.array_names,
            description="Array Label:",
            disabled=False,
            layout={"width": "30%"},
        )
        self._render_array({"new": self.array_selector.index, "old": -1})
        self.array_selector.observe(self._render_array, "index")

    def _render_array(self, change) -> None:
        """Create a HTML table based on the currently selected array."""
        index = change["new"]
        if index == change["old"]:
            return
        values = self.array.get_array(self.array_names[index])
        # Construct HTML Table
        html = "<table>"
        html += "<tr>"
        html += "<th></th><th>X</th><th>Y</th><th>Z</th></tr>"

        for idx, row in enumerate(values):
            html += "<tr>"
            html += f"<td><b>{idx}</b></td><td>{row[0]:.6f}</td><td>{row[1]:.6f}</td>"
            html += f"<td>{row[2]:.6f}</td>"
            html += "</tr>"
        html += "</table>"

        self.children = [self.array_selector, HTML(self.DEFAULT_STYLE + html)]


class GenericArrayDataTableWidget(VBox):
    """Custom widget to display generic array data as a table."""

    DEFAULT_STYLE = """
    <style>
    table {width=100%;}
    table, td { border: 1px solid black; }
    tr:nth-child(odd) { background-color: #e5e7e9; }
    tr:nth-child(odd):hover { background-color: #f5b7b1; }
    tr:nth-child(even):hover { background-color: #f5b7b1; }
    th, td { padding: 10px; }
    td { min-width: 100px; text-align: center; border: none }
    th { position: sticky; top: 0; text-align: center; border: none;
         border-bottom: 1px solid black; background-color: #2196F3; }
    #indexcol {background-color: #2196F3;}
    </style>
    """

    def __init__(self, array: ArrayData, **kwargs):
        """GenericArrayDataTableWidget Constructor."""
        super().__init__(**kwargs)
        self.array = array
        self.show_selector = MultiSelect(
            self.array.get_arraynames(),
            layout=Layout(display="flex", width="100%", flex_flow="row wrap"),
            button_kwargs={"layout": Layout(width="19%")},
            initial_value={*self.array.get_arraynames()},
        )
        self.x_selector = Dropdown(
            options=["Index", *self.array.get_arraynames()],
            description="X Axis:",
            layout={"width": "50%"},
            **kwargs,
        )
        self.deselect = Button(
            description="Clear selection",
            disabled=False,
            button_style="primary",
            tooltip="Clear currently selected graphs",
            layout={"align_self": "flex-end"},
        )
        self.select_all = Button(
            description="Select All",
            disabled=False,
            button_style="primary",
            tooltip="Clear currently selected graphs",
            layout={"align_self": "flex-end"},
        )
        self.show_plt_btn = Button(
            description="Plot Array",
            disabled=False,
            button_style="primary",
            tooltip="Plot the current data series",
            icon="chart-line",
            layout={"align_self": "flex-end"},
        )
        self.plots = HBox(
            [self.x_selector, self.select_all, self.deselect, self.show_plt_btn]
        )
        self.show_plt_btn.on_click(self._plot_data)
        self.deselect.on_click(self._deselect)
        self.select_all.on_click(self._select_all)
        self.show_selector.observe(self._render_array, "value")
        self._render_array()

    @classmethod
    def from_file(
        cls,
        file: TextIO | Iterable[str] | Path | str,
        header: Iterable[str] = (),
        **kwargs,
    ):
        """Create an table display from a file."""
        res = np.loadtxt(file, unpack=True, **kwargs)
        header = tuple(header)
        if not header:
            header = [f"Column_{i}" for i, _ in enumerate(res, 1)]
        return cls(ArrayData(dict(zip(header, res, strict=True))))

    def _deselect(self, _) -> None:
        self.show_selector.value = set()

    def _select_all(self, _) -> None:
        self.show_selector.value = set(self.show_selector.options)

    @property
    def _col_mapping(self) -> dict[str, NDArray] | None:
        cols = [
            name
            for name in self.array.get_arraynames()
            if name in self.show_selector.value
        ]
        values = [self.array.get_array(col) for col in cols]

        if any(value.ndim > 2 for value in values):
            return None

        columns = {}
        for col, value in zip(cols, values, strict=True):
            if value.ndim == 2:
                columns.update(
                    {f"{col}_{i}": value[:, i] for i in range(value.shape[1])}
                )
            else:
                columns[col] = value

        return columns

    def _render_array(self, *_) -> None:
        """Create a HTML table based on the currently selected array."""
        mapping = self._col_mapping

        if mapping is None:
            self.children = [
                self.plots,
                self.show_selector,
                HTML("<p>Too many dimensions to create 2D table from array.</p>"),
            ]
            return

        html = (
            "<div style='max-height: 22em; overflow-y: auto;'>"
            "<table><thead><tr>"
            "<th>Index</th>"
            + "".join(f"<th>{col}</th>" for col in mapping)
            + "</tr></thead>"
        )

        for r, row in enumerate(zip_longest(*mapping.values(), fillvalue="-")):
            html += "<tr>"
            html += f"<td id='indexcol'>{r}</td>"
            for elem in row:
                formatted_val = (
                    f"{elem:.6f}" if isinstance(elem, (float, npfloat)) else str(elem)
                )
                html += f"<td>{formatted_val}</td>"
            html += "</tr>"

        html += "</tbody></table></div>"
        self.table = HTML(self.DEFAULT_STYLE + html)
        self.children = [self.plots, self.show_selector, self.table]

    def _plot_data(self, _=None) -> None:
        """Plot the currently selected array data."""
        mapping = self._col_mapping

        if mapping is None:
            return

        x_values = (
            self.array.get_array(self.x_selector.value)
            if self.x_selector.value != "Index"
            else None
        )
        y_values = [*mapping.values()]

        opts = (
            {"y_label": next(col for col in mapping)}
            if len(mapping) == 1
            else {"series_labels": [*mapping], "y_label": ""}
        )

        plot_widget = PlotWidget(
            data_series=y_values,
            x_values=x_values,
            x_label=self.x_selector.value,
            **opts,
        )

        self.children = [self.plots, plot_widget, self.show_selector, self.table]
