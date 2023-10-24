from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generic, Optional, TypedDict, Union

from inspect import signature

import discord
from discord.abc import Messageable

from .errors import *
from .utils import ContextProperty
from ._types import Page, PossibleMessage, InteractionT, ContextT, BotT

if TYPE_CHECKING:
    from typing_extensions import Self, NotRequired
    from typing import Awaitable, Protocol, Union
    from discord import Guild, Member, User, Thread
    from discord.abc import GuildChannel

    class PaginatorCheck(Protocol):
        def __call__(
            self, author_id: int, /, *, interaction: Optional[InteractionT] = None, ctx: Optional[ContextT] = None
        ) -> Union[bool, Awaitable[bool]]:
            ...

    class BaseKwargs(TypedDict):
        content: Optional[str]
        embeds: list[discord.Embed]
        view: Self

        files: NotRequired[list[discord.File]]
        attachments: NotRequired[list[discord.File]]  # used in edit over files
        wait: NotRequired[bool]  # webhook/followup

else:
    BaseKwargs = dict[str, Any]
    from typing import Callable as PaginatorCheck


__all__: tuple[str, ...] = ("BaseClassPaginator", "PaginatorContext",)

maybe_coroutine = discord.utils.maybe_coroutine


class PaginatorContext(Generic[BotT]):
    def __init__(self, obj: BotT) -> None:
        self.obj: BotT = obj

    def __getattr__(self, __name: str) -> Any:
        obj: BotT = object.__getattribute__(self, "obj")
        if not (res := object.__getattribute__(obj, __name)):
            return res

        raise AttributeError(f"{self.__class__.__name__} or {self.__class__.__name__}.obj has no attribute {__name}")

    @property
    def author(self) -> Union[Member, User]:
        if isinstance(self.obj, discord.Interaction):
            return self.obj.user

        return self.obj.author  # type: ignore

    @property
    def author_id(self) -> int:
        return self.author.id

    @property
    def guild(self) -> Optional[Guild]:
        return self.obj.guild  # type: ignore

    @property
    def channel(self) -> Union[GuildChannel, Thread]:
        return self.obj.channel  # type: ignore

    @property
    def bot(self) -> BotT:
        if isinstance(self.obj, discord.Interaction):
            return self.obj.client  # type: ignore

        return self.obj.bot  # type: ignore


