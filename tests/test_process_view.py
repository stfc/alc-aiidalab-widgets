"""Tests for the process node viewer."""

from aiida.orm import CalcJobNode

from alc_aiidalab_widgets.widgets.process_node_view import ProcessNodeViewerWidget


def test_process_node_viewer_widget(aiida_profile):
    """Base test for the ProcessNodeViewerWidget."""
    process = CalcJobNode()
    process.label = "Process label"
    process.description = "Process Description"
    process.base.attributes.set("process_state", "finished")
    process.base.attributes.set("exit_status", 0)
    process.store()

    widget = ProcessNodeViewerWidget(process)

    assert widget.label_widget.value == "Process label"
    assert widget.description_widget.value == "Process Description"

    widget.label_widget.value = "New Label"
    widget.description_widget.value = "New Description"

    assert widget.label_widget.value == "New Label"
    assert widget.description_widget.value == "New Description"
