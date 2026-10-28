"""Viewer for ExtXYZ info."""

from collections import defaultdict

import ase.io
import ipywidgets as ipw
import numpy as np
from aiida.orm import ArrayData, SinglefileData

from alc_aiidalab_widgets.utils import tab_from_dict
from alc_aiidalab_widgets.widgets import StructureViewWidget
from alc_aiidalab_widgets.widgets.tables import GenericArrayDataTableWidget


class ExtXYZStatsViewer(ipw.VBox):
    """View ExtXYZ stats from e.g. AiiDA outputs."""

    def __init__(self, node: SinglefileData, **kwargs) -> None:
        self.output = ipw.Output()
        self.viewer = StructureViewWidget(node)
        with node.open(None, "r") as inp:
            data = ase.io.iread(inp, index=":", format="extxyz")

            info = defaultdict(list)
            for frame in data:
                for key, val in frame.info.items():
                    if isinstance(val, (np.ndarray, np.floating)):
                        info[key].append(val)

        info = {key: np.array(val) for key, val in info.items()}

        self.table = GenericArrayDataTableWidget(ArrayData(info))

        tabs = tab_from_dict(
            ipw.Tab,
            {
                "Structure": self.viewer,
                "Data": self.table,
            },
        )
        super().__init__([tabs, self.output], **kwargs)
