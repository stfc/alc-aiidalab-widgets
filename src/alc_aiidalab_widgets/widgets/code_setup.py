"""Defines a resource setup widget based on foundations from aiidalab-widgets-base."""

from aiidalab_widgets_base.computational_resources import ResourceSetupBaseWidget
from aiidalab_widgets_base.utils import StatusHTML
from ipywidgets import HTML, Text, VBox, dlink
from traitlets import HasTraits, Unicode, observe


class CodeSetupWidget(VBox, HasTraits):
    """Widget to setup a new code instance.

    Extends the existing ResourceSetupBaseWidget from aiidalab-widgets-base with the
    ability to alter the database source link. By default using this widget will
    point to the provided ALC resources database contained within the
    https://github.com/stfc/alc-ux repository.
    """

    _database_source = Unicode(
        "",
        allow_none=False,
    )

    def __init__(self, **kwargs):
        """CodeSetupWidget constructor."""
        self.source = Text(
            value=self._database_source, description="Source: ", layout={"width": "80%"}
        )
        dlink((self.source, "value"), (self, "_database_source"))
        self.resource_widget = ResourceSetupBaseWidget()
        self.setup_message = StatusHTML(clear_after=15)
        dlink(
            (self.resource_widget, "message"),
            (self.setup_message, "message"),
        )

        self.source.value = "https://raw.githubusercontent.com/stfc/alc-ux/refs/heads/main/resources/remotes.json"

        children = [
            HTML("<hr>"),
            self.source,
            HTML("<hr>"),
            self.resource_widget,
            self.setup_message,
        ]
        super().__init__(children=children, **kwargs)
        return

    @observe("_database_source")
    def _update_database_source(self, _):
        """Update the database source in the ResourceSetupBaseWidget."""
        self.resource_widget.comp_resources_database.database_source = (
            self._database_source
        )
        return
