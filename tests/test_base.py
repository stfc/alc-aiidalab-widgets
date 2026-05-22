"""Test the base python package (i.e. has it been installed correctly)."""

import alc_aiidalab_widgets


def test_import():
    """Test whether the python package can be successfully imported."""
    assert alc_aiidalab_widgets.__version__ is not None
