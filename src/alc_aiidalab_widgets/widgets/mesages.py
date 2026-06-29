"""Widgets for displaying message box style notifications."""

from functools import partial

from ipywidgets import HTML, Button, HBox, VBox
from traitlets import Bool


class MessageBox(VBox):
    """A widget that displays a message and continue/cancel buttons."""

    state = Bool(None, allow_none=True)

    def __init__(self, message: str, **kwargs):
        """MessageBox Constructor."""
        super().__init__(**kwargs)
        self.message = HTML(f"<p>{message}</p>")
        self.buttons = HBox(**kwargs)
        self.accept_btn = Button(
            description="Accept",
            button_style="success",
            tooltip="Accept",
            icon="",
            # layout={"width": "100%"},
        )
        self.cancel_btn = Button(
            description="Cancel",
            button_style="warning",
            tooltip="Cancel",
            icon="",
            # layout={"width": "50%"},
        )
        self.accept_btn.on_click(partial(self._set_state, True))
        self.cancel_btn.on_click(partial(self._set_state, False))

        self.buttons.children = [self.accept_btn, self.cancel_btn]
        self.children = [self.message, self.buttons]

        return

    def _set_state(self, new_state, _) -> None:
        """Set the widgets state trait."""
        self.state = new_state
        return
