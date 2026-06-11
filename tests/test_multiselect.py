"""Unit tests for the multiselect widget."""

import pytest
from traitlets import TraitError

from alc_aiidalab_widgets.widgets.multiselect import MultiSelect


@pytest.fixture
def select(request):
    """Get standard MultiSelect for testing."""
    return MultiSelect(options=("Tom", "Dick", "Harry"), **request.param)


@pytest.mark.parametrize("select", ({},), indirect=True)
@pytest.mark.parametrize(
    "val,expected",
    (
        ((), set()),
        ({"Tom", "Dick"}, {"Tom", "Dick"}),
        (("Tom", "Dick"), {"Tom", "Dick"}),
        (["Tom", "Dick"], {"Tom", "Dick"}),
        ([True, True, False], {"Tom", "Dick"}),
        ((True, True, False), {"Tom", "Dick"}),
        ("Tom", {"Tom"}),
    ),
)
def test_multiselect(select, val, expected):
    """Test setting values."""
    select.value = val
    assert select.value == expected


@pytest.mark.parametrize(
    "select,expected",
    (
        ({}, set()),
        ({"initial_value": {"Tom"}}, {"Tom"}),
    ),
    indirect=["select"],
)
def test_multiselect_default(select, expected):
    """Check initial value works."""
    assert select.value == expected


@pytest.mark.parametrize("select", ({},), indirect=True)
@pytest.mark.parametrize(
    "trial,expected",
    (
        ({"John"}, TraitError),
        ([True, True], ValueError),
        ("Tom,Dick", TraitError),
    ),
)
def test_multiselect_invalid(select, trial, expected):
    """Check invalid inputs fail."""
    with pytest.raises(expected):
        select.value = trial
