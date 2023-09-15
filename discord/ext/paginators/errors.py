__all__: tuple[str, ...] = ("PaginatorException", "NoPages", "MaxPerPageReached", "CallableSignatureError")


class PaginatorException(Exception):
    pass


class NoPages(PaginatorException):
    pass


class MaxPerPageReached(PaginatorException):
    pass


class CallableSignatureError(PaginatorException):
    pass
