"""Unit tests for the status module."""

import pytest

from alc_aiidalab_widgets.widgets.status import Status


@pytest.mark.parametrize("state", ("success", "failure", "warning"))
def test_status_widget_basics(state: str):
    """Test the basic status widget."""
    widget = Status()
    message = "Great job"
    status = Status._Stat[state.upper()]

    getattr(widget, state)(message)

    assert widget.value == getattr(Status, f"_s_{state}")(message)
    assert widget.status is status

    widget.clear()
    assert widget.value == ""
    assert widget.status is None


@pytest.mark.parametrize("state", Status._Stat)
def test_status_widget_set(state: Status._Stat):
    """Test Status.set."""
    widget = Status()
    message = "Great job"

    widget.set(message, state)

    assert widget.value == getattr(Status, f"_s_{state.name.lower()}")(message)
    assert widget.status is state


@pytest.mark.parametrize(
    "widget", (Status(), Status(message="Great job", state=Status._Stat.SUCCESS))
)
@pytest.mark.parametrize("state", Status._Stat)
def test_status_widget_append(widget: Status, state: Status._Stat):
    """Test Status.append."""
    msg = widget.value

    widget.append("Wibble", state)

    assert widget.value == msg + getattr(Status, f"_s_{state.name.lower()}")("Wibble")
    assert widget.status is state
