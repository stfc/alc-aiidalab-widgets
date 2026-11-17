"""Unit tests for the structure module."""

import builtins
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pytest
from aiida.orm import SinglefileData, StructureData, TrajectoryData
from ase import Atoms
from ipywidgets import HTML
from weas_widget import WeasWidget

from alc_aiidalab_widgets.widgets.structure import (
    StructureViewWidget,
    build_binned_vector_field,
)


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


def test_structure_initialise_from_structuredata():
    """Create a WeasWidget viewer initialised with an AiiDA StructureData node."""
    structure = StructureData()
    with open(Path(__file__).resolve().parent / "data/water.xyz") as f:
        structure._parse_xyz(f.read())
    widget = StructureViewWidget(structure)
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 1
    structure_ase = widget.viewer.to_ase()
    assert structure_ase.get_atomic_numbers()[0] == 8
    assert structure_ase.get_atomic_numbers()[1] == 1
    assert structure_ase.get_atomic_numbers()[2] == 1


def test_structure_initialise_from_singlefiledata():
    """Create a WeasWidget viewer initialised with an AiiDA SingelfileData node."""
    structure_file = SinglefileData(Path(__file__).resolve().parent / "data/water.xyz")
    widget = StructureViewWidget(structure_file)
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 1
    structure_ase = widget.viewer.to_ase()
    assert structure_ase.get_atomic_numbers()[0] == 8
    assert structure_ase.get_atomic_numbers()[1] == 1
    assert structure_ase.get_atomic_numbers()[2] == 1


def test_structure_initialise_from_trajectorydata():
    """Create a WeasWidget viewer initialised with an AiiDA TrajectoryData node."""
    structure_1 = StructureData()
    with open(Path(__file__).resolve().parent / "data/water.xyz") as f:
        structure_1._parse_xyz(f.read())
    structure_2 = StructureData()
    with open(Path(__file__).resolve().parent / "data/water.xyz") as f:
        structure_2._parse_xyz(f.read())
    trajectory = TrajectoryData()
    trajectory.set_structurelist([structure_1, structure_2])
    widget = StructureViewWidget(trajectory)
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 1
    structure_ase = widget.viewer.to_ase()
    assert len(structure_ase) == 2
    assert structure_ase[0].get_atomic_numbers()[0] == 8
    assert structure_ase[0].get_atomic_numbers()[1] == 1
    assert structure_ase[0].get_atomic_numbers()[2] == 1


def _generate_magnetic_structure_data():
    """Build a small antiferromagnetic MagneticStructureData for testing."""
    pytest.importorskip("aiida_wannier90_workflows")
    from aiida_wannier90_workflows.data.structure import MagneticStructureData

    structure = MagneticStructureData(
        cell=[[4.8736, 0, 0], [0, 4.8736, 0], [0, 0, 3.3]]
    )
    structure.append_atom(
        position=[0.0, 0.0, 0.0], symbols="Mn", name="Mn0", magmom=(0.0, 0.0, 4.6)
    )
    structure.append_atom(
        position=[2.4368, 2.4368, 1.65],
        symbols="Mn",
        name="Mn1",
        magmom=(0.0, 0.0, -4.6),
    )
    zero_magmom = (0.0, 0.0, 0.0)
    structure.append_atom(position=[1.0, 1.0, 0.0], symbols="F", magmom=zero_magmom)
    structure.append_atom(position=[1.0, 3.0, 1.65], symbols="F", magmom=zero_magmom)
    return structure


def test_structure_initialise_from_magnetic_structuredata():
    """A MagneticStructureData node renders the structure and its moments."""
    structure = _generate_magnetic_structure_data()
    widget = StructureViewWidget(structure)
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 2
    assert widget._magnetic_toggle.value is True

    structure_ase = widget.viewer.to_ase()
    assert structure_ase.get_chemical_symbols().count("Mn") == 2
    assert structure_ase.get_chemical_symbols().count("F") == 2

    settings = widget.viewer.avr.vf.settings
    moments = settings["magnetic moment"]["vectors"]
    assert sorted(moment[2] for moment in moments) == pytest.approx([-4.6, 4.6])
    assert widget.viewer._widget.showVectorField is True


