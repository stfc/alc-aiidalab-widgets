"""Simple utils used in several widgets."""
from typing import TypeVar

import ipywidgets as ipw

AT = TypeVar("AT", ipw.Accordion, ipw.Tab)


def tab_from_dict(typ: type[AT], tabs: dict[str, ipw.Widget]) -> AT:
    """Create a tab or accordion from a dict.

    Dict maps titles to widgets.

    Parameters
    ----------
    typ : type[ipw.Accordion | ipw.Tab]
        Accordion or Tab to create.
    tabs : dict[str, ipw.Widget]
        Dict of tabs to widgets.

    Returns
    -------
    Accordion or Tab
        Constructed Accordion or Tab.
    """
    blk = typ(list(tabs.values()))
    for ind, name in enumerate(tabs):
        blk.set_title(ind, name)

    return blk
