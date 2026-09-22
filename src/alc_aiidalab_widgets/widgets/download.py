"""Widget for downloading data."""

import base64
import mimetypes
from collections.abc import Callable
from typing import Any

import ipywidgets as ipw
from IPython.display import Javascript


class Download(ipw.Button):
    """Widget for downloading data.

    Parameters
    ----------
    filename : str
        Name to download data to by default.
    cb : Callable[[], str | bytes]
        Function which returns data to download.
    output : ipw.Output
        Output to write download to.
    mimetype : str, optional
        Result mimetype of data (if not given derived from filename).

    Notes
    -----
    Due to the nature of Jupyterlab, it is necessary
    to provide an output for the download to dump the
    necessary download Javascript to. This should
    be its own output since it will subsequently be cleared.
    """

    def __init__(
        self,
        filename: str,
        *,
        cb: Callable[[], str | bytes],
        output: ipw.Output,
        mimetype: str = "",
        **kwargs: Any,
    ) -> None:

        super().__init__(**kwargs)

        self.output = output

        self.cb = cb
        self.filename = filename
        if not mimetype:
            mimetype = mimetypes.guess_type(filename)[0] or "text/plain"

        self.mimetype = mimetype

        self.on_click(self._download)

    def _download(self, _b) -> None:
        data = self.cb()
        if isinstance(data, str):
            data = data.encode("utf-8")

        payload = base64.urlsafe_b64encode(data)
        action = Javascript(f"""
        var link = document.createElement("a");
        link.download = "{self.filename}";
        link.href = "data:{self.mimetype};base64,{payload.decode("ascii")}";
        link.click();
         """)

        self.output.append_display_data(action)
        self.output.clear_output()
