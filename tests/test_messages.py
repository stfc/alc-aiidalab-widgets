"""Tests for the message widgets module."""

from alc_aiidalab_widgets.widgets.mesages import MessageBox


def test_message_box_widget():
    """Test the conditional continue style message box."""
    message = MessageBox("Do you want to continue...")

    assert "Do you want to continue..." in message.message.value, (
        "Message not correctly passed to message box HTML widget"
    )
    assert len(message.children) == 2
    assert message.state is None, "Wrong initial state for message box"
    message._set_state(True, None)
    assert message.state, "Failed to set message box state"