def test_assign_structure_from_magnetic_structuredata():
    """assign_structure_from_magnetic_structuredata can be called directly."""
    structure = _generate_magnetic_structure_data()
    widget = StructureViewWidget()
    widget.assign_structure_from_magnetic_structuredata(structure)
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 2
    settings = widget.viewer.avr.vf.settings
    assert len(settings["magnetic moment"]["vectors"]) == 2


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


def test_structure_load_from_mcif_file():
    """Loading a .mcif file renders the structure and the magnetic moments."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert isinstance(widget.viewer, WeasWidget)
    # Controls (visibility toggle + thickness slider) are shown alongside the
    # viewer for magnetic structures.
    assert len(widget.children) == 2
    assert widget.children[0] is widget._magnetic_controls
    assert widget._magnetic_toggle in widget._magnetic_controls.children
    assert widget._magnetic_thickness_slider in widget._magnetic_controls.children
    assert widget._magnetic_toggle.value is True
    assert widget._magnetic_thickness_slider.value == pytest.approx(0.1)

    structure_ase = widget.viewer.to_ase()
    assert structure_ase.get_chemical_symbols().count("Mn") == 2
    assert structure_ase.get_chemical_symbols().count("F") == 4

    settings = widget.viewer.avr.vf.settings
    moments = settings["magnetic moment"]["vectors"]
    assert sorted(moment[2] for moment in moments) == pytest.approx([-4.6, 4.6])
    assert widget.viewer._widget.showVectorField is True


def test_structure_load_from_mcif_file_with_dotted_filename():
    """A filename with multiple dots before the .mcif suffix is still detected."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file("0.15_MnF2.mcif", structure_file.read_bytes())
    assert isinstance(widget.viewer, WeasWidget)
    assert len(widget.children) == 2
    assert widget._magnetic_toggle.value is True


def test_mcif_toggle_controls_vector_field_visibility():
    """The magnetic moment toggle checkbox shows/hides the vector field."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert widget.viewer._widget.showVectorField is True
    widget._magnetic_toggle.value = False
    assert widget.viewer._widget.showVectorField is False


def test_mcif_thickness_slider_controls_vector_field_radius():
    """The arrow thickness slider updates the radius of every vector group."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert widget.viewer.avr.vf.settings["magnetic moment"]["radius"] == pytest.approx(
        0.1
    )
    widget._magnetic_thickness_slider.value = 0.25
    assert widget.viewer.avr.vf.settings["magnetic moment"]["radius"] == pytest.approx(
        0.25
    )


def test_set_magnetic_vectors_from_plain_sequence():
    """set_magnetic_vectors accepts one vector per atom and builds the group."""
    widget = StructureViewWidget()
    positions = [[0, 0, 0], [0, 0, 1], [0, 1, 0]]
    widget.assign_structure_from_ase(Atoms("H2O", positions=positions))
    assert len(widget.children) == 1

    widget.set_magnetic_vectors([[0, 0, 2.0], [0, 0, 0], [0, 0, -2.0]])
    assert len(widget.children) == 2
    settings = widget.viewer.avr.vf.settings
    assert settings["magnetic moment"]["origins"] == [[0, 0, 0], [0, 1, 0]]
    assert settings["magnetic moment"]["vectors"] == [[0, 0, 2.0], [0, 0, -2.0]]
    assert widget.viewer._widget.showVectorField is True


