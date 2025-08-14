from __future__ import annotations
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, TypeVar

import time

if TYPE_CHECKING:
    from ._types import Sequence


if TYPE_CHECKING:
    from typing_extensions import TypeVar

    DefaultT = TypeVar("DefaultT", default=None)
else:
    DefaultT = TypeVar("DefaultT")


class MaybeTTLPages[PageT: Any]:
    def __init__(self, pages: Sequence[PageT], max_age: float | None = None):
        self.__max_age: float | None = max_age

        self.__pages: dict[int, tuple[float, PageT | Sequence[PageT]]] = {}
        self.replace_pages(pages)

    def __remove_expired_keys(self) -> None:
        if self.__max_age is None:
            return

        now = time.time()
        for key, (stamp, _) in self.__pages.copy().items():
            if (now - stamp) > self.__max_age:
                del self.__pages[key]

    def add(self, index: int, value: PageT | Sequence[PageT]) -> None:
        self.__remove_expired_keys()
        self[index] = value

    def replace_pages(self, pages: Sequence[PageT]) -> None:
        self.__remove_expired_keys()
        self.__pages = {i: (time.time(), page) for i, page in enumerate(pages)}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__pages!r}, max_age={self.__max_age!r})"

    def __getitem__(self, index: int) -> PageT | Sequence[PageT]:
        self.__remove_expired_keys()
        return self.__pages[index][1]

    def __setitem__(self, index: int, value: PageT | Sequence[PageT]) -> None:
        self.__remove_expired_keys()
        self.__pages[index] = (time.time(), value)

    def __delitem__(self, index: int) -> None:
        self.__remove_expired_keys()
        try:
            del self.__pages[index]
        except KeyError:
            raise KeyError(index)

    def __len__(self) -> int:
        self.__remove_expired_keys()
        return len(self.__pages)

    def __iter__(self) -> Iterator[PageT | Sequence[PageT]]:
        self.__remove_expired_keys()
        return iter(value[1] for value in self.__pages.values())
