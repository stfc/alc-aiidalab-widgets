"""Viewer for ExtXYZ info."""

from collections import defaultdict

import ase.io
import ipywidgets as ipw
import numpy as np
from aiida.orm import ArrayData, SinglefileData

from alc_aiidalab_widgets.utils import tab_from_dict
from alc_aiidalab_widgets.widgets import StructureViewWidget
from alc_aiidalab_widgets.widgets.tables import GenericArrayDataTableWidget

STRESS_LABELS = ("xx", "yy", "zz", "yz", "xz", "xy")


def _rename(inp: str) -> str:
    if "stress" in inp:
        for i, lab in enumerate(STRESS_LABELS):
            inp = inp.replace(f"stress_{i}", f"stress_{lab}")

    return inp


class ExtXYZStatsViewer(ipw.VBox):
    """View ExtXYZ stats from e.g. AiiDA outputs."""

    def __init__(self, node: SinglefileData, **kwargs) -> None:
        self.output = ipw.Output()
        self.viewer = StructureViewWidget(node)
        with node.open(None, "r") as inp:
            data = ase.io.iread(inp, index=":", format="extxyz")

            info = defaultdict(list)

            for frame in data:
                units: dict[str, str] = frame.info.get("units", {})
                for key, val in frame.info.items():
                    match val:
                        case np.ndarray():
                            for i, v in np.ndenumerate(val):
                                ind = "_".join(map(str, i))
                                info[f"{key}_{ind}"].append(v)

                        case np.floating() | np.integer() | float() | int():
                            info[key].append(val)

        info = {_rename(key): np.array(val) for key, val in info.items()}

        self.table = GenericArrayDataTableWidget(ArrayData(info), units=units)

        tabs = tab_from_dict(
            ipw.Tab,
            {
                "Structure": self.viewer,
                "Data": self.table,
            },
        )
        super().__init__([tabs, self.output], **kwargs)
