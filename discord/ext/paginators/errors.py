__all__: tuple[str, ...] = (
    "PaginatorException",
    "NoPages",
    "MaxPerPageReached",
    "CallableSignatureError",
)


class PaginatorException(Exception):
    """Base exception for all errors raised by this package."""

    pass


class NoPages(PaginatorException):
    """Raised when no pages are provided to the paginator."""

    pass


class MaxPerPageReached(PaginatorException):
    """Raised when the maximum number of pages per page is reached."""

    pass


class CallableSignatureError(PaginatorException):
    """Raised when the provided callable has an invalid signature."""

    pass
