"""Unit tests for the tables module."""

import numpy
from aiida.orm import ArrayData
from ipywidgets import HTML, Dropdown

from alc_aiidalab_widgets.widgets.plots import PlotWidget
from alc_aiidalab_widgets.widgets.tables import (
    GenericArrayDataTableWidget,
    XYZArrayDataTableWidget,
)


def test_xyz_arraydata_table():
    """Test XYZ data table creation and array selection."""
    array = ArrayData()
    array1 = numpy.zeros((3, 3), dtype=float)
    array1[0][0] = 5238.456789
    array2 = numpy.ones((3, 3), dtype=float)
    array2[0][0] = 4263.123456
    array.set_array("Array_1", array1)
    array.set_array("Array_2", array2)
    widget = XYZArrayDataTableWidget(array)
    assert isinstance(widget.children[0], Dropdown)
    assert isinstance(widget.children[1], HTML)
    assert "5238.456789" in widget.children[1].value
    assert "0.000000" in widget.children[1].value
    assert widget.children[0].value == "Array_1"
    widget.array_selector.index = 1
    assert "4263.123456" in widget.children[1].value
    assert widget.children[0].value == "Array_2"
    assert "1.000000" in widget.children[1].value


def test_generic_arraydata_table():
    """Test the basic arraydata table viewer."""
    array = ArrayData(
        {
            "Array_1": numpy.array([0, 1, 2, 32, 4, 5], dtype=float),
            "Array_2": numpy.array([0, 1, 2, 32, 4, 5], dtype=int),
            "Array_3": numpy.array([[0, 1, 2], [32, 4, 5]], dtype=int),
            "Array_4": numpy.zeros((2, 2, 2), dtype=float),
        }
    )
    widget = GenericArrayDataTableWidget(array)

    widget.show_selector.value = {"Array_1"}
    assert "32.00000" in widget.table.value
    assert "0.000000" in widget.table.value

    widget.show_selector.value = {"Array_2"}
    assert "32" in widget.table.value
    assert "1" in widget.table.value
    assert "Array_1" not in widget.table.value
    assert "Array_2" in widget.table.value

    widget.show_selector.value = {"Array_3"}
    assert "32" in widget.table.value
    assert "1" in widget.table.value
    assert "Array_2" not in widget.table.value
    assert "Array_3" in widget.table.value

    widget.show_selector.value = {"Array_4"}
    assert "Too many dimensions" in widget.children[2].value


def test_generic_arraydata_plot_button():
    """The plot button replaces the table with an interactive PlotWidget."""
    array = ArrayData()
    array.set_array("Energy_series", numpy.array([0.0, 1.0, 4.0, 9.0]))
    array.set_array("Other", numpy.array([5.0, 6.0, 7.0]))
    widget = GenericArrayDataTableWidget(array)

    widget.show_selector.value = {"Energy_series"}

    # Before clicking, the plot button is present.
    assert widget.show_plt_btn in widget.plots.children

    # Simulate a user clicking the button (triggers the on_click callback).
    widget.show_plt_btn.click()

    # The table is now replaced by a PlotWidget for the selected array.
    plot = widget.children[1]
    assert isinstance(plot, PlotWidget)
    assert numpy.array_equal(plot.figure.data[0].y, array.get_array("Energy_series"))
    # The y label is derived from the (prettified) array name.
    assert plot.figure.layout.yaxis.title.text == "Energy_series"


def test_plot_button_uses_selected_array():
    """Plotting reflects the currently selected array."""
    array = ArrayData()
    array.set_array("Array_1", numpy.array([0.0, 1.0, 2.0]))
    array.set_array("Array_2", numpy.array([9.0, 8.0, 7.0]))
    widget = GenericArrayDataTableWidget(array)

    widget.show_selector.value = {"Array_2"}
    widget.show_plt_btn.click()

    plot = widget.children[1]
    assert isinstance(plot, PlotWidget)
    assert numpy.array_equal(plot.figure.data[0].y, array.get_array("Array_2"))
