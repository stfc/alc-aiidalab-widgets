"""Unit tests for the plots module."""

import numpy
import plotly.graph_objects as go
import pytest

from alc_aiidalab_widgets.widgets.plots import PlotWidget


def test_single_array():
    """A single 1D array is plotted as one series against its index."""
    y = numpy.array([0.0, 1.0, 4.0, 9.0])
    widget = PlotWidget(data_series=y, y_label="Energy")

    # The figure widget is the sole child.
    assert len(widget.children) == 1
    assert isinstance(widget.children[0], go.FigureWidget)
    assert widget.children[0] is widget.figure

    # One trace holding the supplied y values against a default index.
    assert len(widget.figure.data) == 1
    trace = widget.figure.data[0]
    assert numpy.array_equal(trace.y, y)
    assert numpy.array_equal(trace.x, numpy.arange(len(y)))
    assert trace.name == "Series 1"
    assert trace.mode == "lines+markers"

    # Axis labels and (hidden) legend for a single series.
    assert widget.figure.layout.yaxis.title.text == "Energy"
    assert widget.figure.layout.xaxis.title.text == "Index"
    assert not widget.figure.layout.showlegend


def test_multiple_arrays():
    """A list of arrays produces one trace per series with a legend."""
    series = [numpy.arange(5), numpy.arange(5) * 2]
    widget = PlotWidget(data_series=series)

    assert len(widget.figure.data) == 2
    assert numpy.array_equal(widget.figure.data[0].y, series[0])
    assert numpy.array_equal(widget.figure.data[1].y, series[1])
    assert [trace.name for trace in widget.figure.data] == ["Series 1", "Series 2"]
    assert widget.figure.layout.showlegend


def test_shared_x_values():
    """Explicit x values are used for every series."""
    x = numpy.array([10, 20, 30])
    widget = PlotWidget(
        data_series=[numpy.array([1, 2, 3]), numpy.array([4, 5, 6])],
        x_values=x,
    )
    assert numpy.array_equal(widget.figure.data[0].x, x)
    assert numpy.array_equal(widget.figure.data[1].x, x)


def test_custom_labels_and_title():
    """Axis labels, title and series labels are applied."""
    widget = PlotWidget(
        data_series=[numpy.arange(3)],
        y_label="Force",
        x_label="Step",
        series_labels=["Fx"],
        title="My plot",
    )
    assert widget.figure.layout.xaxis.title.text == "Step"
    assert widget.figure.layout.yaxis.title.text == "Force"
    assert widget.figure.layout.title.text == "My plot"
    assert widget.figure.data[0].name == "Fx"


def test_series_label_count_mismatch():
    """A mismatched number of series labels raises ValueError."""
    with pytest.raises(ValueError, match="series labels"):
        PlotWidget(
            data_series=[numpy.arange(3), numpy.arange(3)],
            series_labels=["only one"],
        )


def test_x_values_length_mismatch():
    """Test that x values differing in length from a series raise ValueError."""
    with pytest.raises(ValueError, match="x values"):
        PlotWidget(data_series=numpy.arange(5), x_values=numpy.arange(3))
