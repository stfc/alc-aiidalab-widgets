"""Unit tests for the database module."""

from aiida.orm import SinglefileData, StructureData
from traitlets.traitlets import TraitError

from alc_aiidalab_widgets.widgets.database import AiiDADatabaseQueryWidget


def test_database_query_default():
    """Test the default database query widget."""
    test_file = SinglefileData.from_string(
        "This is a test text file...", "test_file.txt"
    )
    test_file.store()
    widget = AiiDADatabaseQueryWidget(query=[SinglefileData, StructureData])
    assert len(widget.children) == 3
    assert widget.data_object is None

    widget.results.index = 1
    assert widget.data_object is not None
    assert isinstance(widget.data_object, SinglefileData)
    assert widget.data_object.get_content("r") == "This is a test text file..."

    try:
        widget.results.index = 2
    except TraitError:
        pass
    else:
        raise AssertionError("Results should only contain 1 object.")

    # "Calculated" filter
    widget.mode.index = 2
    assert widget.mode.value == "calculated"
    # Check that search has been re-triggered
    assert widget.data_object is None
    assert widget.results.index == 0
    # Search results should be empty
    try:
        widget.results.index = 1
    except TraitError:
        pass
    else:
        raise AssertionError("Results should be empty.")

    # Apply "Uploaded" filter
    widget.mode.index = 1
    assert widget.mode.value == "uploaded"
    # Check that search has been re-triggered
    assert widget.data_object is None
    assert widget.results.index == 0
    # Search results should be empty
    widget.results.index = 1
    assert isinstance(widget.data_object, SinglefileData)

    widget.disable(True)
    assert widget.results.disabled

    # Apply node type filter
    widget.drop_down.value = StructureData
    # Check that search has been re-triggered
    assert widget.data_object is None
    assert widget.results.index == 0
    # Search results should be empty
    try:
        widget.results.index = 1
    except TraitError:
        pass
    else:
        raise AssertionError("Results should be empty.")
