from typing import Any, Optional, Tuple

import yaml

from .ls_protocols import _RangeTypedDict


class ScalarInfo:
    def __init__(self, scalar: Any, location: Optional[Tuple[int, int, int, int]]):
        """
        Args:
            scalar:
            location: tuple(start_line, start_col, end_line, end_col)
        """
        self.scalar = scalar
        self.location = location

    def __repr__(self):
        return repr(self.scalar)

    def __str__(self):
        return str(self.scalar)

    def __eq__(self, o):
        if isinstance(o, ScalarInfo):
            return self.scalar == o.scalar

        return False

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return hash(self.scalar)

    def as_range(self) -> _RangeTypedDict:
        assert self.location
        start_line, start_col, end_line, end_col = self.location
        return create_range_from_location(start_line, start_col, end_line, end_col)

    def replace(self, *args, **kwargs):
        # Needed because when dealing with floats/ints/bools yaml does a call
        # to `construct_scalar` and then proceeds to do a replace and actually
        # manage the value (we could override more functions to deal with those
        # but we're mostly interested in the keys location, so, this is just
        # ignored for now such that we don't get locations for things that aren't
        # strings).
        return self.scalar.replace(*args, **kwargs)

    def encode(self, *args, **kwargs):
        return self.scalar.encode(*args, **kwargs)


def create_range_from_location(
    start_line: int,
    start_col: int,
    end_line: Optional[int] = None,
    end_col: Optional[int] = None,
) -> _RangeTypedDict:
    """
    If the end_line and end_col aren't passed we consider
    that the location should go up until the end of the line.
    """
    if end_line is None:
        assert end_col is None
        end_line = start_line + 1
        end_col = 0
    assert end_col is not None
    dct: _RangeTypedDict = {
        "start": {
            "line": start_line,
            "character": start_col,
        },
        "end": {
            "line": end_line,
            "character": end_col,
        },
    }
    return dct


class LoaderWithLines(yaml.SafeLoader):
    def construct_scalar(self, node, *args, **kwargs):
        scalar = yaml.SafeLoader.construct_scalar(self, node, *args, **kwargs)
        return ScalarInfo(
            scalar=scalar,
            location=(
                node.start_mark.line,
                node.start_mark.column,
                node.end_mark.line,
                node.end_mark.column,
            ),
        )


class _Position:
    def __init__(self, line: int = 0, character: int = 0):
        self.line: int = line
        self.character: int = character

    def to_dict(self):
        return {"line": self.line, "character": self.character}

    def __repr__(self):
        import json

        return json.dumps(self.to_dict(), indent=4)

    def __getitem__(self, name):
        # provide tuple-access, not just dict access.
        if name == 0:
            return self.line
        if name == 1:
            return self.character
        return getattr(self, name)

    def __eq__(self, other):
        return (
            isinstance(other, _Position)
            and self.line == other.line
            and self.character == other.character
        )

    def __ge__(self, other):
        line_gt = self.line > other.line

        if line_gt:
            return line_gt

        if self.line == other.line:
            return self.character >= other.character

        return False

    def __gt__(self, other):
        line_gt = self.line > other.line

        if line_gt:
            return line_gt

        if self.line == other.line:
            return self.character > other.character

        return False

    def __le__(self, other):
        line_lt = self.line < other.line

        if line_lt:
            return line_lt

        if self.line == other.line:
            return self.character <= other.character

        return False

    def __lt__(self, other):
        line_lt = self.line < other.line

        if line_lt:
            return line_lt

        if self.line == other.line:
            return self.character < other.character

        return False

    def __ne__(self, other):
        return not self.__eq__(other)


def is_inside(range_dct: _RangeTypedDict, line: int, col: int) -> bool:
    start = range_dct["start"]
    end = range_dct["end"]
    start_pos = _Position(start["line"], start["character"])
    end_pos = _Position(end["line"], end["character"])
    curr_pos = _Position(line, col)
    return start_pos <= curr_pos <= end_pos
