"""Widgets to visualise the contents of a file."""

from aiida.orm import SinglefileData
from ipywidgets import Textarea


class SinglefileDataViewer(Textarea):
    """Widget for visualising the contents of an AiiDA SingefileData node."""

    def __init__(self, node: SinglefileData, **kwargs):
        """SinglefileDataViewer constructor."""
        super().__init__(
            value=node.get_content(mode="r"),
            disabled=True,
            layout={"width": "100%"},
            rows=20,
            **kwargs,
        )
