from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

import discord
from discord.ui import Select, Button
from discord.components import SelectOption
from discord.utils import as_chunks

from ._types import InteractionT, ContextT, Page, BotT
from .base_paginator import BaseClassPaginator

if TYPE_CHECKING:
    from typing import Union

    from discord.abc import Messageable


__all__: tuple[str, ...] = ("SelectPaginator", "SelectPaginatorOption")


class SelectPaginatorMoveButton(Button["SelectPaginator[Any, Any]"]):
    view: SelectPaginator[Any, Any]  # pyright: ignore [reportIncompatibleMethodOverride]

    def __init__(self, label: str, emoji: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(label=label, emoji=emoji, row=1, **kwargs)

    def __repr__(self) -> str:
        return f"<SelectPaginatorMoveButton custom_id={self.custom_id}>"

    async def callback(self, interaction: InteractionT) -> None:
        if self.custom_id == "select_paginator_first":
            self.view.current_page = 0
        elif self.custom_id == "select_paginator_last":
            self.view.current_page = len(self.view.pages) - 1
        elif self.custom_id == "select_paginator_next":
            self.view.current_page += 1
        elif self.custom_id == "select_paginator_back":
            self.view.current_page -= 1

        await self.view._switch_pages(interaction)  # pyright: ignore [reportPrivateUsage]


class SelectPaginatorSelector(Select["SelectPaginator[Any, Any]"]):
    view: SelectPaginator[Any, Any]  # pyright: ignore [reportIncompatibleMethodOverride]

    async def callback(self, interaction: InteractionT) -> None:
        current_options = self.view.pages[self.view.current_page]
        selected_value = self.values[0]
        option = discord.utils.get(current_options, value=selected_value)
        page: SelectPaginatorOption = self.view.get_page(current_options.index(option))  # type: ignore
        edit_kwargs = await self.view.get_kwargs_from_page(page.content)
        self._update_options(self.view)
        self._set_defaults()

        edit_kwargs["attachments"] = edit_kwargs.pop("files", [])  # pyright: ignore [reportUnknownArgumentType]
        await self.view._edit_message(interaction, **edit_kwargs)  # pyright: ignore [reportPrivateUsage]

    def _set_defaults(
        self,
    ) -> None:
        selected_value = self.values[0]
        for option in self.options:
            if option.value is selected_value or option.label in selected_value:
                option.default = True
            else:
                option.default = False

    def _update_options(
        self,
        paginator: SelectPaginator[Any, Any],
    ) -> None:
        try:
            self.placeholder = f"{paginator.placeholder} | {paginator.page_string}"
        except AttributeError:
            pass

        option: SelectPaginatorOption
        options = paginator.pages[paginator.current_page]
        for option in options:
            option._update(paginator, self)  # pyright: ignore [reportPrivateUsage]

        self.options = options  # type: ignore


class SelectPaginatorOption(SelectOption):
    def __init__(
        self,
        content: Any,
        *,
        label: Optional[str] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ):
        self.custom_id: Optional[str] = None  # filled in _update
        super().__init__(label=label or "____SelectPaginatorPlaceholder____", **kwargs)
        self.content: Any = content
        self.position: Optional[int] = position

    def __repr__(self) -> str:
        return f"<SelectPaginatorOption value={self.value}>"

    def _update(self, paginator: SelectPaginator[Any, Any], select: SelectPaginatorSelector) -> None:
        CLASS_NAME = "SelectPaginator"

        if self.position is None:
            self.position = list(paginator.pages[paginator.current_page]).index(self)
        else:
            self.position = int(self.position) - 1

        if self.label == f"____{CLASS_NAME}Placeholder____":
            self.label = f"Page {self.position + 1}"

        if self.description is None:
            self.description = f"{paginator.current_page + 1} of {paginator.max_pages}"

        self.value = f"{CLASS_NAME};position={self.position}"


class SelectPaginator(BaseClassPaginator[Page, BotT]):
    PREVIOUS_BUTTON: SelectPaginatorMoveButton = SelectPaginatorMoveButton(
        label="Previous",
        emoji="⬅️",
        custom_id="select_paginator_back",
    )
    NEXT_BUTTON: SelectPaginatorMoveButton = SelectPaginatorMoveButton(
        label="Next",
        emoji="➡️",
        custom_id="select_paginator_next",
    )

    pages: list[list[SelectPaginatorOption]]

    def __init__(
        self,
        pages: list[Union[Page, SelectPaginatorOption]],
        *,
        placeholder: Optional[str] = None,
        **kwargs: Any,
    ):
        self.base_custom_id = "select_paginator"
        self.placeholder = placeholder if placeholder is not None else "Select a page"

        self.select: SelectPaginatorSelector = SelectPaginatorSelector(
            custom_id=f"{self.base_custom_id}:0",
            placeholder=self.placeholder,
            min_values=1,
            max_values=1,
        )

        super().__init__(self.__handle_pages(pages), **kwargs)  # type: ignore
        self.add_item(self.select)
        self.add_item(self.PREVIOUS_BUTTON)
        self.add_item(self.NEXT_BUTTON)

    def _handle_buttons(self) -> None:
        self.PREVIOUS_BUTTON.disabled = self.current_page <= 0
        self.NEXT_BUTTON.disabled = len(self.pages) - 1 <= self.current_page

    def _handle_per_page(self) -> int:
        total_pages, left_over = divmod(len(self.pages), self.per_page)
        if left_over:
            total_pages += 1

        return total_pages

    def __handle_pages(self, _pages: list[Union[Page, SelectPaginatorOption]]) -> list[list[SelectPaginatorOption]]:
        chunked = list(as_chunks(_pages, 25))
        final_pages: list[list[SelectPaginatorOption]] = []

        pages: list[Union[Page, SelectPaginatorOption]]
        page: Union[Page, SelectPaginatorOption]
        for pages in chunked:
            parsed_page: list[SelectPaginatorOption] = []
            for page in pages:
                if not isinstance(page, SelectPaginatorOption):
                    page = SelectPaginatorOption(page)

                parsed_page.append(page)

            final_pages.append(parsed_page)

        self.pages = final_pages  # pyright: ignore [reportIncompatibleVariableOverride] # can't really fix this, its fine
        self.select.placeholder = f"{self.placeholder} | 1/{len(final_pages)}"
        self._current_page = 0
        self.per_page = 1
        self.max_pages = self._handle_per_page()
        self.select._update_options(self)  # pyright: ignore [reportPrivateUsage]
        self._handle_buttons()
        del self.pages, self._current_page, chunked
        return final_pages

    def get_page(self, page_number: int) -> Union[SelectPaginatorOption, list[SelectPaginatorOption]]:  # pyright: ignore [reportIncompatibleMethodOverride]
        pages = self.pages[self._current_page]
        if page_number < 0 or page_number >= len(pages):
            page_number = 0
            return pages[page_number]

        if self._current_page < 0 or self._current_page >= len(self.pages):
            self._current_page = 0
            return pages[page_number]

        if self.per_page == 1:
            return pages[page_number]
        else:
            base = page_number * self.per_page
            return pages[base : base + self.per_page]

    async def _switch_pages(self, interaction: InteractionT) -> None:
        pages = self.pages[self.current_page]
        self.select.options = pages  # type: ignore
        self.select._update_options(self)  # pyright: ignore [reportPrivateUsage]
        page: SelectPaginatorOption = self.get_page(0)  # type: ignore
        kwrgs = await self.get_kwargs_from_page(page.content)
        self._handle_buttons()

        await self._edit_message(interaction, **kwrgs)

    async def send(
        self,
        *,
        ctx: Optional[ContextT] = None,
        send_to: Optional[Messageable] = None,
        interaction: Optional[InteractionT] = None,
        override_custom: bool = False,
        force_send: bool = False,
        **kwargs: Any,
    ):
        page = self.get_page(self.current_page)
        content = page.content  # type: ignore
        return await super()._handle_send(
            content,
            ctx=ctx,
            send_to=send_to,
            interaction=interaction,
            force_send=force_send,
            override_custom=override_custom,
            **kwargs,
        )
