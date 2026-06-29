"""Defines custom viewers for AiiDA nodes."""

from alc_aiidalab_widgets.widgets.file_viewer import SinglefileDataViewer
from alc_aiidalab_widgets.widgets.process_node_view import ProcessNodeViewerWidget
from alc_aiidalab_widgets.widgets.structure import StructureViewWidget
from alc_aiidalab_widgets.widgets.tables import XYZArrayDataTableWidget

ALC_AIIDA_VIEWER_MAPPING = {
    # Process node type labels
    "process.calculation.calcfunction.CalcFunctionNode.": ProcessNodeViewerWidget,
    "process.calculation.calcjob.CalcJobNode.": ProcessNodeViewerWidget,
    "process.workflow.workfunction.WorkFunctionNode.": ProcessNodeViewerWidget,
    "process.workflow.workchain.WorkChainNode.": ProcessNodeViewerWidget,
    # AiiDA data type labels
    "data.core.structure.StructureData.": StructureViewWidget,
    "data.core.singlefile.SinglefileData.": SinglefileDataViewer,
    # Custom redirections
    "xyz_table": XYZArrayDataTableWidget,
}
