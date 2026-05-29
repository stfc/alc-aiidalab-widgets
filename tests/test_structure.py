"""Unit tests for the structure module."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from aiida.orm import StructureData
from ipywidgets import HTML
from weas_widget import WeasWidget

from alc_aiidalab_widgets.widgets.structure import StructureViewWidget


def test_structure_load_from_file():
    """Create a WeasWidget visualisation of a molecule from an input file."""
    widget = StructureViewWidget()
    assert len(widget.children) == 1
    assert widget.viewer is None
    assert "<p>No Structure Currently Loaded</p>" in widget.children[0].value
    structure_file = Path(__file__).resolve().parent / "data/water.xyz"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 1
    structure_ase = widget.viewer.to_ase()
    assert structure_ase.get_atomic_numbers()[0] == 8
    assert structure_ase.get_atomic_numbers()[1] == 1
    assert structure_ase.get_atomic_numbers()[2] == 1


def test_structure_load_from_structuredata():
    """Create a WeasWidget visualisation of a molecule from AiiDA StructureData."""
    widget = StructureViewWidget()
    assert len(widget.children) == 1
    assert widget.viewer is None
    structure = StructureData()
    with open(Path(__file__).resolve().parent / "data/water.xyz") as f:
        structure._parse_xyz(f.read())
    widget.assign_structure_from_structuredata(structure)
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 1
    structure_ase = widget.viewer.to_ase()
    assert structure_ase.get_atomic_numbers()[0] == 8
    assert structure_ase.get_atomic_numbers()[1] == 1
    assert structure_ase.get_atomic_numbers()[2] == 1


def test_invalid_file_type():
    """Load an invalid filetype into a StructureViewWidget."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/water.xyz"
    with NamedTemporaryFile(suffix=".abc") as tmpf:
        tmpf.write(structure_file.read_bytes())
        tmpf.flush()
        widget.assign_structure_from_file(tmpf.name, structure_file.read_bytes())
    assert widget.viewer is None
    assert len(widget.children) == 1
    assert isinstance(widget.children[0], HTML)
    assert "Could not visualise structure" in widget.children[0].value
