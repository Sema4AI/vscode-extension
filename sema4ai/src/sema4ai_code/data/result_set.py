import typing
from typing import Any, Iterator

T = typing.TypeVar("T")


class ResultSet:
    def __init__(self, columns: list[str], rows: list[tuple[Any, ...]]):
        self._columns = columns
        self._data = rows

    def iter_as_dicts(self) -> Iterator[dict[str, Any]]:
        """
        Iterates over the result set as a list of dictionaries.
        """
        for row in self._data:
            yield dict(zip(self._columns, row))

    def iter_as_tuples(self) -> Iterator[tuple[Any, ...]]:
        """
        Iterates over the result set values as a list of tuples.
        """
        yield from self._data

    def build_list(self, item_class: type[T]) -> list[T]:
        """
        Builds a list of objects of the given class from the result set.

        Args:
            item_class: The class to build the list of.

        Returns:
            A list of objects of the given class.

        Note: The class must have a constructor that accepts each item in the
        result set as keyword arguments.
        """
        return [item_class(**row) for row in self.iter_as_dicts()]
