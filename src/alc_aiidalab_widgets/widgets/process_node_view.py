"""Visualisation widget for an AiiDA process node."""

from aiida.tools import delete_nodes
from aiidalab_widgets_base.viewers import (
    ProcessNodeViewerWidget as AiiDAlabProcessNodeViewerWidget,
)
from IPython.display import Javascript, display
from ipywidgets import HTML, Button, Text, Textarea, VBox


class ProcessNodeViewerWidget(VBox):
    """An extension of the AiiDAlab ProcessNodeViewerWidget."""

    def __init__(self, process, **kwargs):
        """CustomProcessNodeViewerWidget Constructor."""
        super().__init__(**kwargs)
        self.process = process
        self.label_widget = Text(
            value=process.label,
            disabled=False,
            description="Label: ",
            layout={"width": "70%"},
        )
        self.label_widget.observe(self._update_node_label, "value")
        self.description_widget = Textarea(
            value=process.description,
            disabled=False,
            description="Description:",
            layout={"width": "80%"},
        )
        self.description_widget.observe(self._update_node_description, "value")
        self.process_view = AiiDAlabProcessNodeViewerWidget(self.process)

        self.delete_btn = Button(
            description="Delete Node",
            button_style="warning",
            tooltip="Delete Process Node From Database",
            icon="trash",
            layout={"align_self": "flex-end"},
        )
        self.delete_btn.on_click(self._delete_node)

        self.children = [
            self.label_widget,
            self.description_widget,
            HTML("<hr>"),
            self.process_view,
            self.delete_btn,
        ]
        return

    def _update_node_label(self, change: dict) -> None:
        """Update the process node's label."""
        if change["new"] == change["old"]:
            return
        self.process.label = change["new"]
        return

    def _update_node_description(self, change: dict) -> None:
        """Update the process node's description."""
        if change["new"] == change["old"]:
            return
        self.process.description = change["new"]
        return

    def _delete_node(self, _) -> None:
        """Delete the current process node from the database."""
        delete_nodes([self.process.pk], dry_run=False)
        display(Javascript("window.location.reload();"))
