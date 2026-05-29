"""Unit tests for file handling module."""

import datetime

from aiida.orm import SinglefileData
from ipywidgets import FileUpload
from traitlets.traitlets import TraitError

from alc_aiidalab_widgets.widgets.file_handling import FileUploadWidget


def test_file_upload():
    """Test uploading a single file object."""
    widget = FileUploadWidget("Test File:")
    assert widget.children[0].description == "Test File:"
    assert isinstance(widget.children[1], FileUpload)
    assert not widget.has_file

    # Simulate file upload
    test_file_content = b"Test file content..."
    try:
        widget.file_upload.value = (
            {
                "name": "test.txt",
                "type": "text",
                "size": len(test_file_content),
                "last_modified": datetime.datetime.now(),
                "content": memoryview(test_file_content),
            },
        )
    except TraitError:
        # This implies using pre- v8 ipywidgets so must use different approach
        widget.file_upload.metadata = [
            {
                "name": "test.txt",
                "type": "text",
                "size": len(test_file_content),
                "last_modified": datetime.datetime.now(),
                # "content": test_file_content,
            },
        ]
        widget.file_upload.data = [
            test_file_content,
        ]
        widget.file_upload._counter += 1

    assert widget.has_file

    assert widget.file_dict.get("name") == "test.txt"

    assert widget.get_file_contents().getvalue() == test_file_content
    assert widget.filename() == "test.txt"
    assert isinstance(widget.file, SinglefileData)
    assert widget.file.get_content("rb") == test_file_content

    widget.disable(True)
    assert widget.children[1].disabled
