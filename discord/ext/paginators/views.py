from __future__ import annotations
from typing import TYPE_CHECKING, Any

import discord


if TYPE_CHECKING:
    from .core import BaseClassPaginator


__all__ = ("PaginatorView", "PaginatorLayoutView", "View")


class PaginatorView[PaginatorT: BaseClassPaginator[Any]](discord.ui.View):
    paginator: PaginatorT

    def __init__(self, paginator: PaginatorT, *args: Any, timeout: int | float | None = None, **kwargs: Any) -> None:
        self.paginator = paginator
        super().__init__(*args, timeout=timeout, **kwargs)

    async def on_timeout(self) -> None:
        await self.paginator.on_timeout()
        return await super().on_timeout()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        await self.paginator.interaction_check(interaction)
        return await super().interaction_check(interaction)

    def stop(self) -> None:
        self.paginator.stop()
        return super().stop()


class PaginatorLayoutView[PaginatorT: BaseClassPaginator[Any]](discord.ui.LayoutView):
    paginator: PaginatorT

    def __init__(self, paginator: PaginatorT, *args: Any, timeout: int | float | None = None, **kwargs: Any) -> None:
        self.paginator = paginator
        super().__init__(*args, timeout=timeout, **kwargs)

    async def on_timeout(self) -> None:
        await self.paginator.on_timeout()
        return await super().on_timeout()

    async def interaction_check(self, interaction: discord.Interaction[Any]) -> bool:
        await self.paginator.interaction_check(interaction)
        return await super().interaction_check(interaction)

    def stop(self) -> None:
        self.paginator.stop()
        return super().stop()


type View[PaginatorT: BaseClassPaginator[Any]] = PaginatorView[PaginatorT] | PaginatorLayoutView[PaginatorT]
