from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .base_paginator import BaseClassPaginator

import discord

if TYPE_CHECKING:
    from typing_extensions import Self

    from discord import Emoji, PartialEmoji
    from discord.abc import Messageable

    from ._types import PossiblePage, ContextT, InteractionT, PossibleMessage


class _PaginatorSelect(discord.ui.Select["SelectOptionsPaginator"]):
    view: SelectOptionsPaginator  # type: ignore

    def __init__(self, paginator: SelectOptionsPaginator) -> None:
        options: Sequence[discord.SelectOption] = paginator.current_options
        super().__init__(
            placeholder=f"Select a page | {paginator.page_string}", options=options, min_values=1, max_values=1 # type: ignore
        )

        self.paginator = paginator

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view._switch_options(self.view.current_page) 
        option = self._get_current_option()
        kwrgs = await self.view.get_kwargs_from_page(option.content)

        kwrgs.pop("wait", None)
        kwrgs["attachments"] = kwrgs.pop("files", [])
        await interaction.response.edit_message(**kwrgs)  # type: ignore

    def _get_current_option(self) -> PaginatorOption:
        selected = self.values[0]
        found = None
        for idx, option in enumerate(self.options):
            if option.value == selected:
                option.default = True
                if not found:
                    self.view.current_option_index = idx
                    found = self.view.current_options[idx]
            else:
                option.default = False
        else:
            if not found:
                raise ValueError("No option found, this should not happen.")

            return found

    def _reset(self):
        for option in self.options:
            option.default = False


class PaginatorOption(discord.SelectOption):
    def __init__(
        self,
        content: PossiblePage,
        *,
        label: str,
        value: str = discord.utils.MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        super().__init__(label=label, value=value, description=description, emoji=emoji, default=default)
        self.content: PossiblePage = content

    @classmethod
    def from_original(
        cls,
        option: discord.SelectOption,
        content: PossiblePage,
    ) -> PaginatorOption:
        if isinstance(option, PaginatorOption):
            return option

        return cls(
            content=content,
            label=option.label,
            value=option.value,
            description=option.description,
            emoji=option.emoji,
            default=option.default,
        )


class SelectOptionsPaginator(BaseClassPaginator[Any, Any]):
    pages: dict[int, list[PaginatorOption]]  # type: ignore

    def __init__(
        self,
        options: list[PaginatorOption],
        *,
        interaction: Optional[InteractionT] = None,
        ctx: Optional[ContextT] = None,
        **kwargs: Any,
    ) -> None:
        self._raw_options: list[PaginatorOption] = options
        super().__init__(
            self.__split_options(options),  # type: ignore
            interaction=interaction,
            ctx=ctx,
            **kwargs,
        )

        self.current_options: list[PaginatorOption] = options
        self.current_option_index: int = 0
        self.select = _PaginatorSelect(self)
        self._switch_options(0)
        self.add_item(self.select)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, row=1)
    async def previous_page(self, interaction: discord.Interaction, _: discord.ui.Button[Self]) -> None:
        if self._current_page <= 0:
            self._current_page = 0
        else:
            self._current_page -= 1

        self._switch_options(self._current_page)
        opt = self.current_options[self.current_option_index]
        opt.default = True
        kwrgs = await self.get_kwargs_from_page(opt.content)
        await self._edit_message(interaction, **kwrgs)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, row=1)
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button[Self]) -> None:
        if self._current_page >= self.max_pages - 1:
            self._current_page = self.max_pages - 1
        else:
            self._current_page += 1

        self._switch_options(self._current_page)
        kwrgs = await self.get_kwargs_from_page(self.current_options[self.current_option_index].content)
        await self._edit_message(interaction, **kwrgs)

    @staticmethod
    def __split_options(options: list[PaginatorOption]) -> dict[int, list[PaginatorOption]]:
        pages: dict[int, list[PaginatorOption]] = {}
        for idx, options in enumerate(discord.utils.as_chunks(options, 25)):
            for opt_idx, option in enumerate(options):
                option.value = f";position={opt_idx}"

            pages[idx] = options

        return pages

    def _switch_options(self, num: int) -> None:
        self.select._reset()
        self.current_options = self.pages[num]
        self.current_option_index = 0
        first_option = self.current_options[0]
        first_option.default = True

        self.select.options = self.current_options  # type: ignore
        self.select.placeholder = f"Select a page | {self.page_string}"

        self.previous_page.disabled = self.current_page <= 0
        self.next_page.disabled = self.current_page >= self.max_pages - 1

    def get_option(self, option_index: int) -> PaginatorOption:
        if option_index < 0 or option_index >= self.max_pages:
            self.current_option_index = 0
            return self.current_options[self._current_page]

        return self.current_options[self.current_option_index]

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
        self._switch_options(self._current_page)
        page = self.get_option(self.current_option_index)
        page.default = True
        return await super()._handle_send(
            page.content,
            ctx=ctx,
            send_to=send_to,
            interaction=interaction,
            override_custom=override_custom,
            force_send=force_send,
            **kwargs,
        )