def test_set_magnetic_vectors_clears_vector_field():
    """Passing None removes an existing vector field and its controls."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert len(widget.children) == 2

    widget.set_magnetic_vectors(None)
    assert len(widget.children) == 1
    assert widget.viewer.avr.vf.settings == {}


def test_set_magnetic_vectors_without_structure_raises():
    """set_magnetic_vectors requires a structure to already be assigned."""
    widget = StructureViewWidget()
    with pytest.raises(RuntimeError):
        widget.set_magnetic_vectors([[0, 0, 1.0]])


def test_set_magnetic_vectors_rejects_plain_sequence_for_trajectory():
    """A plain vector sequence cannot be mapped onto a multi-frame trajectory."""
    widget = StructureViewWidget()
    widget.assign_structure_from_ase(
        [
            Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]]),
            Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]]),
        ]
    )
    with pytest.raises(ValueError, match="trajectory"):
        widget.set_magnetic_vectors([[0, 0, 1.0], [0, 0, 0], [0, 0, 0]])


def test_set_vector_field_from_dict():
    """set_vector_field accepts a settings dict for non-magnetic data too."""
    widget = StructureViewWidget()
    positions = [[0, 0, 0], [0, 0, 1], [0, 1, 0]]
    widget.assign_structure_from_ase(Atoms("H2O", positions=positions))

    custom_field = {
        "forces": {
            "origins": [[0, 0, 0]],
            "vectors": [[1.0, 0, 0]],
            "color": "green",
        }
    }
    widget.set_vector_field(custom_field)
    assert len(widget.children) == 2
    assert dict(widget.viewer.avr.vf.settings["forces"]) == custom_field["forces"]
    assert widget.viewer._widget.showVectorField is True


def test_set_vector_field_rebuilds_viewer_on_subsequent_calls():
    """A later call must rebuild the viewer, not update the existing one.

    Regression test: two earlier, less drastic fixes were tried and found
    insufficient in real browser use -- clearing `vf.settings` to `{}`
    immediately before the new dict, and issuing an explicit `avr.draw()`
    redraw command. Neither reliably discarded a previous vector field's
    stale arrows when the new one was smaller. Rebuilding the viewer from
    scratch is the only confirmed-working fix (a fresh viewer has nothing
    stale to leave behind); this asserts that rebuild actually happens (a
    new `viewer` object identity) while the displayed structure survives it
    unchanged.
    """
    widget = StructureViewWidget()
    widget.assign_structure_from_ase(
        Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]])
    )
    widget.set_vector_field(
        {"a": {"origins": [[0, 0, 0]], "vectors": [[1.0, 0, 0]], "color": "red"}}
    )
    first_viewer = widget.viewer

    widget.set_vector_field(
        {"b": {"origins": [[0, 0, 0]], "vectors": [[0, 1.0, 0]], "color": "blue"}}
    )

    assert widget.viewer is not first_viewer
    assert set(widget.viewer.avr.vf.settings.keys()) == {"b"}
    assert widget.to_ase().get_chemical_symbols() == ["H", "H", "O"]


def test_set_vector_field_does_not_rebuild_on_first_call():
    """The very first call (no stale field yet) should not need a rebuild."""
    widget = StructureViewWidget()
    widget.assign_structure_from_ase(Atoms("H2O", positions=[[0, 0, 0]] * 3))
    first_viewer = widget.viewer

    widget.set_vector_field(
        {"a": {"origins": [[0, 0, 0]], "vectors": [[1.0, 0, 0]], "color": "red"}}
    )

    assert widget.viewer is first_viewer


def test_set_vector_field_clears_vector_field():
    """Passing None removes an existing vector field and its controls."""
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert len(widget.children) == 2

    widget.set_vector_field(None)
    assert len(widget.children) == 1
    assert widget.viewer.avr.vf.settings == {}


def test_set_vector_field_without_structure_raises():
    """set_vector_field requires a structure to already be assigned."""
    widget = StructureViewWidget()
    with pytest.raises(RuntimeError):
        widget.set_vector_field({"forces": {"origins": [], "vectors": []}})


def test_mcif_missing_pymatgen_dependency(monkeypatch):
    """A helpful message is shown when pymatgen is not installed."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("pymatgen"):
            raise ImportError("No module named 'pymatgen'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    widget = StructureViewWidget()
    structure_file = Path(__file__).resolve().parent / "data/MnF2.mcif"
    widget.assign_structure_from_file(structure_file.name, structure_file.read_bytes())
    assert widget.viewer is None
    assert len(widget.children) == 1
    assert isinstance(widget.children[0], HTML)
    assert "pymatgen" in widget.children[0].value


def test_edited_flag_clean_after_programmatic_load():
    """The edit flag stays False when structures are assigned programmatically."""
    widget = StructureViewWidget()
    assert widget.edited is False
    widget.assign_structure_from_ase(
        Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]])
    )
    assert widget.edited is False
    # A subsequent programmatic load also leaves the structure unedited.
    widget.assign_structure_from_ase(
        Atoms("CO2", positions=[[0, 0, 0], [0, 0, 1.2], [0, 0, -1.2]])
    )
    assert widget.edited is False


