"""Standard types used in UI."""

from datetime import datetime
from typing import Generic, Protocol, TypeVar

from traitlets import HasTraits, TraitType
from typing_extensions import NotRequired, TypedDict

from alc_aiidalab_widgets.widgets.status import Status

T = TypeVar("T")



class ValueWidget(Protocol):
    """Widget that can be used for the input of an interactive function."""

    value: TraitType


class CallbackDict(TypedDict, Generic[T]):
    """Type documenting ``observe`` callback dicts."""

    type: str
    owner: NotRequired[HasTraits]
    old: NotRequired[T | None]
    new: NotRequired[T | None]
    name: NotRequired[str]


class FileUpload(TypedDict):
    """Result of a FileUpload widget."""

    name: str
    type: str
    size: int
    last_modified: datetime
    content: bytes


class HasStatus(Protocol):
    """Protocol for status traited entities."""

    status: Status
