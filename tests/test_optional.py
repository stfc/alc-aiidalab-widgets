"""Unit tests for the optional widget."""

import pytest
from ipywidgets.widgets.widget_int import IntSlider

from alc_aiidalab_widgets.widgets.optional import Optional


@pytest.mark.parametrize("init", (1, None))
def test_init_optional(init: int | None):
    """Test initial_value on Optional."""
    widget = Optional(IntSlider(), initial_value=init)
    assert widget.value == init
    if init is not None:
        assert widget._target.value == init
    assert widget._option.value == (init is None)
    if init is None:
        assert widget._target.disabled


@pytest.mark.parametrize("value", (10, None))
def test_set_optional(value: int | None):
    """Test setting value on Optional."""
    widget = Optional(IntSlider(), initial_value=50)
    widget.value = value

    assert widget.value == value
    assert widget._option.value == (value is None)
    if value is not None:
        assert widget._target.value == value
    else:
        assert widget._target.value == 50
        assert widget._target.disabled