def test_edited_flag_set_on_interactive_edit():
    """An interactive geometry edit sets the edit flag, which the parent can reset."""
    widget = StructureViewWidget()
    widget.assign_structure_from_ase(
        Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]])
    )
    assert widget.edited is False
    # Simulate an interactive edit: the frontend updates the atoms trait
    # asynchronously, i.e. outside the programmatic loading guard.
    edited_atoms = dict(
        widget.viewer.avr.atoms,
        positions=[[0, 0, 0.5], [0, 0, 1], [0, 1, 0]],
    )
    widget.viewer._widget.set_trait("atoms", edited_atoms)
    assert widget.edited is True
    # The parent is responsible for resetting the flag once handled.
    widget.edited = False
    assert widget.edited is False


def test_to_ase_and_to_aiida_without_structure():
    """The structure extractors return None when nothing is loaded."""
    widget = StructureViewWidget()
    assert widget.to_ase() is None
    assert widget.to_aiida() is None


def test_to_aiida_returns_structuredata():
    """to_aiida returns a valid StructureData node matching the displayed atoms."""
    positions = [[0, 0, 0], [0, 0, 1], [0, 1, 0]]
    widget = StructureViewWidget()
    widget.assign_structure_from_ase(Atoms("H2O", positions=positions))
    node = widget.to_aiida()
    assert isinstance(node, StructureData)
    # The node is valid and can be persisted to the AiiDA provenance graph.
    node.store()
    assert node.is_stored
    assert node.get_formula() == "H2O"
    # The atoms it holds match the structure that was displayed.
    structure_ase = node.get_ase()
    assert structure_ase.get_chemical_symbols() == ["H", "H", "O"]
    assert np.allclose(structure_ase.get_positions(), positions)


def test_build_binned_vector_field_groups_by_magnitude():
    """Magnitudes should be binned into equal-width, distinctly colored groups."""
    origins = [[0, 0, 0]] * 5
    vectors = [[1, 0, 0]] * 5
    magnitudes = [0.1, 0.2, 0.3, 5.0, 5.1]

    settings = build_binned_vector_field(origins, vectors, magnitudes, n_bins=3)

    assert len(settings) == 2
    total_arrows = sum(len(group["origins"]) for group in settings.values())
    assert total_arrows == 5
    colors = {group["color"] for group in settings.values()}
    assert len(colors) == 2


def test_build_binned_vector_field_empty():
    """An empty input should return an empty settings dict, not raise."""
    assert build_binned_vector_field([], [], []) == {}


def test_build_binned_vector_field_constant_magnitude():
    """All-equal magnitudes should fall into a single bin, not divide by zero."""
    settings = build_binned_vector_field(
        [[0, 0, 0], [1, 0, 0]], [[1, 0, 0], [1, 0, 0]], [2.0, 2.0]
    )

    assert len(settings) == 1
    (group,) = settings.values()
    assert len(group["origins"]) == 2


def test_build_binned_vector_field_arrow_length_normalises_magnitude():
    """`arrow_length` should rescale every vector to the same length.

    Direction and the magnitude-based color binning must be unaffected --
    only the drawn length changes, decoupling it from whatever unrelated
    quantity `vectors` happens to encode (e.g. bond distance).
    """
    vectors = [[1.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 10.0]]
    magnitudes = [5.0, 1.0, 0.1]

    settings = build_binned_vector_field(
        [[0, 0, 0]] * 3, vectors, magnitudes, arrow_length=2.0
    )

    lengths = [
        np.linalg.norm(vector)
        for group in settings.values()
        for vector in group["vectors"]
    ]
    assert all(np.isclose(length, 2.0) for length in lengths)
    assert len(lengths) == 3
