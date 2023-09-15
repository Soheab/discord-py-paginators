from __future__ import annotations
from typing import TYPE_CHECKING, Any, Type, Union, overload

if TYPE_CHECKING:
    from ._types import Page, BotT, InteractionT, ContextT
    from .base_paginator import BaseClassPaginator, PaginatorContext


class ContextProperty:
    def __init__(self, function) -> None:
        self.function = function

    @overload
    def __get__(
        self, instance: BaseClassPaginator[Page, ContextT[BotT]], owner: Type[ BaseClassPaginator[Page, ContextT[BoT]]]
    ) -> PaginatorContext[ContextT[BotT]]:
        ...

    @overload
    def __get__(
        self, instance:  BaseClassPaginator[Page, InteractionT[BotT]], owner: Type[ BaseClassPaginator[Page, InteractionT[BotT]]]
    ) -> PaginatorContext[InteractionT[BotT]]:
        ...

    @overload
    def __get__(self, instance: BaseClassPaginator[Page], owner: Type[BaseClassPaginator[Page]]) -> None:
        ...

    def __get__(
        self,
        instance: Union[
             BaseClassPaginator[Page, ContextT[BotT]],  BaseClassPaginator[Page, InteractionT[BotT]], BaseClassPaginator[Page]
        ],
        owner: Type[
            Union[
                 BaseClassPaginator[Page, ContextT[BotT]],  BaseClassPaginator[Page, InteractionT[BotT]], BaseClassPaginator[Page]
            ]
        ],
    ) -> Union[PaginatorContext[BotT], PaginatorContext[BotT], None]:
        if not instance:
            return self  # type: ignore

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value
