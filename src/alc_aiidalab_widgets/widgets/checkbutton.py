"""Check button widget."""

import ipywidgets as ipw
from traitlets import observe

from alc_aiidalab_widgets.types import CallbackDict


class CheckButton(ipw.ToggleButton):
    """Custom button with toggling checkmark."""

    @observe("value")
    def _value_changed(self, change: CallbackDict[bool]):
        self.icon = "check" if change["new"] else ""
