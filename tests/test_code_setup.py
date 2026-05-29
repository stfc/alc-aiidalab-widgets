"""Unit tests for the code_setup module."""

from alc_aiidalab_widgets.widgets.code_setup import CodeSetupWidget

AIIDA_DEFAULT_DATABASE = (
    "https://aiidateam.github.io/aiida-resource-registry/database.json"
)


def test_remote_resource_database():
    """Test switching the source database for resource quick setup."""
    widget = CodeSetupWidget()

    domains = list(widget.resource_widget.comp_resources_database.database.keys())
    assert "scarf" in domains[0]

    widget.source.value = AIIDA_DEFAULT_DATABASE
    domains = list(widget.resource_widget.comp_resources_database.database.keys())
    assert "scarf" not in domains[0]
    assert "eiger" in domains[0]
