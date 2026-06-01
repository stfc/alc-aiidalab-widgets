"""Status holder widget."""

from enum import Enum, auto
from typing import ClassVar

import ipywidgets as ipw


class Status(ipw.HTML):
    """Status holder for standard warnings/messages."""

    class _Stat(Enum):
        SUCCESS = auto()
        FAILURE = auto()
        WARNING = auto()

    status: _Stat | None = None
    MAIN_STYLING: ClassVar[str] = "<p style='color: {colour};'>{message}</p>"

    def __init__(self, *args, message: str = "", state: _Stat | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        if state is None:
            self.clear()
            return

        self.set(message, state)

    @classmethod
    def _s_success(cls, message: str) -> str:
        return cls.MAIN_STYLING.format(colour="green", message=message)

    @classmethod
    def _s_failure(cls, message: str) -> str:
        return cls.MAIN_STYLING.format(colour="red", message=message)

    @classmethod
    def _s_warning(cls, message: str) -> str:
        return cls.MAIN_STYLING.format(colour="yellow", message=message)

    def _s_get(self, message: str, status: _Stat) -> str:
        self.status = status
        match self.status:
            case self._Stat.SUCCESS:
                return self._s_success(message)
            case self._Stat.FAILURE:
                return self._s_failure(message)
            case self._Stat.WARNING:
                return self._s_warning(message)

        raise ValueError(f"Unrecognised status: {status}")

    def clear(self) -> None:
        """Clear status."""
        self.status = None
        self.value = ""

    def success(self, message: str) -> None:
        """Set status to success."""
        self.value = self._s_get(message, self._Stat.SUCCESS)

    def failure(self, message: str) -> None:
        """Set status to error."""
        self.value = self._s_get(message, self._Stat.FAILURE)

    def warning(self, message: str) -> None:
        """Set status to warning."""
        self.value = self._s_get(message, self._Stat.WARNING)

    def set(self, message: str, status: _Stat) -> None:
        """Set status."""
        self.value = self._s_get(message, status)

    def append(self, message: str, status: _Stat) -> None:
        """Add a status to existing stati."""
        self.value += self._s_get(message, status)
