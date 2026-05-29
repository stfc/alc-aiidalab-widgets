"""Unit tests for the loading module."""

from alc_aiidalab_widgets.widgets.loading import LoadingWidget


def test_loading_widget():
    """Test the basic loading widget."""
    widget = LoadingWidget()
    assert len(widget.children) == 2
    assert widget.children[0].value == "Loading"

    widget = LoadingWidget("Custom Message")
    assert widget.children[0].value == "Custom Message"
