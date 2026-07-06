"""Widgets used for displaying tabular information."""

from aiida.orm import ArrayData
from ipywidgets import HTML, Dropdown, VBox
from numpy import floating as npfloat


class XYZArrayDataTableWidget(VBox):
    """
    Custom widget to display array data associated with XYZ coordinates.

    Create a table based widget for displaying different arrays within
    an ArrayData object assuming that all the data is XYZ based i.e
    atomic positions of forces.
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

        return

    def _render_array(self, change) -> None:
        """Create a HTML table based on the currently selected array."""
        index = change["new"]
        if index == change["old"]:
            return
        values = self.array.get_array(self.array_names[index])
        # Construct HTML Table
        html = "<table style='width:100%; border: 1px solid #ddd; text-align: left; "
        html += "border-collapse: collapse;'>"
        html += "<tr style='background-color: #2196F3; color: white;'>"
        html += "<th> </th><th>X</th><th>Y</th><th>Z</th></tr>"

        for idx, row in enumerate(values):
            bg_color = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
            html += f"<tr style='background-color: {bg_color};'>"
            html += f"<td><b>{idx}</b></td><td>{row[0]:.6f}</td><td>{row[1]:.6f}</td>"
            html += f"<td>{row[2]:.6f}</td>"
            html += "</tr>"
        html += "</table>"

        self.children = [self.array_selector, HTML(html)]
        return


class GenericArrayDataTableWidget(VBox):
    """Custom widget to display generic array data as a table."""

    def __init__(self, array: ArrayData, **kwargs):
        """GenericArrayDataTableWidget Constructor."""
        super().__init__(**kwargs)
        self.array = array
        self.array_selector = Dropdown(
            options=self.array.get_arraynames(),
            description="Array Labels:",
            layout={"width": "50%"},
            **kwargs,
        )
        self._render_array({"new": self.array_selector.index, "old": -1})
        self.array_selector.observe(self._render_array, "index")
        return

    def _render_array(self, change: dict) -> None:
        """Create a HTML table based on the currently selected array."""
        index = change["new"]
        if index == change["old"]:
            return
        values = self.array.get_array(self.array.get_arraynames()[index])
        if len(values.shape) > 2:
            self.children = [
                self.array_selector,
                HTML("<p>To many dimensions to create 2D table from array.</p>"),
            ]
            return
        if len(values.shape) == 1:
            nrows = values.shape[0]
            ncols = 1
        else:
            ncols, nrows = values.shape  # type: ignore

        # Build Table Header (Column Indices)
        html = "<table style='width:100%; border: 1px solid #ddd; text-align: left; "
        html += "border-collapse: collapse;'>"
        html += "<tr style='background-color: #2196F3; color: white;'>"
        html += "<th>Index</th>"
        if ncols > 1:
            for c in range(ncols):
                html += f"<th>{c}</th>"
        else:
            col_header = (
                self.array.get_arraynames()[index].replace("_", " ").capitalize()
            )
            html += f"<th>{col_header}</th>"
        html += "</tr></thead><tbody>"

        # Build Table Body (Row Index + Cell Data)
        for r in range(nrows):
            html += "<tr>"
            html += f'<th class="row-idx">{r}</th>'
            if ncols > 1:
                for c in range(ncols):
                    formatted_val = (
                        f"{values[c, r]}"
                        if isinstance(values[c, r], float | npfloat)
                        else str(values[c, r])
                    )
                    html += f"<td>{formatted_val}</td>"
            else:
                formatted_val = (
                    f"{values[r]:.6f}"
                    if isinstance(values[r], float | npfloat)
                    else str(values[r])
                )
                html += f"<td>{formatted_val}</td>"
            html += "</tr>"

        html += "</tbody></table></div>"
        self.children = [self.array_selector, HTML(html)]
        return
