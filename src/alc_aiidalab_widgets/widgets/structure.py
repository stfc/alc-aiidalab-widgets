"""Defines a widget for visualisation of chemical structures."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from aiida.orm import Node, SinglefileData, StructureData, TrajectoryData
from ase import Atoms
from ase import io as ase_io
from ipywidgets import HTML, VBox
from weas_widget import WeasWidget


class StructureViewWidget(VBox):
    """Visualise atom structure using weas_widget."""

    def __init__(self, node: Node | None = None, **kwargs):
        """StructureViewWidget constructor."""
        super().__init__(**kwargs)
        self.message = HTML("<p>No Structure Currently Loaded</p>")
        self.viewer = None
        self.children = [
            self.message,
        ]
        if isinstance(node, StructureData):
            self.assign_structure_from_structuredata(node)
        elif isinstance(node, SinglefileData):
            self.assign_structure_from_file(node.filename, node.content)
        elif isinstance(node, TrajectoryData):
            self.assign_structure_from_trajectorydata(node)
        elif node:
            self.message.value = (
                "<p>AiiDA Node type not supported by the structure viewer."
            )

    def assign_structure_from_file(
        self, fname: str, content: bytes, format: str | None = None
    ) -> None:
        """Visualise the given structure from a file.

        Parameters
        ----------
        fname: str
            The structure file path.
        content: bytes
            The content of the file.
        format: str | None
            An optional format specifier compatible with ASE. By default it is set
            to None which results in ASE auto-detecting the file format from the
            filename/extension.
        """
        suffix = "".join(Path(fname).suffixes)
        with NamedTemporaryFile(suffix=suffix) as tmpf:
            tmpf.write(content)
            tmpf.flush()
            try:
                structure = ase_io.read(tmpf.name, index=":", format=format)[0]
            except (KeyError, ase_io.formats.UnknownFileTypeError):
                self.message = HTML("<p>Could not visualise structure...</p>")
                self.children = [
                    self.message,
                ]
            else:
                self.viewer = WeasWidget()
                self.viewer.from_ase(structure)
                self.children = [
                    self.viewer,
                ]
        return

    def assign_structure_from_ase(self, structure: Atoms | list[Atoms]) -> None:
        """Visualise the given ASE structure.

        Parameters
        ----------
        structure: Atoms | list[Atoms]
            The ASE atoms structure(s) object.
        """
        self.viewer = WeasWidget()
        self.viewer.from_ase(structure)
        self.children = [
            self.viewer,
        ]
        return

    def assign_structure_from_structuredata(self, structure: StructureData) -> None:
        """Visualise the given AiiDA StructureData object.

        Parameters
        ----------
        structure: StructureData
            The AiiDA StructureData object.
        """
        self.assign_structure_from_ase(structure._get_object_ase())
        return

    def assign_structure_from_trajectorydata(self, trajectory: TrajectoryData) -> None:
        """
        Visualise a series of structures contained in an AiiDA TrajectoryData node.

        Parameters
        ----------
        trajectory: TrajectoryData
            The AiiDA TrajectoryData node containing the structure series to visualise.
        """
        symbols = trajectory.symbols
        positions = trajectory.get_positions()
        nsteps = trajectory.numsteps
        atoms = []
        for i in range(nsteps):
            step = Atoms(symbols=symbols, positions=positions[i])
            atoms.append(step)
        self.assign_structure_from_ase(atoms)
        return