class BaseClassPaginator(Generic[Page, BotT], discord.ui.View):
    message: Optional[PossibleMessage]

    def __init__(
        self,
        pages: list[Page],
        *,
        ctx: Optional[ContextT[BotT]] = None,
        interaction: Optional[InteractionT] = None,
        check: Optional[PaginatorCheck] = None,
        author_id: Optional[int] = None,
        delete_after: bool = False,
        disable_after: bool = False,
        clear_buttons_after: bool = False,
        per_page: int = 1,
        message: Optional[PossibleMessage] = None,
        timeout: Union[int, float] = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)

        self.pages: list[Page] = pages
        if not pages:
            raise NoPages("No pages provided.")

        self.per_page: int = per_page
        self.max_pages: int = self._handle_per_page()

        self._current_page: int = 0

        self._ctx: Optional[ContextT[BotT]] = ctx
        self._interaction: Optional[InteractionT] = interaction
        self._context: Optional[PaginatorContext[BotT]] = None
        if self._ctx:
            self._context = PaginatorContext(self._ctx)  # type: ignore
        elif self._interaction:
            self._context = PaginatorContext(self._interaction)  # type: ignore

        self.check = check
        if self.check:
            if not callable(check) or not len(signature(check).parameters) == 3:
                raise CallableSignatureError(
                    "check must be a callable with exactly 3 parameters. Represents the author_id, interaction and ctx."
                )

        self.author_id = author_id
        self.delete_after = delete_after
        self.disable_after = disable_after
        self.clear_buttons_after = clear_buttons_after

        self.message = message
        self._reset_base_kwargs()

    @ContextProperty
    def context(self):
        """The paginator context."""
        if self._context:
            return self._context

        if self._ctx:
            self._context = PaginatorContext(self._ctx)  # type: ignore
        elif self._interaction:
            self._context = PaginatorContext(self._interaction)  # type: ignore

        return self._context

    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        self._current_page = value

    @property
    def page_string(self) -> str:
        return f"Page {self.current_page + 1} of {self.max_pages}"

    def _reset_base_kwargs(self) -> None:
        self._base_kwargs: BaseKwargs = {"content": None, "embeds": [], "view": self}

    def _handle_per_page(self) -> int:
        total_pages, left_over = divmod(len(self.pages), self.per_page)
        if left_over:
            total_pages += 1

        return total_pages

    def stop(self) -> None:
        self._reset_base_kwargs()
        super().stop()

    async def get_kwargs_from_page(
        self,
        page: Union[Page, list[Page]],
        send_kwargs: dict[str, Any] = {},
        skip_formatting: bool = False,
    ) -> BaseKwargs:
        if not skip_formatting:
            self._reset_base_kwargs()
            page = await maybe_coroutine(self.format_page, page)

        if send_kwargs:
            for key, value in send_kwargs.items():
                if key in ("embed", "file"):
                    self._base_kwargs[f"{key}s"] = value  # type: ignore # literal keys.
                elif key == "view":
                    continue
                else:
                    self._base_kwargs.update(send_kwargs)  # type: ignore

        # if self.per_page > 1 and isinstance(page, (list, tuple)):
        #   raise ValueError("format_page must be used to format multiple pages.")
        if isinstance(page, (list, tuple)):
            for _page in page:
                page = await self.get_kwargs_from_page(_page, skip_formatting=True)  # type: ignore

        if isinstance(page, (int, str)):
            self._base_kwargs["content"] = f"{page}\n\n{self.page_string}"
        elif isinstance(page, dict):
            self._base_kwargs.update(page)  # type: ignore
        elif isinstance(page, discord.Embed):
            if not page.footer.text:
                page.set_footer(text=self.page_string)
            else:
                if not "|" in page.footer.text:
                    page.set_footer(text=f"{page.footer.text} | {self.page_string}")

            self._base_kwargs["embeds"].append(page)

        elif isinstance(page, discord.File):
            page.reset()
            if not "files" in self._base_kwargs:
                self._base_kwargs["files"] = [page]
            else:
                self._base_kwargs["files"].append(page)

            if not self._base_kwargs["content"]:
                self._base_kwargs["content"] = self.page_string
            else:
                if not self.page_string in self._base_kwargs["content"]:
                    self._base_kwargs["content"] += f"\n\n{self.page_string}"

        return self._base_kwargs

    def get_page(self, page_number: int) -> Union[Page, list[Page]]:
        if page_number < 0 or page_number >= self.max_pages:
            self._current_page = 0
            return self.pages[self._current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    async def interaction_check(self, interaction: InteractionT) -> bool:
        if self.check:
            return await maybe_coroutine(self.check, interaction.user.id, interaction=interaction, ctx=self._ctx)

        if self._interaction is None and self._ctx is None:
            return True

        client = interaction.client
        TO_CHECK: set[Union[int, Any]] = {interaction.user.id}.union(set(getattr(client, "owner_ids", set())))  # pyright: ignore [reportUnknownArgumentType]
        if getattr(client, "owner_id", None):
            TO_CHECK.union({client.owner_id})  # type: ignore

        return interaction.user.id in TO_CHECK

    def format_page(self, page: Union[list[Page], Page]) -> Any:
        return page

    async def stop_paginator(self) -> None:
        if not self.message:
            self.stop()
            return

        if self.delete_after:
            try:
                await self.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            return

        if self.clear_buttons_after:
            await self._edit_message(view=None)
        elif self.disable_after:
            for button in self.children:
                button.disabled = True  # type: ignore

            await self._edit_message(view=self)
            return

        self.stop()

    async def on_timeout(self) -> None:
        await self.stop_paginator()

    async def _edit_message(self, interaction: Optional[InteractionT] = None, /, **kwargs: Any) -> None:
        if interaction is not None:
            self._interaction = interaction

        to_call: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
        if self._interaction:
            to_call = self._interaction.response.edit_message
            if self._interaction.response.is_done():
                if not self._interaction.message:
                    to_call = self._interaction.edit_original_response
                else:
                    to_call = self._interaction.message.edit

        elif self.message:
            to_call = self.message.edit
        else:
            ValueError("No interaction or message to edit.")

        _kwargs = kwargs.copy()
        _kwargs.pop("ephemeral", None)
        if to_call is not None:
            await to_call(**_kwargs)

        if self.is_finished():
            self.message = None

    async def send(
        self,
        *,
        ctx: Optional[ContextT] = None,
        send_to: Optional[Messageable] = None,
        interaction: Optional[InteractionT] = None,
        override_custom: bool = False,
        force_send: bool = False,
        **kwargs,
    ) -> PossibleMessage:
        raise NotImplementedError("send must be implemented in a subclass.")

    async def _handle_send(  
        self,
        page: Any,
        *,
        ctx: Optional[ContextT] = None,
        send_to: Optional[Messageable] = None,
        interaction: Optional[InteractionT] = None,
        override_custom: bool = False,
        force_send: bool = False,
        **kwargs: Any,
    ) -> Optional[PossibleMessage]:
        if ctx and interaction:
            raise ValueError("ctx and interaction cannot be both set.")

        self._interaction = interaction or self._interaction
        self._ctx = ctx or self._ctx  # type: ignore
        send_kwargs = await self.get_kwargs_from_page(page, send_kwargs=kwargs if override_custom else {})

        if self.message is not None and not force_send:
            await self._edit_message(self._interaction, **send_kwargs)
            return

        if send_to is not None:
            self.message = await send_to.send(**send_kwargs)  # type: ignore
            return self.message  # type: ignore

        elif self._interaction is not None:
            if self._interaction.response.is_done():
                send_kwargs["wait"] = True
                self.message = await self._interaction.followup.send(**send_kwargs)  # type: ignore
            else:
                await self._interaction.response.send_message(**send_kwargs)  # type: ignore
                self.message = await interaction.original_response()  # type: ignore

        elif self._ctx is not None:
            self.message = await self._ctx.send(**send_kwargs)  # type: ignore

        else:
            raise ValueError("ctx or interaction or send_to must be provided")

        return self.message  # type: ignore
