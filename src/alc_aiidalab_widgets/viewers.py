"""Defines custom viewers for AiiDA nodes."""

from alc_aiidalab_widgets.widgets.process_node_view import ProcessNodeViewerWidget
from alc_aiidalab_widgets.widgets.tables import XYZArrayDataTableWidget

ALC_AIIDA_VIEWER_MAPPING = {
    # Process node type labels
    "process.calculation.calcfunction.CalcFunctionNode.": ProcessNodeViewerWidget,
    "process.calculation.calcjob.CalcJobNode.": ProcessNodeViewerWidget,
    "process.workflow.workfunction.WorkFunctionNode.": ProcessNodeViewerWidget,
    "process.workflow.workchain.WorkChainNode.": ProcessNodeViewerWidget,
    # Custom redirections
    "xyz_table": XYZArrayDataTableWidget,
}
