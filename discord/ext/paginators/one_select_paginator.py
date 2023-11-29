from __future__ import annotations
from typing import TYPE_CHECKING, Any, Sequence, Optional

from discord.ui import Select
from discord.components import SelectOption

from ._types import InteractionT, ContextT
from ._types import Page, BotT

from .base_paginator import BaseClassPaginator

if TYPE_CHECKING:
    from typing import Union

    from discord.abc import Messageable

    from ._types import PossibleMessage


__all__: tuple[str, ...] = ("SelectPaginator", "SelectPaginatorOption")


class SelectPaginatorSelector(Select["SelectPaginator[Any, Any]"]):
    view: SelectPaginator[Any, Any]  # pyright: ignore [reportIncompatibleMethodOverride]

    async def callback(self, interaction: InteractionT) -> None:
        page_index = int(self.values[0].split("position=")[1])
        page: SelectPaginatorOption = self.view.get_page(page_index)
        edit_kwargs = await self.view.get_kwargs_from_page(page.content)
        self._set_defaults(self.values[0])

        edit_kwargs["attachments"] = edit_kwargs.pop("files", [])
        await self.view._edit_message(interaction, **edit_kwargs)

    def _set_defaults(self, selected_value: str) -> None:
        for option in self.options:
            if option.value == selected_value:
                option.default = True
            else:
                option.default = False


class SelectPaginatorOption(SelectOption):
    def __init__(
        self,
        content: Any,
        *,
        label: Optional[str] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self.custom_id: Optional[str] = None  # filled in _update
        super().__init__(label=label or "____SelectPaginatorPlaceholder____", **kwargs)
        self.content: Any = content
        self.position: Optional[int] = position

    def _update(self, paginator: SelectPaginator[Any, Any]) -> None:
        CLASS_NAME = "SelectPaginator"

        if self.position is None:
            self.position = list(paginator.pages).index(self)
        else:
            self.position = int(self.position) - 1

        if self.label == f"____{CLASS_NAME}Placeholder____":
            self.label = f"Page {self.position + 1}"
        if self.description is None:
            self.description = f"{self.position + 1} of {len(list(paginator.pages))}"

        self.value = f"{CLASS_NAME};position={self.position}"


class SelectPaginator(BaseClassPaginator[Page, BotT]):
    if TYPE_CHECKING:

        def get_page(self, page: int) -> SelectPaginatorOption:  # type: ignore
            ...

    def __init__(
        self,
        pages: list[Union[Page, SelectPaginatorOption]],
        *,
        custom_id: Optional[str] = None,
        placeholder: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(pages, **kwargs)  # type: ignore
        if len(pages) > 25:
            raise ValueError("SelectPaginator cannot have more than 25 pages.")

        self.custom_id = custom_id if custom_id is not None else "select_paginator"
        self.placeholder = placeholder if placeholder is not None else "Select a page | 0/0"

        self.select: SelectPaginatorSelector = SelectPaginatorSelector(
            custom_id=self.custom_id,
            placeholder=self.placeholder,
            min_values=1,
            max_values=1,
        )

        self.pages: Sequence[SelectPaginatorOption] = pages  # type: ignore
        self.__handle_pages()
        self._reset_base_kwargs()

    def __handle_pages(self) -> None:
        new_pages: Sequence[SelectPaginatorOption] = []
        page: Union[Page, SelectPaginatorOption]
        for page in self.pages:
            if isinstance(page, SelectPaginatorOption):  # pyright: ignore [reportUnnecessaryIsInstance] 
                new_pages.append(page)
            else:
                pg = SelectPaginatorOption(page)
                new_pages.append(pg)

        self.pages = sorted(new_pages, key=lambda x: x.position if x.position is not None else new_pages.index(x))  # pyright: ignore [reportIncompatibleVariableOverride] # dw
        for new_page in new_pages:
            new_page._update(self)
            self.select.append_option(new_page)


    async def send(  # type: ignore
        self,
        *,
        ctx: Optional[ContextT] = None,
        send_to: Optional[Messageable] = None,
        interaction: Optional[InteractionT] = None,
        override_custom: bool = False,
        force_send: bool = False,
        **kwargs: Any,
    ) -> Optional[PossibleMessage]:
        page = self.get_page(self.current_page)
        content = page.content
        return await super()._handle_send(
            content,
            ctx=ctx,
            send_to=send_to,
            interaction=interaction,
            force_send=force_send,
            override_custom=override_custom,
            **kwargs,
        )
